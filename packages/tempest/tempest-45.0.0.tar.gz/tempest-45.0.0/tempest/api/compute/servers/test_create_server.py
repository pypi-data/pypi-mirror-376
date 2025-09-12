# Copyright 2012 OpenStack Foundation
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

import netaddr
import testtools

from oslo_serialization import jsonutils as json

from tempest.api.compute import base
from tempest.common import utils
from tempest.common.utils.linux import remote_client
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class ServersTestJSON(base.BaseV2ComputeTest):
    """Test creating server and verifying the server attributes

    This is to create server booted from image and with disk_config 'AUTO'
    """

    disk_config = 'AUTO'
    volume_backed = False

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServersTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServersTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServersTestJSON, cls).resource_setup()
        validation_resources = cls.get_class_validation_resources(
            cls.os_primary)
        cls.meta = {'hello': 'world'}
        cls.accessIPv4 = '1.1.1.1'
        cls.accessIPv6 = '0000:0000:0000:0000:0000:babe:220.12.22.2'
        cls.name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name=cls.__name__ + '-server')
        cls.password = data_utils.rand_password()
        disk_config = cls.disk_config
        server_initial = cls.create_test_server(
            validatable=True,
            validation_resources=validation_resources,
            wait_until='ACTIVE',
            name=cls.name,
            metadata=cls.meta,
            accessIPv4=cls.accessIPv4,
            accessIPv6=cls.accessIPv6,
            disk_config=disk_config,
            adminPass=cls.password,
            volume_backed=cls.volume_backed)
        cls.server = cls.client.show_server(server_initial['id'])['server']

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('5de47127-9977-400a-936f-abcfbec1218f')
    def test_verify_server_details(self):
        """Verify the specified server attributes are set correctly"""
        self.assertEqual(self.accessIPv4, self.server['accessIPv4'])
        # NOTE(maurosr): See http://tools.ietf.org/html/rfc5952 (section 4)
        # Here we compare directly with the canonicalized format.
        self.assertEqual(self.server['accessIPv6'],
                         str(netaddr.IPAddress(self.accessIPv6)))
        self.assertEqual(self.name, self.server['name'])
        if self.volume_backed:
            # Image is an empty string as per documentation
            self.assertEqual("", self.server['image'])
        else:
            self.assertEqual(self.image_ref, self.server['image']['id'])
        self.assert_flavor_equal(self.flavor_ref, self.server['flavor'])
        self.assertEqual(self.meta, self.server['metadata'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('9a438d88-10c6-4bcd-8b5b-5b6e25e1346f')
    def test_list_servers(self):
        """The created server should be in the list of all servers"""
        body = self.client.list_servers()
        servers = body['servers']
        found = [i for i in servers if i['id'] == self.server['id']]
        self.assertNotEmpty(found)

    @decorators.idempotent_id('585e934c-448e-43c4-acbf-d06a9b899997')
    def test_list_servers_with_detail(self):
        """The created server should be in the detailed list of all servers"""
        body = self.client.list_servers(detail=True)
        servers = body['servers']
        found = [i for i in servers if i['id'] == self.server['id']]
        self.assertNotEmpty(found)

    @decorators.idempotent_id('cbc0f52f-05aa-492b-bdc1-84b575ca294b')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'Instance validation tests are disabled.')
    def test_verify_created_server_vcpus(self):
        """The created server should have the same specification as the flavor

        Verify that the number of vcpus reported by the instance matches
        the amount stated by the flavor
        """
        flavor = self.flavors_client.show_flavor(self.flavor_ref)['flavor']
        validation_resources = self.get_class_validation_resources(
            self.os_primary)
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(self.server, validation_resources),
            self.ssh_user,
            self.password,
            validation_resources['keypair']['private_key'],
            server=self.server,
            servers_client=self.client)
        output = linux_client.exec_command('grep -c ^processor /proc/cpuinfo')
        self.assertEqual(flavor['vcpus'], int(output))

    @decorators.idempotent_id('ac1ad47f-984b-4441-9274-c9079b7a0666')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'Instance validation tests are disabled.')
    def test_host_name_is_same_as_server_name(self):
        """Verify the instance host name is the same as the server name"""
        validation_resources = self.get_class_validation_resources(
            self.os_primary)
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(self.server, validation_resources),
            self.ssh_user,
            self.password,
            validation_resources['keypair']['private_key'],
            server=self.server,
            servers_client=self.client)
        hostname = linux_client.exec_command("hostname").rstrip()
        msg = ('Failed while verifying servername equals hostname. Expected '
               'hostname "%s" but got "%s".' %
               (self.name, hostname.split(".")[0]))
        # NOTE(zhufl): Some images will add postfix for the hostname, e.g.,
        # if hostname is "aaa", postfix ".novalocal" may be added to it, and
        # the hostname will be "aaa.novalocal" then, so we should ignore the
        # postfix when checking whether hostname equals self.name.
        self.assertEqual(self.name.lower(), hostname.split(".")[0], msg)


