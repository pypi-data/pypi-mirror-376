# Copyright 2013 IBM Corp.
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
import time

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions
import tempest.test

CONF = config.CONF
BAD_REQUEST_RETRIES = 3


class BaseImageTest(tempest.test.BaseTestCase):
    """Base test class for Image API tests."""

    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseImageTest, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(BaseImageTest, cls).setup_credentials()

    @classmethod
    def resource_setup(cls):
        super(BaseImageTest, cls).resource_setup()
        cls.created_images = []

    @classmethod
    def create_image(cls, data=None, **kwargs):
        """Wrapper that returns a test image."""

        if 'name' not in kwargs:
            name = data_utils.rand_name(
                prefix=CONF.resource_name_prefix,
                name=cls.__name__ + "-image")
            kwargs['name'] = name

        image = cls.client.create_image(**kwargs)
        cls.created_images.append(image['id'])
        cls.addClassResourceCleanup(cls.client.wait_for_resource_deletion,
                                    image['id'])
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    cls.client.delete_image, image['id'])
        return image


class BaseV2ImageTest(BaseImageTest):

    @classmethod
    def skip_checks(cls):
        super(BaseV2ImageTest, cls).skip_checks()
        if not CONF.image_feature_enabled.api_v2:
            msg = "Glance API v2 not supported"
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(BaseV2ImageTest, cls).setup_clients()
        cls.client = cls.os_primary.image_client_v2
        cls.schemas_client = cls.os_primary.schemas_client
        cls.versions_client = cls.os_primary.image_versions_client

    def create_namespace(self, namespace_name=None, visibility='public',
                         description='Tempest', protected=False,
                         **kwargs):
        if not namespace_name:
            namespace_name = data_utils.rand_name(
                prefix=CONF.resource_name_prefix, name='test-ns')
        kwargs.setdefault('display_name', namespace_name)
        namespace = self.namespaces_client.create_namespace(
            namespace=namespace_name, visibility=visibility,
            description=description, protected=protected, **kwargs)
        self.addCleanup(self.namespaces_client.delete_namespace,
                        namespace_name)
        return namespace

    def create_and_stage_image(self, all_stores=False):
        """Create Image & stage image file for glance-direct import method."""
        image_name = data_utils.rand_name('test-image')
        container_format = CONF.image.container_formats[0]
        image = self.create_image(name=image_name,
                                  container_format=container_format,
                                  disk_format='raw',
                                  visibility='private')
        self.assertEqual('queued', image['status'])

        self.client.stage_image_file(
            image['id'],
            io.BytesIO(data_utils.random_bytes()))
        # Check image status is 'uploading'
        body = self.client.show_image(image['id'])
        self.assertEqual(image['id'], body['id'])
        self.assertEqual('uploading', body['status'])

        if all_stores:
            stores_list = ','.join([store['id']
                                    for store in self.available_stores
                                    if store.get('read-only') != 'true'])
        else:
            stores = [store['id'] for store in self.available_stores
                      if store.get('read-only') != 'true']
            stores_list = stores[::max(1, len(stores) - 1)]

        return body, stores_list

    @classmethod
    def get_available_stores(cls):
        stores = []
        try:
            stores = cls.client.info_stores()['stores']
        except exceptions.NotFound:
            pass
        return stores

    def _update_image_with_retries(self, image, patch):
        # NOTE(danms): If glance was unable to fetch the remote image via
        # HTTP, it will return BadRequest. Because this can be transient in
        # CI, we try this a few times before we agree that it has failed
        # for a reason worthy of failing the test.
        for i in range(BAD_REQUEST_RETRIES):
            try:
                self.client.update_image(image, patch)
                break
            except exceptions.BadRequest:
                if i + 1 == BAD_REQUEST_RETRIES:
                    raise
                else:
                    time.sleep(1)

    def check_set_location(self):
        image = self.client.create_image(container_format='bare',
                                         disk_format='raw')

        # Locations should be empty when there is no data
        self.assertEqual('queued', image['status'])
        self.assertEqual([], image['locations'])

        # Add a new location
        new_loc = {'metadata': {'foo': 'bar'},
                   'url': CONF.image.http_image}
        self._update_image_with_retries(image['id'], [
            dict(add='/locations/-', value=new_loc)])

        # The image should now be active, with one location that looks
        # like we expect
        image = self.client.show_image(image['id'])
        self.assertEqual(1, len(image['locations']),
                         'Image should have one location but has %i' % (
                         len(image['locations'])))
        self.assertEqual(new_loc['url'], image['locations'][0]['url'])
        self.assertEqual('bar', image['locations'][0]['metadata'].get('foo'))
        if 'direct_url' in image:
            self.assertEqual(image['direct_url'], image['locations'][0]['url'])

        # If we added the location directly, the image goes straight
        # to active and no hashing is done
        self.assertEqual('active', image['status'])
        self.assertIsNone(image['os_hash_algo'])
        self.assertIsNone(image['os_hash_value'])

        return image

    def check_set_multiple_locations(self):
        image = self.check_set_location()

        new_loc = {'metadata': {'speed': '88mph'},
                   'url': '%s#new' % CONF.image.http_image}
        self._update_image_with_retries(image['id'],
                                        [dict(add='/locations/-',
                                              value=new_loc)])

        # The image should now have two locations and the last one
        # (locations are ordered) should have the new URL.
        image = self.client.show_image(image['id'])
        self.assertEqual(2, len(image['locations']),
                         'Image should have two locations but has %i' % (
                         len(image['locations'])))
        self.assertEqual(new_loc['url'], image['locations'][1]['url'])

        # The image should still be active and still have no hashes
        self.assertEqual('active', image['status'])
        self.assertIsNone(image['os_hash_algo'])
        self.assertIsNone(image['os_hash_value'])

        # The direct_url should still match the first location
        if 'direct_url' in image:
            self.assertEqual(image['direct_url'], image['locations'][0]['url'])

        return image


class BaseV2MemberImageTest(BaseV2ImageTest):

    credentials = ['primary', 'alt']

    @classmethod
    def setup_clients(cls):
        super(BaseV2MemberImageTest, cls).setup_clients()
        cls.image_member_client = cls.os_primary.image_member_client_v2
        cls.alt_image_member_client = cls.os_alt.image_member_client_v2
        cls.alt_img_client = cls.os_alt.image_client_v2

    @classmethod
    def resource_setup(cls):
        super(BaseV2MemberImageTest, cls).resource_setup()
        cls.alt_tenant_id = cls.alt_image_member_client.tenant_id

    def _list_image_ids_as_alt(self):
        image_list = self.alt_img_client.list_images()['images']
        image_ids = map(lambda x: x['id'], image_list)
        return image_ids

    def _create_image(self):
        name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name=self.__class__.__name__ + '-image')
        image = self.client.create_image(name=name,
                                         container_format='bare',
                                         disk_format='raw')
        self.addCleanup(self.client.delete_image, image['id'])
        return image['id']


class BaseV2ImageAdminTest(BaseV2ImageTest):

    credentials = ['admin', 'primary']

    @classmethod
    def setup_clients(cls):
        super(BaseV2ImageAdminTest, cls).setup_clients()
        cls.admin_client = cls.os_admin.image_client_v2
        cls.namespaces_client = cls.os_admin.namespaces_client
        cls.resource_types_client = cls.os_admin.resource_types_client
        cls.namespace_properties_client =\
            cls.os_admin.namespace_properties_client
        cls.namespace_objects_client = cls.os_admin.namespace_objects_client
        cls.namespace_tags_client = cls.os_admin.namespace_tags_client
