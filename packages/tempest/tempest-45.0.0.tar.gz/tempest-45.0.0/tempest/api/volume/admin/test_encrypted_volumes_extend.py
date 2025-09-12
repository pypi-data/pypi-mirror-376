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

from tempest.api.volume import base
from tempest.api.volume import test_volumes_extend as extend
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class EncryptedVolumesExtendAttachedTest(extend.BaseVolumesExtendAttachedTest,
                                         base.BaseVolumeAdminTest):
    """Tests extending the size of an attached encrypted volume."""

    @classmethod
    def skip_checks(cls):
        super(EncryptedVolumesExtendAttachedTest, cls).skip_checks()
        if not CONF.service_available.nova:
            skip_msg = ("%s skipped as Nova is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        if not CONF.volume_feature_enabled.extend_attached_encrypted_volume:
            raise cls.skipException(
                "Attached encrypted volume extend is disabled.")

    @decorators.skip_because(bug="2116852")
    @decorators.idempotent_id('e93243ec-7c37-4b5b-a099-ebf052c13216')
    def test_extend_attached_encrypted_volume_luksv1(self):
        """LUKs v1 decrypts and extends through libvirt."""
        volume = self.create_encrypted_volume(encryption_provider="luks")
        self._test_extend_attached_volume(volume)

    @decorators.idempotent_id('381a2a3a-b2f4-4631-a910-720881f2cc2f')
    @testtools.skipIf(CONF.volume.storage_protocol == 'ceph',
                      'Ceph only supports LUKSv2 if doing host attach.')
    def test_extend_attached_encrypted_volume_luksv2(self):
        """LUKs v2 decrypts and extends through os-brick."""
        volume = self.create_encrypted_volume(encryption_provider="luks2")
        self._test_extend_attached_volume(volume)
