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

from oslo_log import log as logging
import testtools

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestVolumeBootPattern(manager.EncryptionScenarioTest):

    # Boot from volume scenario is quite slow, and needs extra
    # breathing room to get through deletes in the time allotted.
    TIMEOUT_SCALING_FACTOR = 2

    @classmethod
    def skip_checks(cls):
        super(TestVolumeBootPattern, cls).skip_checks()
        if not CONF.service_available.cinder:
            raise cls.skipException("Cinder is not available")

    @classmethod
    def setup_clients(cls):
        super(TestVolumeBootPattern, cls).setup_clients()
        cls.servers_client = cls.os_primary.servers_client

    def _delete_server(self, server):
        self.servers_client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.servers_client, server['id'])

    def _delete_snapshot(self, snapshot_id):
        self.snapshots_client.delete_snapshot(snapshot_id)
        self.snapshots_client.wait_for_resource_deletion(snapshot_id)

    @decorators.idempotent_id('557cd2c2-4eb8-4dce-98be-f86765ff311b')
    @decorators.attr(type='slow')
    # Note: This test is being skipped based on 'public_network_id'.
    # It is being used in create_floating_ip() method which gets called
    # from get_server_ip() method
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          'Cinder volume snapshots are disabled')
    @utils.services('compute', 'volume', 'image')
    def test_volume_boot_pattern(self):
        """This test case attempts to reproduce the following steps:

        * Create in Cinder some bootable volume importing a Glance image
        * Boot an instance from the bootable volume
        * Write content to the volume
        * Delete an instance and Boot a new instance from the volume
        * Check written content in the instance
        * Create a volume snapshot while the instance is running
        * Boot an additional instance from the new snapshot based volume
        * Check written content in the instance booted from snapshot
        """

        LOG.info("Creating keypair and security group")
        keypair = self.create_keypair()
        security_group = self.create_security_group()

        # create an instance from volume
        LOG.info("Booting instance 1 from volume")
        volume_origin = self.create_volume_from_image()
        instance_1st = self.boot_instance_from_resource(
            source_id=volume_origin['id'],
            source_type='volume',
            keypair=keypair,
            security_group=security_group)
        LOG.info("Booted first instance: %s", instance_1st)

        # write content to volume on instance
        LOG.info("Setting timestamp in instance %s", instance_1st)
        ip_instance_1st = self.get_server_ip(instance_1st)
        timestamp = self.create_timestamp(ip_instance_1st,
                                          private_key=keypair['private_key'],
                                          server=instance_1st)

        # delete instance
        LOG.info("Deleting first instance: %s", instance_1st)
        self._delete_server(instance_1st)

        # create a 2nd instance from volume
        instance_2nd = self.boot_instance_from_resource(
            source_id=volume_origin['id'],
            source_type='volume',
            keypair=keypair,
            security_group=security_group)
        LOG.info("Booted second instance %s", instance_2nd)

        # check the content of written file
        LOG.info("Getting timestamp in instance %s", instance_2nd)
        ip_instance_2nd = self.get_server_ip(instance_2nd)
        timestamp2 = self.get_timestamp(ip_instance_2nd,
                                        private_key=keypair['private_key'],
                                        server=instance_2nd)
        self.assertEqual(timestamp, timestamp2)

        # snapshot a volume
        LOG.info("Creating snapshot from volume: %s", volume_origin['id'])
        snapshot = self.create_volume_snapshot(volume_origin['id'], force=True)

        # create a 3rd instance from snapshot
        LOG.info("Creating third instance from snapshot: %s", snapshot['id'])
        volume = self.create_volume(snapshot_id=snapshot['id'],
                                    size=snapshot['size'])
        LOG.info("Booting third instance from snapshot")
        server_from_snapshot = (
            self.boot_instance_from_resource(source_id=volume['id'],
                                             source_type='volume',
                                             keypair=keypair,
                                             security_group=security_group))
        LOG.info("Booted third instance %s", server_from_snapshot)

        # check the content of written file
        LOG.info("Logging into third instance to get timestamp: %s",
                 server_from_snapshot)
        server_from_snapshot_ip = self.get_server_ip(server_from_snapshot)
        timestamp3 = self.get_timestamp(server_from_snapshot_ip,
                                        private_key=keypair['private_key'],
                                        server=server_from_snapshot)
        self.assertEqual(timestamp, timestamp3)

    @decorators.idempotent_id('e3f4f2fc-5c6a-4be6-9c54-aedfc0954da7')
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          'Cinder volume snapshots are disabled')
    @utils.services('compute', 'volume', 'image')
    def test_bootable_volume_snapshot_stop_start_instance(self):
        # Step 1: Create a bootable volume from an image
        volume = self.create_volume_from_image()

        # Step 2: Boot an instance from the created volume
        instance = self.boot_instance_from_resource(
            source_id=volume['id'],
            source_type='volume',
            wait_until='SSHABLE'
        )

        # Step 3: Stop the instance
        self.servers_client.stop_server(instance['id'])
        waiters.wait_for_server_status(self.servers_client, instance['id'],
                                       'SHUTOFF')

        # Step 4: Create a snapshot of the bootable volume
        self.create_volume_snapshot(volume['id'], force=True)

        # Step 5: Start the instance and verify it returns to ACTIVE state
        self.servers_client.start_server(instance['id'])
        waiters.wait_for_server_status(self.servers_client, instance['id'],
                                       'ACTIVE')

        # Step 6: Verify console log
        self.log_console_output([instance])

    @decorators.idempotent_id('05795fb2-b2a7-4c9f-8fac-ff25aedb1489')
    @decorators.attr(type='slow')
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          'Cinder volume snapshots are disabled')
    @utils.services('compute', 'image', 'volume')
    def test_create_server_from_volume_snapshot(self):
        # Create a volume from an image
        boot_volume = self.create_volume_from_image()

        # Create a snapshot
        boot_snapshot = self.create_volume_snapshot(boot_volume['id'])

        # Create a server from a volume snapshot
        server = self.boot_instance_from_resource(
            source_id=boot_snapshot['id'],
            source_type='snapshot',
            delete_on_termination=True)

        server_info = self.servers_client.show_server(server['id'])['server']

        # The created volume when creating a server from a snapshot
        created_volume = server_info['os-extended-volumes:volumes_attached']

        self.assertNotEmpty(created_volume, "No volume attachment found.")

        created_volume_info = self.volumes_client.show_volume(
            created_volume[0]['id'])['volume']

        # Verify the server was created from the snapshot
        self.assertEqual(
            boot_volume['volume_image_metadata']['image_id'],
            created_volume_info['volume_image_metadata']['image_id'])
        self.assertEqual(boot_snapshot['id'],
                         created_volume_info['snapshot_id'])
        self.assertEqual(server['id'],
                         created_volume_info['attachments'][0]['server_id'])
        self.assertEqual(created_volume[0]['id'],
                         created_volume_info['attachments'][0]['volume_id'])

        # Delete the server and wait
        self._delete_server(server)

        # Assert that the underlying volume is gone before class tearDown
        # to prevent snapshot deletion from failing
        self.volumes_client.wait_for_resource_deletion(created_volume[0]['id'])

    @decorators.idempotent_id('36c34c67-7b54-4b59-b188-02a2f458a63b')
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          'Cinder volume snapshots are disabled')
    @utils.services('compute', 'volume', 'image')
    def test_image_defined_boot_from_volume(self):
        # create an instance from image-backed volume
        volume_origin = self.create_volume_from_image()
        name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name=self.__class__.__name__ + '-volume-backed-server')
        instance1 = self.boot_instance_from_resource(
            source_id=volume_origin['id'],
            source_type='volume',
            delete_on_termination=True,
            wait_until='SSHABLE',
            name=name)
        # Create a snapshot image from the volume-backed server.
        # The compute service will have the block service create a snapshot of
        # the root volume and store its metadata in the image.
        image = self.create_server_snapshot(instance1)

        # Create a server from the image snapshot which has an
        # "image-defined block device mapping (BDM)" in it, i.e. the metadata
        # about the volume snapshot. The compute service will use this to
        # create a volume from the volume snapshot and use that as the root
        # disk for the server.
        name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name=self.__class__.__name__ + '-image-snapshot-server')
        instance2 = self.create_server(image_id=image['id'], name=name,
                                       wait_until='SSHABLE')

        # Verify the server was created from the image-defined BDM.
        volume_attachments = instance2['os-extended-volumes:volumes_attached']
        self.assertEqual(1, len(volume_attachments),
                         "No volume attachment found.")
        created_volume = self.volumes_client.show_volume(
            volume_attachments[0]['id'])['volume']
        # Assert that the volume service also shows the server attachment.
        self.assertEqual(1, len(created_volume['attachments']),
                         "No server attachment found for volume: %s" %
                         created_volume)
        self.assertEqual(instance2['id'],
                         created_volume['attachments'][0]['server_id'])
        self.assertEqual(volume_attachments[0]['id'],
                         created_volume['attachments'][0]['volume_id'])
        self.assertEqual(
            volume_origin['volume_image_metadata']['image_id'],
            created_volume['volume_image_metadata']['image_id'])

        # Delete the second server which should also delete the second volume
        # created from the volume snapshot.
        self._delete_server(instance2)

        # Assert that the underlying volume is gone.
        self.volumes_client.wait_for_resource_deletion(created_volume['id'])

        # Delete the volume snapshot. We must do this before deleting the first
        # server created in this test because the snapshot depends on the first
        # instance's underlying volume (volume_origin).
        # In glance v2, the image properties are flattened and in glance v1,
        # the image properties are under the 'properties' key.
        bdms = image.get('block_device_mapping')
        if not bdms:
            bdms = image['properties']['block_device_mapping']
        snapshot_id = self.get_snapshot_id(bdms)
        self._delete_snapshot(snapshot_id)

        # Now, delete the first server which will also delete the first
        # image-backed volume.
        self._delete_server(instance1)

        # Assert that the underlying volume is gone.
        self.volumes_client.wait_for_resource_deletion(volume_origin['id'])

    def _do_test_boot_server_from_encrypted_volume_luks(self, provider):
        # Create an encrypted volume
        volume = self.create_encrypted_volume(provider,
                                              volume_type=provider)

        self.volumes_client.set_bootable_volume(volume['id'], bootable=True)

        # Boot a server from the encrypted volume
        server = self.boot_instance_from_resource(
            source_id=volume['id'],
            source_type='volume',
            delete_on_termination=False)

        server_info = self.servers_client.show_server(server['id'])['server']
        created_volume = server_info['os-extended-volumes:volumes_attached']
        self.assertEqual(volume['id'], created_volume[0]['id'])

    @decorators.idempotent_id('cb78919a-e553-4bab-b73b-10cf4d2eb125')
    @testtools.skipUnless(CONF.compute_feature_enabled.attach_encrypted_volume,
                          'Encrypted volume attach is not supported')
    @utils.services('compute', 'volume')
    def test_boot_server_from_encrypted_volume_luks(self):
        """LUKs v1 decrypts volume through libvirt."""
        self._do_test_boot_server_from_encrypted_volume_luks('luks')

    @decorators.idempotent_id('5ab6100f-1b31-4dd0-a774-68cfd837ef77')
    @testtools.skipIf(CONF.volume.storage_protocol == 'ceph',
                      'Ceph only supports LUKSv2 if doing host attach.')
    @testtools.skipUnless(CONF.compute_feature_enabled.attach_encrypted_volume,
                          'Encrypted volume attach is not supported')
    @utils.services('compute', 'volume')
    def test_boot_server_from_encrypted_volume_luksv2(self):
        """LUKs v2 decrypts volume through os-brick."""
        self._do_test_boot_server_from_encrypted_volume_luks('luks2')


