#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import fixtures
from oslo_log import log as logging

from tempest.lib.services.volume import base_client

LOG = logging.getLogger(__name__)


class APIMicroversionFixture(fixtures.Fixture):

    def __init__(self, volume_microversion):
        self.volume_microversion = volume_microversion
        new_fixture = (
            'tempest.lib.common.api_microversion_fixture.'
            'APIMicroversionFixture')
        LOG.warning("%s class is deprecated and moved to %s. It"
                    " will be removed in Z cycle.",
                    self.__class__.__name__, new_fixture)

    def _setUp(self):
        super(APIMicroversionFixture, self)._setUp()
        base_client.VOLUME_MICROVERSION = self.volume_microversion
        self.addCleanup(self._reset_volume_microversion)

    def _reset_volume_microversion(self):
        base_client.VOLUME_MICROVERSION = None
