# Copyright 2022 Red Hat, Inc.
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

import io

from oslo_log import log as logging
from tempest.api.image import base
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


CONF = config.CONF
LOG = logging.getLogger(__name__)


class ImageCachingTest(base.BaseV2ImageTest):
    """Here we test the caching operations for image"""
    credentials = ['primary', 'admin']

    def setUp(self):
        super(ImageCachingTest, self).setUp()
        # NOTE(abhishekk): As caching is enabled instance boot or volume
        # boot or image download can also cache image, so we are going to
        # maintain our caching information to avoid disturbing other tests
        self.cached_info = []
        self.cached_info_remote = []

    def tearDown(self):
        # Delete all from cache/queue if we exit abruptly
        for image_id in self.cached_info:
            self.os_admin.image_cache_client.cache_delete(image_id)

        for image_id in self.cached_info_remote:
            self.os_admin.image_cache_client.cache_delete(image_id)

        super(ImageCachingTest, self).tearDown()

    @classmethod
    def skip_checks(cls):
        super(ImageCachingTest, cls).skip_checks()
        # Check to see if we should even be running these tests.
        if not CONF.image.image_caching_enabled:
            raise cls.skipException('Target system is not configured with '
                                    'glance caching')

    def image_create_and_upload(self, upload=True, **kwargs):
        """Wrapper that returns a test image."""
        if 'name' not in kwargs:
            name = data_utils.rand_name(
                prefix=CONF.resource_name_prefix,
                name=self.__name__ + "-image")
            kwargs['name'] = name

        params = dict(kwargs)
        image = self.create_image(**params)
        self.assertEqual('queued', image['status'])
        if not upload:
            return image

        file_content = data_utils.random_bytes()
        image_file = io.BytesIO(file_content)
        self.client.store_image_file(image['id'], image_file)

        image = self.client.show_image(image['id'])
        return image

    def _assertCheckCache(self, cached_images, cached):
        cached_list = []
        for image in cached_images:
            cached_list.append(image['image_id'])

        for image in cached:
            self.assertIn(image, cached_list)

    @decorators.idempotent_id('4bf6adba-2f9f-47e9-a6d5-37f21ad4387c')
    def test_image_caching_cycle(self):
        """Test image cache APIs"""
        # Ensure that non-admin user is not allowed to perform caching
        # operations
        self.assertRaises(lib_exc.Forbidden,
                          self.os_primary.image_cache_client.list_cache)

        # Check there is nothing cached by us
        output = self.os_admin.image_cache_client.list_cache()
        self._assertCheckCache(output['cached_images'], self.cached_info)

        # Non-existing image should raise NotFound exception
        self.assertRaises(lib_exc.NotFound,
                          self.os_admin.image_cache_client.cache_queue,
                          'non-existing-image-id')

        # Verify that we can not use queued image for queueing
        image = self.image_create_and_upload(name='queued', upload=False)
        self.assertRaises(lib_exc.BadRequest,
                          self.os_admin.image_cache_client.cache_queue,
                          image['id'])

        # Create one image
        image = self.image_create_and_upload(name='first',
                                             container_format='bare',
                                             disk_format='raw',
                                             visibility='private')
        self.assertEqual('active', image['status'])

        # Queue image for caching
        self.os_admin.image_cache_client.cache_queue(image['id'])
        # Wait for image caching
        LOG.info("Waiting for image %s to get cached", image['id'])
        caching = waiters.wait_for_caching(
            self.client,
            self.os_admin.image_cache_client,
            image['id'])

        self.cached_info.append(image['id'])
        # verify that we have image cached
        self._assertCheckCache(caching['cached_images'], self.cached_info)

        # Verify that we can delete images from caching and queueing with
        # api call.
        self.os_admin.image_cache_client.cache_clear()
        output = self.os_admin.image_cache_client.list_cache()
        self.assertEqual(0, len(output['queued_images']))
        self.assertEqual(0, len(output['cached_images']))

        # Verify that invalid header value for target returns 400 response
        self.assertRaises(lib_exc.BadRequest,
                          self.os_admin.image_cache_client.cache_clear,
                          target="invalid")
        # Remove all data from local information
        self.cached_info = []

    @decorators.idempotent_id('0a6b7e10-bc30-4a41-91ff-69fb4f5e65f2')
    def test_remote_and_self_cache(self):
        """Test image cache works with self and remote glance service"""
        if not CONF.image.alternate_image_endpoint:
            raise self.skipException('No image_remote service to test '
                                     'against')

        # Check there is nothing is cached by us on current and
        # remote node
        output = self.os_admin.image_cache_client.list_cache()
        self._assertCheckCache(output['cached_images'], self.cached_info)

        output = self.os_admin.cache_client_remote.list_cache()
        self._assertCheckCache(output['cached_images'],
                               self.cached_info_remote)

        # Create one image
        image = self.image_create_and_upload(name='first',
                                             container_format='bare',
                                             disk_format='raw',
                                             visibility='private')
        self.assertEqual('active', image['status'])

        # Queue image for caching on local node
        self.os_admin.image_cache_client.cache_queue(image['id'])
        # Wait for image caching
        LOG.info("Waiting for image %s to get cached", image['id'])
        caching = waiters.wait_for_caching(
            self.client,
            self.os_admin.image_cache_client,
            image['id'])
        self.cached_info.append(image['id'])
        # verify that we have image in cache on local node
        self._assertCheckCache(caching['cached_images'], self.cached_info)
        # verify that we don't have anything cached on remote node
        output = self.os_admin.cache_client_remote.list_cache()
        self._assertCheckCache(output['cached_images'],
                               self.cached_info_remote)

        # cache same image on remote node
        self.os_admin.cache_client_remote.cache_queue(image['id'])
        # Wait for image caching
        LOG.info("Waiting for image %s to get cached", image['id'])
        caching = waiters.wait_for_caching(
            self.client,
            self.os_admin.cache_client_remote,
            image['id'])
        self.cached_info_remote.append(image['id'])

        # verify that we have image cached on remote node
        output = self.os_admin.cache_client_remote.list_cache()
        self._assertCheckCache(output['cached_images'],
                               self.cached_info_remote)

        # Verify that we can delete image from remote cache and it
        # still present in local cache
        self.os_admin.cache_client_remote.cache_clear()
        output = self.os_admin.cache_client_remote.list_cache()
        self.assertEqual(0, len(output['queued_images']))
        self.assertEqual(0, len(output['cached_images']))

        output = self.os_admin.image_cache_client.list_cache()
        self._assertCheckCache(output['cached_images'], self.cached_info)

        # Delete image from local cache as well
        self.os_admin.image_cache_client.cache_clear()
        output = self.os_admin.image_cache_client.list_cache()
        self.assertEqual(0, len(output['queued_images']))
        self.assertEqual(0, len(output['cached_images']))

        # Remove all data from local and remote information
        self.cached_info = []
        self.cached_info_remote = []