class TestVolumeBootPatternV346(manager.EncryptionScenarioTest):

    volume_min_microversion = '3.46'
    volume_max_microversion = 'latest'

    @decorators.idempotent_id('77889046-1a75-4f14-9b3a-fbbfdd8e5093')
    @decorators.attr(type='slow')
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          'Cinder volume snapshots are disabled')
    @utils.services('compute', 'volume', 'image')
    def test_instance_boot_after_snapshot_deletion(self):
        """Test instance bootability after deleting snapshots.

        This test ensures volumes created from instance snapshots
        are bootable with volume API microversion >= 3.46.

        Steps:
        1. Create a bootable volume1 from an image.
        2. Launch an instance1 from the created volume.
        3. Create image1 - a snapshot1 of the instance1.
        4. Create a volume2 from the image1.
        5. Boot an instance2 from the volume2 to verify it's bootable.
        6. Delete image1 - the first instance1 snapshot1.
        7. Create image2 - a snapshot2 of the instance1.
        8. Create a volume3 from the image2.
        9. Boot instance3 from the new volume3 to verify it's bootable.
        """

        # Step 1: Create a bootable volume1 from an image
        volume1 = self.create_volume_from_image()

        # Step 2: Launch instance1 from volume1
        instance1 = self.boot_instance_from_resource(
            source_id=volume1['id'],
            source_type='volume',
            wait_until='SSHABLE'
        )

        # Step 3: Create image1 – a snapshot of the instance1
        image1 = self.create_server_snapshot(instance1)

        # Step 4: Create volume2 from image1
        volume2 = self.create_volume_from_image(image_id=image1['id'])

        # Step 5: Launch instance2 from volume2
        self.boot_instance_from_resource(
            source_id=volume2['id'],
            source_type='volume',
            wait_until='SSHABLE'
        )

        # Step 6: Delete image1
        self.image_client.delete_image(image1['id'])
        self.image_client.wait_for_resource_deletion(image1['id'])

        # Step 7: Create image2 – a snapshot of the instance1
        image2 = self.create_server_snapshot(instance1)

        # Step 8: Create volume3 from image2
        volume3 = self.create_volume_from_image(image_id=image2['id'])

        # Step 9: Launch instance from volume3
        self.boot_instance_from_resource(
            source_id=volume3['id'],
            source_type='volume',
            wait_until='SSHABLE'
        )