class ServersTestManualDisk(ServersTestJSON):
    """Test creating server and verifying the server attributes

    This is to create server booted from image and with disk_config 'MANUAL'
    """
    disk_config = 'MANUAL'

    @classmethod
    def skip_checks(cls):
        super(ServersTestManualDisk, cls).skip_checks()
        if not CONF.compute_feature_enabled.disk_config:
            msg = "DiskConfig extension not enabled."
            raise cls.skipException(msg)


class ServersTestBootFromVolume(ServersTestJSON):
    """Test creating server and verifying the server attributes

    This is to create server booted from volume and with disk_config 'AUTO'
    """
    # Run the `ServersTestJSON` tests with a volume backed VM
    volume_backed = True

    @classmethod
    def skip_checks(cls):
        super(ServersTestBootFromVolume, cls).skip_checks()
        if not utils.get_service_list()['volume']:
            msg = "Volume service not enabled."
            raise cls.skipException(msg)


class ServersTestFqdnHostnames(base.BaseV2ComputeTest):
    """Test creating server with FQDN hostname and verifying attributes

    Starting Wallaby release, Nova sanitizes freeform characters in
    server hostname with dashes. This test verifies the same.
    """

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServersTestFqdnHostnames, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServersTestFqdnHostnames, cls).setup_clients()
        cls.client = cls.servers_client

    @decorators.idempotent_id('622066d2-39fc-4c09-9eeb-35903c114a0a')
    @testtools.skipUnless(
        CONF.compute_feature_enabled.hostname_fqdn_sanitization,
        'FQDN hostname sanitization is not supported.')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'Instance validation tests are disabled.')
    def test_create_server_with_fqdn_name(self):
        """Test to create an instance with FQDN type name scheme"""
        validation_resources = self.get_class_validation_resources(
            self.os_primary)
        self.server_name = 'guest-instance-1.domain.com'
        self.password = data_utils.rand_password()
        self.accessIPv4 = '2.2.2.2'
        test_server = self.create_test_server(
            validatable=True,
            validation_resources=validation_resources,
            wait_until='ACTIVE',
            adminPass=self.password,
            name=self.server_name,
            accessIPv4=self.accessIPv4)

        """Verify the hostname within the instance is sanitized

        Freeform characters in the hostname are replaced with dashes
        """
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(test_server, validation_resources),
            self.ssh_user,
            self.password,
            validation_resources['keypair']['private_key'],
            server=test_server,
            servers_client=self.client)
        hostname = linux_client.exec_command("hostname").rstrip()
        self.assertEqual('guest-instance-1-domain-com', hostname)


class ServersV294TestFqdnHostnames(base.BaseV2ComputeTest):
    """Test creating server with FQDN hostname and verifying attributes

    Starting Antelope release, Nova allows to set hostname as an FQDN
    type and allows free form characters in hostname using --hostname
    parameter with API above 2.94 .

    This is to create server with --hostname having FQDN type value having
    more than 64 characters
    """

    min_microversion = '2.94'

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServersV294TestFqdnHostnames, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServersV294TestFqdnHostnames, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServersV294TestFqdnHostnames, cls).resource_setup()
        cls.validation_resources = cls.get_class_validation_resources(
            cls.os_primary)
        cls.accessIPv4 = '1.1.1.1'
        cls.name = 'guest-instance-1'
        cls.password = data_utils.rand_password()
        cls.hostname = 'x' * 52 + '-guest-test.domaintest.com'
        cls.test_server = cls.create_test_server(
            validatable=True,
            validation_resources=cls.validation_resources,
            wait_until='ACTIVE',
            name=cls.name,
            accessIPv4=cls.accessIPv4,
            adminPass=cls.password,
            hostname=cls.hostname)
        cls.server = cls.client.show_server(cls.test_server['id'])['server']

    def verify_metadata_hostname(self, md_json):
        md_dict = json.loads(md_json)
        dhcp_domain = CONF.compute_feature_enabled.dhcp_domain
        if md_dict['hostname'] == f"{self.hostname}{dhcp_domain}":
            return True
        else:
            return False

    @decorators.idempotent_id('e7b05488-f9d5-4fce-91b3-e82216c52017')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'Instance validation tests are disabled.')
    def test_verify_hostname_allows_fqdn(self):
        """Test to verify --hostname allows FQDN type name scheme

        Verify the hostname has FQDN value and Freeform characters
        in the hostname are allowed
        """
        self.assertEqual(
            self.hostname, self.server['OS-EXT-SRV-ATTR:hostname'])
        # Verify that metadata API has correct hostname inside guest
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(self.test_server, self.validation_resources),
            self.ssh_user,
            self.password,
            self.validation_resources['keypair']['private_key'],
            server=self.test_server,
            servers_client=self.client)
        self.verify_metadata_from_api(
            self.test_server, linux_client, self.verify_metadata_hostname)
