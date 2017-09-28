#  
# ============LICENSE_START========================================== 
# org.onap.vvp/engagementmgr
# ===================================================================
# Copyright © 2017 AT&T Intellectual Property. All rights reserved.
# ===================================================================
#
# Unless otherwise specified, all software contained herein is licensed
# under the Apache License, Version 2.0 (the “License”);
# you may not use this software except in compliance with the License.
# You may obtain a copy of the License at
#
#             http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
#
# Unless otherwise specified, all documentation contained herein is licensed
# under the Creative Commons License, Attribution 4.0 Intl. (the “License”);
# you may not use this documentation except in compliance with the License.
# You may obtain a copy of the License at
#
#             https://creativecommons.org/licenses/by/4.0/
#
# Unless required by applicable law or agreed to in writing, documentation
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ============LICENSE_END============================================
#
# ECOMP is a trademark and service mark of AT&T Intellectual Property.
from engagementmanager.tests.test_base_entity import TestBaseEntity
import json
from boto.s3.connection import S3Connection, OrdinaryCallingFormat
from django.conf import settings
from wheel.signatures import assertTrue
from django.utils import timezone
from engagementmanager.utils.constants import Constants
from engagementmanager.vm_integration import vm_client
from validationmanager.rados.rgwa_client import RGWAClient
from validationmanager.tests.test_rgwa_client_factory import TestRGWAClientFactory


class ActivateTestCase(TestBaseEntity):

    def childSetup(self):  # Variables to use in this class.
        self.s3_host = '10.252.0.21'  # settings.AWS_S3_HOST
        self.s3_port = 8080  # settings.AWS_S3_PORT

        self.urlStr = self.urlPrefix + "signup/"
        self.createDefaultRoles()
        uuid, vendor = self.creator.createVendor(Constants.service_provider_company_name)
        self.activation_token_time = timezone.now()
        self.activation_token_time = self.activation_token_time.replace(
            2012, 1, 2, 13, 48, 25)
        print("This is the time that is going to be added to expiredTokenUser: " +
              str(self.activation_token_time))
        self.user = self.creator.createUser(vendor, self.randomGenerator("email"), self.randomGenerator(
            "randomNumber"), self.randomGenerator("randomString"), self.standard_user, True)
        self.new_user = self.creator.createUser(vendor, self.randomGenerator("email"), self.randomGenerator(
            "randomNumber"), self.randomGenerator("randomString"), self.standard_user, True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.user.uuid))
        print('Full Name: ' + self.user.full_name)
        print('-----------------------------------------------------')
        self.params = '{"company":"' + str(self.user.company) + '","full_name":"' + self.user.full_name + '","email":"' + self.user.email + '","phone_number":"' + self.user.phone_number + \
            '","password":"' + self.user.user.password + '","regular_email_updates":"' + \
            str(self.user.regular_email_updates) + \
            '","is_service_provider_contact":"' + str(self.user.is_service_provider_contact) + '"}'
        self.userToken = self.loginAndCreateSessionToken(self.user)
        self.new_user_token = self.loginAndCreateSessionToken(self.new_user)

    def test_validate_rgwauser_created_after_Activation(self):
        if settings.IS_SIGNAL_ENABLED:
            vm_client.fire_event_in_bg(
                'send_create_user_in_rgwa_event', self.user)
            rgwa = TestRGWAClientFactory.admin()
            rgwa_user = rgwa.get_user(self.user.full_name)
            if rgwa_user is None:
                print("Test Failed!")
            else:
                access_key = rgwa_user['access_key']
                print("######access_key#################= ", access_key)
                secret_key = rgwa_user['secret_key']
                print("######secret_key#################= ", secret_key)
                self.assertTrue(access_key and secret_key != None)
                print("#################################")
                print("Test PASS!")
                self.printTestName("Test ended")


# Whenever a new user is configured, we should create a RadosGW user for them.
# If unspecified, the access keys are generated on the server and returned here
# in the response.
    def testCreateAndGetRgwaUser(self):
        if settings.IS_SIGNAL_ENABLED:
            base_url = 'http://{S3_HOST}:{S3_PORT}/admin'.format(
                S3_HOST=self.s3_host,  # settings.AWS_S3_HOST,
                S3_PORT=self.s3_port,  # settings.AWS_S3_PORT,
            )
            admin_conn = RGWAClient(base_url)
            print("base_url=" + base_url)
            print("S3_HOST = " + self.s3_host)
            print("s3_port =" + str(self.s3_port))
            print("admin_conn= ", admin_conn)
            username = self.randomGenerator("randomString")
            print("username", username)
            new_user = admin_conn.create_user(
                uid=username, display_name='User "%s"' % username)
            print("new_user = " + str(new_user))
            self.assertTrue(new_user['user_id'] != None)
            get_user = admin_conn.get_user(new_user['user_id'])
            self.assertTrue(new_user['user_id'] == get_user['user_id'])

    def testCreateAndGetRgwaBucket(self):
        if settings.IS_SIGNAL_ENABLED:
            s3aws_access_key_id = settings.AWS_ACCESS_KEY_ID
            s3aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
            print("s3aws_access_key_id=" + s3aws_access_key_id)
            print("s3aws_secret_access_key=" + s3aws_secret_access_key)
            print("S3_HOST = " + self.s3_host)
            print("s3_port =" + str(self.s3_port))

            boto_conn = S3Connection(host=self.s3_host,
                                     port=self.s3_port,
                                     aws_access_key_id=s3aws_access_key_id,
                                     aws_secret_access_key=s3aws_secret_access_key,
                                     calling_format=OrdinaryCallingFormat(),
                                     is_secure=False,
                                     )
            boto_conn.num_retries = 0
            bucketname = self.randomGenerator("randomString").lower()
            new_bucket = boto_conn.create_bucket(bucketname)
            assertTrue(new_bucket != None)
            print("new_bucket = " + str(new_bucket))
            bucket = boto_conn.get_bucket(bucketname)
            print("bucket = " + str(bucket))
            bucket_acl = bucket.get_acl()
            print("bucket_acl = " + str(bucket_acl))

    def testGetSecretKey(self):
        vm_client.send_create_user_in_rgwa_event(self.user)
        urlStr = self.urlPrefix + 'users/account/rgwa/'
        print("urlStr of get secret key",urlStr)
        self.printTestName("testGetSecretKey [Start]")
        response = self.c.get(urlStr, data={}, content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.userToken})
        print('Got response : ' + str(response.status_code))
        dict_response = json.loads(response.content)
        print("api response",dict_response)
        self.assertTrue(dict_response["rgwa_secret_key"] is not None)
        self.printTestName("testGetSecretKey [End]")

    def testNegativeGetSecretKeyInvalidToken(self):
        vm_client.send_create_user_in_rgwa_event(self.user)
        urlStr = self.urlPrefix + 'users/account/rgwa/'
        print("urlStr of get secret key",urlStr)
        self.printTestName("testGetSecretKey [Start]")
        response = self.c.get(urlStr, data={}, content_type='application/json',
                              **{'HTTP_AUTHORIZATION': 'token' + self.new_user_token})
        print('Got response : ' + str(response.status_code))
        dict_response = json.loads(response.content)
        print("api response",dict_response)
        self.assertTrue(dict_response[
                        "detail"] == 'You must authenticate in order to ' +
                        'perform this action: Authentication credentials were not provided.')
        self.printTestName("testGetSecretKey [End]")
