# Copyright 2013 IBM Corp.
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

import functools
from urllib import parse as urllib

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc

CHUNKSIZE = 1024 * 64  # 64kB


class ImagesClient(rest_client.RestClient):
    api_version = "v2"

    def update_image(self, image_id, patch):
        """Update an image.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#update-image
        """
        data = json.dumps(patch)
        headers = {"Content-Type": "application/openstack-images-v2.0"
                                   "-json-patch"}
        resp, body = self.patch('images/%s' % image_id, data, headers)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def create_image(self, **kwargs):
        """Create an image.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#create-image
        """
        data = json.dumps(kwargs)
        resp, body = self.post('images', data)
        self.expected_success(201, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def deactivate_image(self, image_id):
        """Deactivate image.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#deactivate-image
        """
        url = 'images/%s/actions/deactivate' % image_id
        resp, body = self.post(url, None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reactivate_image(self, image_id):
        """Reactivate image.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#reactivate-image
        """
        url = 'images/%s/actions/reactivate' % image_id
        resp, body = self.post(url, None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_image(self, image_id):
        """Delete image.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#delete-image
         """
        url = 'images/%s' % image_id
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def list_images(self, params=None):
        """List images.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#list-images
        """
        url = 'images'

        if params:
            url += '?%s' % urllib.urlencode(params)

        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_image(self, image_id):
        """Show image details.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#show-image
        """
        url = 'images/%s' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def show_image_tasks(self, image_id):
        """Show image tasks."""
        url = 'images/%s/tasks' % image_id
        resp, body = self.get(url)
        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_image(id)
        except lib_exc.NotFound:
            return True
        return False

    def is_resource_active(self, id):
        try:
            image = self.show_image(id)
            if image['status'] != 'active':
                return False
        except lib_exc.NotFound:
            return False
        return True

    @property
    def resource_type(self):
        """Returns the primary type of resource this client works with."""
        return 'image'

    def store_image_file(self, image_id, data):
        """Upload binary image data.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#upload-binary-image-data
        """
        url = 'images/%s/file' % image_id

        # We are going to do chunked transfer, so split the input data
        # info fixed-sized chunks.
        headers = {'Content-Type': 'application/octet-stream'}
        data = iter(functools.partial(data.read, CHUNKSIZE), b'')

        resp, body = self.request('PUT', url, headers=headers,
                                  body=data, chunked=True)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def stage_image_file(self, image_id, data):
        """Upload binary image data to staging area.

        For a full list of available parameters, please refer to the official
        API reference (stage API:
        https://docs.openstack.org/api-ref/image/v2/#interoperable-image-import
        """
        url = 'images/%s/stage' % image_id

        # We are going to do chunked transfer, so split the input data
        # info fixed-sized chunks.
        headers = {'Content-Type': 'application/octet-stream'}
        data = iter(functools.partial(data.read, CHUNKSIZE), b'')

        resp, body = self.request('PUT', url, headers=headers,
                                  body=data, chunked=True)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def info_import(self):
        """Return information about server-supported import methods."""
        url = 'info/import'
        resp, body = self.get(url)

        self.expected_success(200, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def info_stores(self):
        """Return information about server-supported stores."""
        url = 'info/stores'
        resp, body = self.get(url)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)

    def image_import(self, image_id, method='glance-direct',
                     all_stores_must_succeed=None, all_stores=True,
                     stores=None, import_params=None):
        """Import data from staging area to glance store.

        For a full list of available parameters, please refer to the official
        API reference (stage API:
        https://docs.openstack.org/api-ref/image/v2/#interoperable-image-import

        :param method: The import method (i.e. glance-direct) to use
        :param all_stores_must_succeed: Boolean indicating if all store imports
                                        must succeed for the import to be
                                        considered successful. Must be None if
                                        server does not support multistore.
        :param all_stores: Boolean indicating if image should be imported to
                           all available stores (incompatible with stores)
        :param stores: A list of destination store names for the import. Must
                       be None if server does not support multistore.
        :param import_params: A dict of import method parameters
        """
        url = 'images/%s/import' % image_id
        if import_params is None:
            import_params = {}
        data = {
            "method": {
                "name": method
            },
        }
        if stores is not None:
            data["stores"] = stores
        else:
            data["all_stores"] = all_stores

        if all_stores_must_succeed is not None:
            data['all_stores_must_succeed'] = all_stores_must_succeed
        if import_params:
            data['method'].update(import_params)
        data = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        resp, _ = self.post(url, data, headers=headers)

        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp)

    def show_image_file(self, image_id, chunked=False):
        """Download binary image data.

        :param bool chunked: If True, do not read the body and return only
                             the raw urllib3 response object for processing.
                             NB: If you pass True here, you **MUST** call
                             release_conn() on the response object before
                             finishing!

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#download-binary-image-data
        """
        url = 'images/%s/file' % image_id
        resp, body = self.get(url, chunked=chunked)
        self.expected_success([200, 204, 206], resp.status)
        if chunked:
            return resp
        else:
            return rest_client.ResponseBodyData(resp, body)

    def add_image_tag(self, image_id, tag):
        """Add an image tag.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#add-image-tag
        """
        url = 'images/%s/tags/%s' % (image_id, tag)
        resp, body = self.put(url, body=None)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_image_tag(self, image_id, tag):
        """Delete an image tag.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/image/v2/#delete-image-tag
        """
        url = 'images/%s/tags/%s' % (image_id, tag)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def delete_image_from_store(self, image_id, store_name):
        """Delete image from store

        For a full list of available parameters,
        please refer to the official API reference:
        https://docs.openstack.org/api-ref/image/v2/#delete-image-from-store
        """
        url = 'stores/%s/%s' % (store_name, image_id)
        resp, _ = self.delete(url)
        self.expected_success(204, resp.status)
        return rest_client.ResponseBody(resp)

    def add_image_location(self, image_id, url, validation_data=None):
        """Add location for specific Image."""
        if not validation_data:
            validation_data = {}
        data = json.dumps({'url': url, 'validation_data': validation_data})
        resp, _ = self.post('images/%s/locations' % (image_id),
                            data)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp)
