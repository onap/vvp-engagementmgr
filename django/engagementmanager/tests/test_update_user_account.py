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
import json

from engagementmanager.models import Vendor, IceUserProfile
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants


class TestUpdateUserAccountTestCase(TestBaseEntity):

    def childSetup(self):

        self.createVendors([Constants.service_provider_company_name, 'Amdocs'])

        self.createDefaultRoles()

        # Create a user with role el
        self.user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), self.randomGenerator("main-vendor-email"),
            '55501000199', 'user', self.standard_user, True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.user.uuid))
        print('Full Name: ' + self.user.full_name)
        print('-----------------------------------------------------')

        self.urlStr = self.urlPrefix + "users/account/"
        self.data = dict()
        self.token = self.loginAndCreateSessionToken(self.user)

    def initBody(self):
        self.data['company'] = Vendor.objects.get(name='Amdocs').name
        self.data['full_name'] = "user"
        self.data['email'] = self.randomGenerator("main-vendor-email")
        self.data['phone_number'] = "12345"
        self.data['password'] = "Aa12345"
        self.data['confirm_password'] = "Aa12345"

    def updateAccount(self, expectedStatus=200, httpMethod="PUT"):
        self.accountData = json.dumps(self.data, ensure_ascii=False)
        if (httpMethod == "PUT"):
            response = self.c.put(self.urlStr, self.accountData, content_type='application/json',
                                  **{'HTTP_AUTHORIZATION': "token " + self.token})
        elif (httpMethod == "POST"):
            response = self.c.post(self.urlStr, self.accountData, content_type='application/json',
                                   **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code) + " Expecting 200")
        self.assertEqual(response.status_code, expectedStatus)
        return response

    ### TESTS ###
    def testUpdateNegativeWrongHttpMethodAccount(self):
        self.initBody()
        print("Negative Test: Wrong HTTP Method --> Expecting status code 405")
        self.updateAccount(405, "POST")

    def testUpdateNegativeDiffPasswords(self):
        self.initBody()
        print("Negative Test: password!=confirm_password --> Expecting status code 400")
        self.data['confirm_password'] = "fakePassword"
        self.updateAccount(400, "PUT")

    def testUpdatePositive(self):
        self.initBody()
        print("Positive Test: --> Expecting status code 200")
        self.updateAccount(200, "PUT")

    def testUpdateUserProfileNotificationsSettings(self):
        self.initBody()

        self.data['regular_email_updates'] = False
        self.data['email_updates_daily_digest'] = True
        self.data['email_updates_on_every_notification'] = False

        print("Positive Test: --> Expecting status code 200")

        self.updateAccount(200, "PUT")

        user = IceUserProfile.objects.get(uuid=self.user.uuid)
        self.assertEqual(user.regular_email_updates, False)
        self.assertEqual(user.email_updates_daily_digest, True)
        self.assertEqual(user.email_updates_on_every_notification, False)