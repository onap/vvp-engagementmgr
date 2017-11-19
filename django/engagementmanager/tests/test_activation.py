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
from django.utils import timezone

from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants


class ActivateTestCase(TestBaseEntity):

    def childSetup(self):  # Variables to use in this class.
        self.urlStr = self.urlPrefix + "signup/"
        self.createDefaultRoles()
        uuid, vendor = self.creator.createVendor(
            Constants.service_provider_company_name)
        self.activation_token_time = timezone.now()
        self.activation_token_time = self.activation_token_time.replace(
            2012, 1, 2, 13, 48, 25)
        print("This is the time that is going " +
              "to be added to expiredTokenUser: " +
              str(self.activation_token_time))
        self.user = self.creator.createUser(
            vendor,
            self.randomGenerator("email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.standard_user,
            False)
        self.expiredTokenUser = self.creator.createUser(
            vendor,
            self.randomGenerator("email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.standard_user,
            False,
            activation_token_create_time=self.activation_token_time)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.user.uuid))
        print('Full Name: ' + self.user.full_name)
        print('-----------------------------------------------------')
        self.params = '{"company":"' + str(self.user.company) + \
            '","full_name":"' + self.user.full_name + '","email":"' + \
            self.user.email + '","phone_number":"' + \
            self.user.phone_number + \
            '","password":"' + self.user.user.password + \
            '","regular_email_updates":"' + \
            str(self.user.regular_email_updates) + \
            '","is_service_provider_contact":"' + \
            str(self.user.is_service_provider_contact) + '"}'

    def testActivation(self):
        print("\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print(" Test started: user activation")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        for a in range(2):
            print("###############################################")
        print("  Before activation, Current User's activation mode: " +
              str(self.user.user.is_active))
        for a in range(2):
            print("###############################################")
        user_uuid = self.user.uuid
        print(self.urlPrefix + 'activate/' + str(user_uuid) +
              '/' + str(self.user.user.activation_token))
        print("Activating through the activate_user function: " +
              "(simulating a GET request)")
        response = self.c.get(self.urlPrefix + 'activate/' + str(user_uuid) +
                              '/' + str(self.user.user.activation_token))
        print("Response: " + str(response.status_code))
        self.user.refresh_from_db()
        for a in range(5):
            print("******")
        for a in range(2):
            print("###############################################")
        print("   Current User's activation mode: " +
              str(self.user.user.is_active))
        for a in range(2):
            print("###############################################")
        print("Current User's activation mode: " +
              str(self.user.user.is_active))
        if (not self.user.user.is_active):
            for a in range(2):
                print("###############################################")
            print("   User's activation failed: is_active != True..")
            for a in range(2):
                print("###############################################")
        else:
            for a in range(2):
                print("#################################")
            print("         User's is activated        ")
            for a in range(2):
                print("#################################")
        self.printTestName("Test ended")

    def testExpiredTokenActivation(self):
        print("\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print("Negative test started: Expired token activation")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        for a in range(2):
            print("###############################################")
        print("Current User's activation mode: " +
              str(self.user.user.is_active))
        for a in range(2):
            print("###############################################")

        user_uuid = self.expiredTokenUser.uuid
        print("\n\nA user with was pre-initiated with old token " +
              "creation time: 2012-01-02 13:48:25.299000+00:00\n\n")
        self.c.get(
            self.urlPrefix +
            'activate/' +
            str(user_uuid) +
            '/' +
            str(self.expiredTokenUser.user.activation_token))
        self.user.refresh_from_db()
        for a in range(2):
            print("###############################################")
        print("   Current User's activation mode: " +
              str(self.expiredTokenUser.user.is_active))
        for a in range(2):
            print("###############################################")
        print("\n\n")
        if (not self.expiredTokenUser.user.activation_token):
            for a in range(2):
                print("###############################################")
            print("Test Success!")
            for a in range(2):
                print("###############################################")
        else:
            for a in range(2):
                print("###############################################")
            print("Test Failed!")
            for a in range(2):
                print("###############################################")

    def testUnMatchingTokenActivation(self):
        print("\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print("Negative test started: Un-matching token activation test")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        for a in range(2):
            print("###############################################")
        print("Current User's activation mode: " +
              str(self.user.user.is_active))
        for a in range(2):
            print("###############################################")

        print("\n\n Trying to activate a user with an unmatching token")
        self.c.get(
            self.urlPrefix +
            'activate/' +
            str(self.user.uuid) +
            '/' +
            str(self.expiredTokenUser.user.activation_token))
        self.user.refresh_from_db()
        for a in range(2):
            print("###############################################")
        print("   Current User's activation mode: " +
              str(self.expiredTokenUser.user.is_active))
        for a in range(2):
            print("###############################################")
        print("\n\n")
        if (not self.expiredTokenUser.user.activation_token):
            for a in range(2):
                print("###############################################")
            print("Test Success!")
            for a in range(2):
                print("###############################################")
        else:
            for a in range(2):
                print("###############################################")
            print("Test Failed!")
            for a in range(2):
                print("###############################################")
