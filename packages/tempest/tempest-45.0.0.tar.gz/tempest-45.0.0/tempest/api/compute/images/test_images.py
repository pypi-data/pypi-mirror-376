# Copyright 2012 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import testtools

from tempest.api.compute import base
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exceptions

CONF = config.CONF


class ImagesTestJSON(base.BaseV2ComputeTest):
    """Test server images"""

    create_default_network = True

    @classmethod
    def skip_checks(cls):
        super(ImagesTestJSON, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        if not CONF.compute_feature_enabled.snapshot:
            skip_msg = ("%s skipped as instance snapshotting is not supported"
                        % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(ImagesTestJSON, cls).setup_clients()
        if cls.is_requested_microversion_compatible('2.35'):
            cls.client = cls.compute_images_client
        else:
            cls.client = cls.images_client

    @decorators.idempotent_id('aa06b52b-2db5-4807-b218-9441f75d74e3')
    def test_delete_saving_image(self):
        """Test deleting server image while it is in 'SAVING' state"""
        server = self.create_test_server(wait_until='ACTIVE')
        self.addCleanup(self.servers_client.delete_server, server['id'])
        # wait for server active to avoid conflict when deleting server
        # in task_state image_snapshot
        self.addCleanup(waiters.wait_for_server_status, self.servers_client,
                        server['id'], 'ACTIVE')
        snapshot_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='test-snap')
        try:
            image = self.create_image_from_server(server['id'],
                                                  name=snapshot_name,
                                                  wait_until='SAVING')
            self.client.delete_image(image['id'])
            msg = ('The image with ID {image_id} failed to be deleted'
                   .format(image_id=image['id']))
            self.assertTrue(self.client.is_resource_deleted(image['id']),
                            msg)
            self.assertEqual(snapshot_name, image['name'])
        except lib_exceptions.TimeoutException as ex:
            # If timeout is reached, we don't need to check state,
            # since, it wouldn't be a 'SAVING' state at least and apart from
            # it, this testcase doesn't have scope for other state transition
            # Hence, skip the test.
            raise self.skipException("This test is skipped because " + str(ex))

    @decorators.idempotent_id('aaacd1d0-55a2-4ce8-818a-b5439df8adc9')
    def test_create_image_from_stopped_server(self):
        """Test creating server image from stopped server"""
        server = self.create_test_server(wait_until='ACTIVE')
        self.servers_client.stop_server(server['id'])
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'SHUTOFF')
        self.addCleanup(self.servers_client.delete_server, server['id'])
        snapshot_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='test-snap')
        image = self.create_image_from_server(server['id'],
                                              name=snapshot_name,
                                              wait_until='ACTIVE',
                                              wait_for_server=False)
        # This is required due to ceph issue:
        # https://bugs.launchpad.net/glance/+bug/2045769.
        # New location APIs are async so we need to wait for the location
        # import task to complete.
        # This should work with old location API since we don't fail if there
        # are no tasks for the image
        waiters.wait_for_image_tasks_status(self.images_client,
                                            image['id'], 'success')
        self.addCleanup(self.client.delete_image, image['id'])
        self.assertEqual(snapshot_name, image['name'])

    @decorators.idempotent_id('71bcb732-0261-11e7-9086-fa163e4fa634')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    def test_create_image_from_paused_server(self):
        """Test creating server image from paused server"""
        server = self.create_test_server(wait_until='ACTIVE')
        self.servers_client.pause_server(server['id'])
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'PAUSED')
        self.addCleanup(self.servers_client.delete_server, server['id'])

        snapshot_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='test-snap')
        image = self.create_image_from_server(server['id'],
                                              name=snapshot_name,
                                              wait_until='ACTIVE',
                                              wait_for_server=False)
        # This is required due to ceph issue:
        # https://bugs.launchpad.net/glance/+bug/2045769.
        # New location APIs are async so we need to wait for the location
        # import task to complete.
        # This should work with old location API since we don't fail if there
        # are no tasks for the image
        waiters.wait_for_image_tasks_status(self.images_client,
                                            image['id'], 'success')
        self.addCleanup(self.client.delete_image, image['id'])
        self.assertEqual(snapshot_name, image['name'])

    @decorators.idempotent_id('8ca07fec-0262-11e7-907e-fa163e4fa634')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    def test_create_image_from_suspended_server(self):
        """Test creating server image from suspended server"""
        server = self.create_test_server(wait_until='ACTIVE')
        self.servers_client.suspend_server(server['id'])
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'SUSPENDED')
        self.addCleanup(self.servers_client.delete_server, server['id'])

        snapshot_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='test-snap')
        image = self.create_image_from_server(server['id'],
                                              name=snapshot_name,
                                              wait_until='ACTIVE',
                                              wait_for_server=False)
        # This is required due to ceph issue:
        # https://bugs.launchpad.net/glance/+bug/2045769.
        # New location APIs are async so we need to wait for the location
        # import task to complete.
        # This should work with old location API since we don't fail if there
        # are no tasks for the image
        waiters.wait_for_image_tasks_status(self.images_client,
                                            image['id'], 'success')
        self.addCleanup(self.client.delete_image, image['id'])
        self.assertEqual(snapshot_name, image['name'])

    @decorators.idempotent_id('f3cac456-e3fe-4183-a7a7-a59f7f017088')
    def test_create_server_from_snapshot(self):
        # Create one server normally
        server = self.create_test_server(wait_until='ACTIVE')
        self.addCleanup(self.servers_client.delete_server, server['id'])

        # Snapshot it
        snapshot_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='test-snap')
        image = self.create_image_from_server(server['id'],
                                              name=snapshot_name,
                                              wait_until='ACTIVE',
                                              wait_for_server=False)
        self.addCleanup(self.client.delete_image, image['id'])

        # Try to create another server from that snapshot
        server2 = self.create_test_server(wait_until='ACTIVE',
                                          image_id=image['id'])

        # Delete server 2 before we finish otherwise we'll race with
        # the cleanup which tries to delete the image before the
        # server is gone.
        self.servers_client.delete_server(server2['id'])
        waiters.wait_for_server_termination(self.servers_client, server2['id'])
