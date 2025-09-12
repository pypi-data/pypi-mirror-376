# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
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
from tempest.common import compute
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class ServerRescueTestBase(base.BaseV2ComputeTest):
    create_default_network = True

    @classmethod
    def skip_checks(cls):
        super(ServerRescueTestBase, cls).skip_checks()
        if not CONF.compute_feature_enabled.rescue:
            msg = "Server rescue not available."
            raise cls.skipException(msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources(network=True, subnet=True, router=True)
        super(ServerRescueTestBase, cls).setup_credentials()

    @classmethod
    def resource_setup(cls):
        super(ServerRescueTestBase, cls).resource_setup()

        password = data_utils.rand_password()
        server = cls.create_test_server(adminPass=password,
                                        wait_until='ACTIVE')
        cls.servers_client.rescue_server(server['id'], adminPass=password)
        waiters.wait_for_server_status(cls.servers_client, server['id'],
                                       'RESCUE')
        cls.rescued_server_id = server['id']


class ServerRescueTestJSON(ServerRescueTestBase):
    """Test server rescue"""

    @decorators.idempotent_id('fd032140-714c-42e4-a8fd-adcd8df06be6')
    def test_rescue_unrescue_instance(self):
        """Test rescue/unrescue server"""
        password = data_utils.rand_password()
        server = self.create_test_server(adminPass=password,
                                         wait_until='ACTIVE')
        self.servers_client.rescue_server(server['id'], adminPass=password)
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'RESCUE')
        self.servers_client.unrescue_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')


class ServerRescueTestJSONUnderV235(ServerRescueTestBase):
    """Test server rescue with compute microversion less than 2.36"""

    max_microversion = '2.35'

    # TODO(zhufl): After 2.35 we should switch to neutron client to create
    # floating ip, but that will need admin credential, so the testcases will
    # have to be added in somewhere in admin directory.

    @decorators.idempotent_id('4842e0cf-e87d-4d9d-b61f-f4791da3cacc')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    @testtools.skipUnless(CONF.network_feature_enabled.floating_ips,
                          "Floating ips are not available")
    def test_rescued_vm_associate_dissociate_floating_ip(self):
        """Test associate/dissociate floating ip for rescued server"""
        floating_ip_body = self.floating_ips_client.create_floating_ip(
            pool=CONF.network.floating_network_name)['floating_ip']
        self.addCleanup(self.floating_ips_client.delete_floating_ip,
                        floating_ip_body['id'])

        self.floating_ips_client.associate_floating_ip_to_server(
            str(floating_ip_body['ip']).strip(), self.rescued_server_id)

        # Disassociation of floating IP that was associated in this method
        self.floating_ips_client.disassociate_floating_ip_from_server(
            str(floating_ip_body['ip']).strip(), self.rescued_server_id)

    @decorators.idempotent_id('affca41f-7195-492d-8065-e09eee245404')
    def test_rescued_vm_add_remove_security_group(self):
        """Test add/remove security group to for rescued server"""
        # Add Security group
        sg = self.create_security_group()
        self.servers_client.add_security_group(self.rescued_server_id,
                                               name=sg['name'])

        # Delete Security group
        self.servers_client.remove_security_group(self.rescued_server_id,
                                                  name=sg['name'])


