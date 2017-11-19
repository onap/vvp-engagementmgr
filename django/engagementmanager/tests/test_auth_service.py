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
from engagementmanager.models import Vendor
from engagementmanager.service.authorization_service import \
    AuthorizationService, Permissions
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants
from engagementmanager.utils.request_data_mgr import request_data_mgr


class TestAuthService(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])

        self.createDefaultRoles()

        self.admin_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            Constants.service_provider_admin_mail,
            '55501000199',
            'admin user',
            self.admin,
            True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.admin_user.uuid))
        print('Full Name: ' + self.admin_user.full_name)
        print('-----------------------------------------------------')

        # Create a user with role el
        self.el_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'el user',
            self.el,
            True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.el_user.uuid))
        print('Full Name: ' + self.el_user.full_name)
        print('-----------------------------------------------------')

        self.peer_reviewer = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'peer-reviewer user',
            self.el,
            True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.peer_reviewer.uuid))
        print('Full Name: ' + self.peer_reviewer.full_name)
        print('-----------------------------------------------------')

        # Create another EL
        self.another_el_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'el user2',
            self.el,
            True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.another_el_user.uuid))
        print('Full Name: ' + self.another_el_user.full_name)
        print('-----------------------------------------------------')

        # Create a user with role standard_user
        self.user = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'user', self.standard_user, True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.user.uuid))
        print('Full Name: ' + self.user.full_name)
        print('-----------------------------------------------------')

        # Create a user with role standard_user with SSH key
        self.user_with_ssh = self.creator.createUser(
            Vendor.objects.get(
                name='Other'),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'ssh user',
            self.standard_user,
            True,
            'just-a-fake-ssh-key')
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.user_with_ssh.uuid))
        print('Full Name: ' + self.user_with_ssh.full_name)
        print('-----------------------------------------------------')

        # Create an Engagement with team
        self.engagement = self.creator.createEngagement(
            'just-a-fake-uuid', 'Validation', None)
        self.engagement.engagement_team.add(self.user, self.el_user)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.peer_reviewer
        self.engagement.save()
        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(self.engagement.uuid))
        print('-----------------------------------------------------')

        # Create another Engagement with team with SSH Key
        self.engagement_ssh = self.creator.createEngagement(
            'just-another-fake-uuid', 'Validation', None)
        self.engagement_ssh.engagement_team.add(
            self.user_with_ssh, self.el_user)
        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(self.engagement_ssh.uuid))
        print('-----------------------------------------------------')

        # Create another Engagement with Main Contact
        self.engagement_with_contact = self.creator.createEngagement(
            'yet-just-another-fake-uuid', 'Validation', None)
        self.engagement_with_contact.engagement_team.add(
            self.user_with_ssh, self.el_user)
        self.engagement_with_contact.contact_user = self.user_with_ssh
        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(self.engagement_with_contact.uuid))
        print('-----------------------------------------------------')

        # Create another Engagement with Main Contact
        self.engagement_4_createNS = self.creator.createEngagement(
            'yet-just-another-fake-uuid2', 'Validation', None)
        self.engagement_4_createNS.engagement_team.add(
            self.user_with_ssh, self.el_user)
        self.engagement_4_createNS.contact_user = self.user_with_ssh
        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(self.engagement_4_createNS.uuid))
        print('-----------------------------------------------------')
        self.token = self.loginAndCreateSessionToken(self.user)
        self.sshtoken = self.loginAndCreateSessionToken(self.user_with_ssh)
        self.ELtoken = self.loginAndCreateSessionToken(self.el_user)

        self.checklist_template = self.creator.createDefaultCheckListTemplate()
        print('-----------------------------------------------------')
        print('Created Check List Template')
        print('UUID: ' + str(self.checklist_template.uuid))
        print('-----------------------------------------------------')

        self.checklist = self.creator.createCheckList(
            'some-checklist',
            'Automation',
            1,
            '{}',
            self.engagement,
            self.checklist_template,
            self.el_user,
            self.peer_reviewer)
        print('-----------------------------------------------------')
        print('Created Check List')
        print('UUID: ' + str(self.checklist.uuid))
        print('-----------------------------------------------------')

    def testAuthorization(self):
        auth = AuthorizationService()

        ######################
        # TEST EL PERMISSIONS
        ######################
        # Test Add VF for EL
        auth_result, message = auth.is_user_able_to(
            self.el_user, Permissions.add_vf, str(self.engagement.uuid), '')
        print('ADD_VF Got Result : ' + str(auth_result) + ' ' + message)
        self.assertEquals(auth_result, True)

        auth_result, message = auth.is_user_able_to(
            self.el_user, Permissions.add_vendor, '', '')
        print('ADD_VENDOR Got Result : ' + message)
        self.assertEquals(auth_result, True)

        # Check that EL that belong to ENG can create next step
        auth_result, message = auth.is_user_able_to(
            self.el_user, Permissions.add_nextstep, str(
                self.engagement.uuid), '')
        print('ADD_NEXTSTEP Got Result : ' + message)
        self.assertEquals(auth_result, True)

        # Check that EL that does not belong to ENG cannot create next step
        auth_result, message = auth.is_user_able_to(
            self.another_el_user, Permissions.add_nextstep, str(
                self.engagement.uuid), '')
        print('ADD_NEXTSTEP Got Result : ' + message)
        self.assertEquals(auth_result, False)

        # Check that CL can be created only by EL that belongs to ENG
        auth_result, message = auth.is_user_able_to(
            self.el_user, Permissions.add_checklist, str(
                self.engagement.uuid), '')
        print('ADD_CHECKLIST Got Result : ' + message)
        self.assertEquals(auth_result, True)

        # Check that CL can be created only by EL that belongs to ENG (use
        # another el)
        auth_result, message = auth.is_user_able_to(
            self.another_el_user, Permissions.add_checklist, str(
                self.engagement.uuid), '')
        print('ADD_CHECKLIST Got Result : ' + message)
        self.assertEquals(auth_result, False)

        auth_result, message = auth.is_user_able_to(
            self.user, Permissions.add_checklist, str(
                self.engagement.uuid), '')
        print('ADD_CHECKLIST Got Result : ' + message)
        self.assertEquals(auth_result, False)

        # Check that only peer reviewer can do peer review
        request_data_mgr.set_cl_uuid(str(self.checklist.uuid))
        auth_result, message = auth.is_user_able_to(
            self.peer_reviewer, Permissions.peer_review_checklist, str(
                self.engagement.uuid), str(
                self.checklist.uuid))
        print('PEER_REVIEW_CHECKLIST Got Result : ' + message)
        self.assertEquals(auth_result, True)

        # Check that a user that is not defined as peer review cannot review
        auth_result, message = auth.is_user_able_to(
            self.el_user, Permissions.peer_review_checklist, str(
                self.engagement.uuid), str(
                self.checklist.uuid))
        print('PEER_REVIEW_CHECKLIST Got Result : ' + message)
        self.assertEquals(auth_result, False)

        # Check that only admin which is the cl owner can approve CL
        self.checklist.owner = self.admin_user  # Make admin the owner
        self.checklist.save()
        auth_result, message = auth.is_user_able_to(
            self.admin_user, Permissions.admin_approve_checklist, str(
                self.engagement.uuid), str(
                self.checklist.uuid))
        print('ADMIN_APPROVE_CHECKLIST Got Result : ' + message)
        self.assertEquals(auth_result, True)

        # Check that only admin can approve CL (attempt with regular EL)
        auth_result, message = auth.is_user_able_to(
            self.el_user, Permissions.admin_approve_checklist, str(
                self.engagement.uuid), str(
                self.checklist.uuid))
        print('ADMIN_APPROVE_CHECKLIST Got Result : ' + message)
        self.assertEquals(auth_result, False)

        # Check that only admin can approve CL (attempt with regular user)
        auth_result, message = auth.is_user_able_to(
            self.user, Permissions.admin_approve_checklist, str(
                self.engagement.uuid), str(
                self.checklist.uuid))
        print('ADMIN_APPROVE_CHECKLIST Got Result : ' + message)
        self.assertEquals(auth_result, False)
