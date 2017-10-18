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
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from engagementmanager.models import Vendor, IceUserProfile
from engagementmanager.utils.constants import Constants


class TestInviteMembersTestCase(TestBaseEntity):

    def createEng(self, name):
        # Create an Engagement with team
        engagement = self.creator.createEngagement(name, 'Validation', None)
        engagement.reviewer = self.reviewer
        engagement.peer_reviewer = self.reviewer
        engagement.save()
        engagement.engagement_team.add(self.inviter, self.el_user)
        self.engList.append(engagement)
        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(engagement.uuid))
        print('-----------------------------------------------------')

    def childSetup(self):

        self.createVendors([Constants.service_provider_company_name, 'Other'])

        self.createDefaultRoles()
        self.engList = []
        self.vfList = []

        # Create a user with role el
        self.el_user_email = self.randomGenerator("main-vendor-email")
        self.el_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name),
            self.el_user_email, '55501000199', 'el user', self.el, True)
        self.inviter = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'inviter user', self.standard_user, True)
        self.reviewer = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'reviewer user', self.standard_user, True)

        self.createEng('123456789')
        self.createEng('abcdefghi')

        # Create a VF
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"), self.randomGenerator("randomString"))

        for eng in self.engList:
            vf = self.creator.createVF(self.randomGenerator("randomString"), eng,
                                       self.deploymentTarget, False, Vendor.objects.get(name='Other'))
            self.vfList.append(vf)

        self.urlStr = self.urlPrefix + "invite-team-members/"
        self.data = dict()
        self.data2 = dict()
        self.token = self.loginAndCreateSessionToken(self.inviter)

    def initBody(self):
        self.invitedData = []

        self.data['email'] = self.randomGenerator("main-vendor-email")
        self.data['eng_uuid'] = str(self.engList[0].uuid)
        self.invitedData.append(self.data)

        self.data2['email'] = self.el_user_email
        self.data2['eng_uuid'] = str(self.engList[0].uuid)
        self.invitedData.append(self.data2)

    def inviteContact(self, expectedStatus=HTTP_200_OK):
        self.invitedDataStr = json.dumps(self.invitedData, ensure_ascii=False)
        response = self.c.post(self.urlStr, self.invitedDataStr, content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code), str(response.content))
        self.assertEqual(response.status_code, expectedStatus)
        return response

    def createContactUser(self):
        self.contact = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), self.data['email'], self.data['phone_number'], self.data['full_name'], self.standard_user, True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.contact.uuid))
        print('Full Name: ' + self.contact.full_name)
        print('-----------------------------------------------------')

    ### TESTS ###
    def testAddContactForNonExistingContact(self):
        self.initBody()
        self.inviteContact()

    def testThrotellingInviteSameEmailSameEng(self):
        self.invitedData = []

        self.data['email'] = self.el_user_email
        self.data['eng_uuid'] = str(self.engList[0].uuid)
        self.invitedData.append(self.data)

        self.data2['email'] = self.el_user_email
        self.data2['eng_uuid'] = str(self.engList[0].uuid)
        self.invitedData.append(self.data2)

        self.inviteContact(expectedStatus=HTTP_400_BAD_REQUEST)

    def testThrotellingInviteMoreThan5EmailsToSameEng(self):
        self.invitedData = []

        for i in range(0, 30):
            data = dict()
            data['email'] = self.randomGenerator("main-vendor-email")
            data['eng_uuid'] = str(self.engList[0].uuid)
            self.invitedData.append(data)

        self.inviteContact(expectedStatus=HTTP_400_BAD_REQUEST)

    def testMultipleInvitationsForSameUserDiffEng(self):
        for i in range(0, 2):
            data = dict()
            data['email'] = self.el_user_email
            data['eng_uuid'] = str(self.engList[i].uuid)
            self.invitedData = []
            self.invitedData.append(data)
            self.inviteContact(expectedStatus=HTTP_200_OK)
            invitedUser = IceUserProfile.objects.get(email=data['email'])
            self.assertTrue(invitedUser in self.engList[i].engagement_team.all())