class BaseServerStableDeviceRescueTest(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(BaseServerStableDeviceRescueTest, cls).skip_checks()
        if not CONF.compute_feature_enabled.rescue:
            msg = "Server rescue not available."
            raise cls.skipException(msg)
        if not CONF.compute_feature_enabled.stable_rescue:
            msg = "Stable rescue not available."
            raise cls.skipException(msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources(network=True, subnet=True, router=True,
                                  dhcp=True)
        super(BaseServerStableDeviceRescueTest, cls).setup_credentials()

    def _create_server_and_rescue_image(self, hw_rescue_device=None,
                                        hw_rescue_bus=None,
                                        block_device_mapping_v2=None,
                                        validatable=False,
                                        validation_resources=None,
                                        wait_until='ACTIVE'):
        server = self.create_test_server(
            wait_until=wait_until,
            validatable=validatable,
            validation_resources=validation_resources)
        image_id = self.create_image_from_server(
            server['id'], wait_until='ACTIVE')['id']

        if block_device_mapping_v2:
            server = self.create_test_server(
                wait_until=wait_until,
                validatable=validatable,
                validation_resources=validation_resources,
                block_device_mapping_v2=block_device_mapping_v2)

        if hw_rescue_bus:
            self.images_client.update_image(
                image_id, [dict(add='/hw_rescue_bus',
                                value=hw_rescue_bus)])
        if hw_rescue_device:
            self.images_client.update_image(
                image_id, [dict(add='/hw_rescue_device',
                                value=hw_rescue_device)])
        return server, image_id

    def _test_stable_device_rescue(
            self, server, rescue_image_id,
            validation_resources=None):
        self.servers_client.rescue_server(
            server['id'], rescue_image_ref=rescue_image_id)
        waiters.wait_for_server_status(
            self.servers_client, server['id'], 'RESCUE')
        self.servers_client.unrescue_server(server['id'])
        # NOTE(gmann) In next addCleanup, server unrescue is called before the
        # detach volume is called in cleanup (added by self.attach_volume()
        # method) so to make sure server is ready before detach operation, we
        # need to perform ssh on it, more details are in bug#1960346.
        if validation_resources and CONF.validation.run_validation:
            tenant_network = self.get_tenant_network()
            compute.wait_for_ssh_or_ping(
                server, self.os_primary, tenant_network,
                True, validation_resources, "SSHABLE", True)
        else:
            waiters.wait_for_server_status(
                self.servers_client, server['id'], 'ACTIVE')


class ServerStableDeviceRescueTestIDE(BaseServerStableDeviceRescueTest):
    """Test rescuing server using an IDE device for the rescue disk"""

    @classmethod
    def skip_checks(cls):
        super().skip_checks()
        if not CONF.compute_feature_enabled.ide_bus:
            raise cls.skipException("IDE bus not available.")

    @decorators.idempotent_id('947004c3-e8ef-47d9-9f00-97b74f9eaf96')
    @testtools.skipIf("aarch64" in CONF.scenario.img_file,
                      "Aarch64 does not support ide bus for cdrom")
    def test_stable_device_rescue_cdrom_ide(self):
        """Test rescuing server with cdrom and ide as the rescue disk"""
        server, rescue_image_id = self._create_server_and_rescue_image(
            hw_rescue_device='cdrom', hw_rescue_bus='ide')
        self._test_stable_device_rescue(server, rescue_image_id)


class ServerStableDeviceRescueTest(BaseServerStableDeviceRescueTest):
    """Test rescuing server specifying type of device for the rescue disk"""

    @decorators.idempotent_id('16865750-1417-4854-bcf7-496e6753c01e')
    def test_stable_device_rescue_disk_virtio(self):
        """Test rescuing server with disk and virtio as the rescue disk"""
        server, rescue_image_id = self._create_server_and_rescue_image(
            hw_rescue_device='disk', hw_rescue_bus='virtio')
        self._test_stable_device_rescue(server, rescue_image_id)

    @decorators.idempotent_id('12340157-6306-4745-bdda-cfa019908b48')
    def test_stable_device_rescue_disk_scsi(self):
        """Test rescuing server with disk and scsi as the rescue disk"""
        server, rescue_image_id = self._create_server_and_rescue_image(
            hw_rescue_device='disk', hw_rescue_bus='scsi')
        self._test_stable_device_rescue(server, rescue_image_id)

    @decorators.idempotent_id('647d04cf-ad35-4956-89ab-b05c5c16f30c')
    def test_stable_device_rescue_disk_usb(self):
        """Test rescuing server with disk and usb as the rescue disk"""
        server, rescue_image_id = self._create_server_and_rescue_image(
            hw_rescue_device='disk', hw_rescue_bus='usb')
        self._test_stable_device_rescue(server, rescue_image_id)

    @decorators.idempotent_id('a3772b42-00bf-4310-a90b-1cc6fd3e7eab')
    @utils.services('volume')
    def test_stable_device_rescue_disk_virtio_with_volume_attached(self):
        """Test rescuing server with volume attached

        Attach a volume to the server and then rescue the server with disk
        and virtio as the rescue disk.
        """
        # This test just check detach fail and does not
        # perform the detach operation but in cleanup from
        # self.attach_volume() it will try to detach the server
        # after unrescue the server. Due to that we need to make
        # server SSHable before it try to detach, more details are
        # in bug#1960346
        volume = self.create_volume(wait_for_available=False)
        validation_resources = self.get_class_validation_resources(
            self.os_primary)
        server, rescue_image_id = self._create_server_and_rescue_image(
            hw_rescue_device='disk', hw_rescue_bus='virtio', validatable=True,
            validation_resources=validation_resources, wait_until="SSHABLE")
        server = self.servers_client.show_server(server['id'])['server']
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        self.attach_volume(server, volume)
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'in-use')
        self._test_stable_device_rescue(
            server, rescue_image_id,
            validation_resources=validation_resources)


class ServerBootFromVolumeStableRescueTest(BaseServerStableDeviceRescueTest):
    """Test rescuing server specifying type of device for the rescue disk

    Test rescuing server specifying type of device for the rescue disk with
    compute microversion greater than 2.86.
    """

    min_microversion = '2.87'

    @classmethod
    def skip_checks(cls):
        super(ServerBootFromVolumeStableRescueTest, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('48f123cb-922a-4065-8db6-b9a9074a556b')
    def test_stable_device_rescue_bfv_blank_volume(self):
        """Test rescuing server with blank volume as block_device_mapping_v2

        Create a server with block_device_mapping_v2 with blank volume,
        then rescue the server with disk and virtio as the rescue disk.
        """
        block_device_mapping_v2 = [{
            "boot_index": "0",
            "source_type": "blank",
            "volume_size": CONF.volume.volume_size,
            "destination_type": "volume"}]
        server, rescue_image_id = self._create_server_and_rescue_image(
            hw_rescue_device='disk', hw_rescue_bus='virtio',
            block_device_mapping_v2=block_device_mapping_v2)
        self._test_stable_device_rescue(server, rescue_image_id)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('e4636333-c928-40fc-98b7-70a23eef4224')
    def test_stable_device_rescue_bfv_image_volume(self):
        """Test rescuing server with blank volume as block_device_mapping_v2

        Create a server with block_device_mapping_v2 with image volume,
        then rescue the server with disk and virtio as the rescue disk.
        """
        block_device_mapping_v2 = [{
            "boot_index": "0",
            "source_type": "image",
            "volume_size": CONF.volume.volume_size,
            "uuid": CONF.compute.image_ref,
            "destination_type": "volume"}]
        server, rescue_image_id = self._create_server_and_rescue_image(
            hw_rescue_device='disk', hw_rescue_bus='virtio',
            block_device_mapping_v2=block_device_mapping_v2)
        self._test_stable_device_rescue(server, rescue_image_id)
