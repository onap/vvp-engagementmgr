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
from uuid import uuid4

from rest_framework import status
from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_200_OK, \
    HTTP_204_NO_CONTENT

from engagementmanager.models import Vendor, NextStep
from engagementmanager.service.nextstep_service import NextStepSvc
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants


class TestNextStepsAPI(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])

        self.createDefaultRoles()

        # Create a user with role el
        self.el_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), self.randomGenerator("main-vendor-email"),
            '55501000199', 'el user', self.el, True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.el_user.uuid))
        print('Full Name: ' + self.el_user.full_name)
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

        # Create a user with role standard_user
        self.pruser = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'peer-reviewer user', self.el, True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.pruser.uuid))
        print('Full Name: ' + self.pruser.full_name)
        print('-----------------------------------------------------')

        # Create a user with role standard_user with SSH key
        self.user_with_ssh = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'ssh user', self.standard_user, True, 'just-a-fake-ssh-key')
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.user_with_ssh.uuid))
        print('Full Name: ' + self.user_with_ssh.full_name)
        print('-----------------------------------------------------')

        # Create an Engagement with team
        self.engagement = self.creator.createEngagement('just-a-fake-uuid', 'Validation', None)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.el_user
        self.engagement.engagement_team.add(self.user, self.el_user)
        self.engagement.save()
        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(self.engagement.uuid))
        print('-----------------------------------------------------')

        # Create another Engagement with team with SSH Key
        self.engagement_ssh = self.creator.createEngagement('just-another-fake-uuid', 'Validation', None)
        self.engagement_ssh.engagement_team.add(self.user_with_ssh, self.el_user)
        self.engagement_ssh.peer_reviewer = self.pruser
        self.engagement_ssh.save()

        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(self.engagement_ssh.uuid))
        print('-----------------------------------------------------')

        # Create another Engagement with Main Contact
        self.engagement_with_contact = self.creator.createEngagement('yet-just-another-fake-uuid', 'Validation', None)
        self.engagement_with_contact.engagement_team.add(self.user, self.el_user)
        self.engagement_with_contact.contact_user = self.user
        self.engagement_with_contact.peer_reviewer = self.pruser
        self.engagement_with_contact.save()

        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(self.engagement_with_contact.uuid))
        print('-----------------------------------------------------')

        # Create another Engagement with Main Contact
        self.engagement_4_createNS = self.creator.createEngagement('yet-just-another-fake-uuid2', 'Validation', None)
        self.engagement_4_createNS.reviewer = self.el_user
        self.engagement_4_createNS.peer_reviewer = self.el_user
        self.engagement_4_createNS.engagement_team.add(self.user_with_ssh, self.el_user)
        self.engagement_4_createNS.contact_user = self.user_with_ssh
        self.engagement_4_createNS.save()

        # Create engagement for order
        self.engagement_4_order = self.creator.createEngagement('yet-just-another-fake-uuid3', 'Validation', None)
        self.engagement_4_order.reviewer = self.el_user
        self.engagement_4_order.peer_reviewer = self.el_user
        self.engagement_4_order.engagement_team.add(self.user_with_ssh, self.el_user)
        self.engagement_4_order.contact_user = self.user_with_ssh
        self.engagement_4_order.save()

        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"), self.randomGenerator("randomString"))
        self.vendor = Vendor.objects.get(name='Other')
        self.vf = self.creator.createVF(self.randomGenerator("randomString"),
                                        self.engagement_4_createNS, self.deploymentTarget, False, self.vendor)

        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(self.engagement_4_createNS.uuid))
        print('-----------------------------------------------------')

        self.token = self.loginAndCreateSessionToken(self.user)
        self.sshtoken = self.loginAndCreateSessionToken(self.user_with_ssh)
        self.ELtoken = self.loginAndCreateSessionToken(self.el_user)

    def testCreateDefaultNextStepsAndSetNextStepsState(self):
        urlStr = self.urlPrefix + 'engagements/${uuid}/nextsteps/Intake'
        NextStepSvc().create_default_next_steps(self.user, self.engagement, self.el_user)
        NextStepSvc().create_default_next_steps_for_user(self.user, self.el_user)
        num_of_steps = 3

        response = self.c.get(urlStr.replace('${uuid}', str(self.engagement.uuid)),
                              **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        print("DATA After JSON Parse:" + str(response.content))

#         content = response.content

        print('Test that GET nextsteps was successful')
        self.assertEqual(response.status_code, HTTP_200_OK)

        print('Test that GET nextsteps in Intake state returns 3 items ')
        self.assertEqual(len(response.json()), num_of_steps)

        print('Test First item state is Incomplete: ' + response.json()[0]['state'])
        self.assertEqual(response.json()[0]['state'], 'Incomplete')

        step_uuid = response.json()[0]['uuid']
        urlStr = self.urlPrefix + 'nextsteps/' + step_uuid + '/state'

        print('attempt change state of next step Incomplete->COMPLETED by standard_user. This should succeed...')
        response = self.c.put(urlStr, '{ "state" : "Completed" }',
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

        print('Negative: attempt change state of next step COMPLETED->Incomplete by EL. This should success')
        response = self.c.put(urlStr, '{ "state" : "Incomplete" }',
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def testCreateDefaultNextStepsForUserWithSSHKey(self):
        urlStr = self.urlPrefix + 'engagements/${uuid}/nextsteps/Intake'
        NextStepSvc().create_default_next_steps(self.user_with_ssh, self.engagement_ssh, self.el_user)
        # Would not create any next step, due to the reason that the user already has an SSH
        NextStepSvc().create_default_next_steps_for_user(self.user_with_ssh, self.el_user)
        num_of_steps = 2

        response = self.c.get(urlStr.replace('${uuid}', str(self.engagement_ssh.uuid)),
                              **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        print("DATA After JSON Parse:" + str(response.content))

        print('Test that GET nextsteps was successful')
        self.assertEqual(response.status_code, HTTP_200_OK)

        print('Test that GET nextsteps in Intake state returns 3 items ')
        self.assertEqual(len(response.json()), num_of_steps)

    def testOrderNextSteps(self):

        nsDict = {}
        nsDict["position"] = 4
        nsDict["creator_uuid"] = str(self.el_user.uuid)
        nsDict[
            "description"] = "Please submit the first version of the VF package. If you have any problems or questions please contact your Engagement Lead (EL)"
        nsDict["state"] = "Incomplete"
        nsDict["engagement_stage"] = "Active"

        myjson = json.dumps([nsDict], ensure_ascii=False)

        create_nextsteps_url = self.urlPrefix + "engagements/" + str(self.engagement_4_order.uuid) + "/nextsteps/"
        response = self.c.post(create_nextsteps_url, myjson, content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        response = self.c.post(create_nextsteps_url, myjson, content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        response = self.c.post(create_nextsteps_url, myjson, content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})

        get_nextsteps_url = self.urlPrefix + 'engagements/${uuid}/nextsteps/Intake'
        response = self.c.get(get_nextsteps_url.replace('${uuid}', str(
            self.engagement_4_order.uuid)), **{'HTTP_AUTHORIZATION': "token " + self.sshtoken})

        decoded_ns = json.loads(response.content)
        myjson = json.dumps(decoded_ns, ensure_ascii=False)
        order_nextsteps_url = self.urlPrefix + 'engagements/' + \
            str(self.engagement_4_order.uuid) + '/nextsteps/order_next_steps/'
        response = self.c.put(order_nextsteps_url, myjson, content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})

        response = self.c.get(get_nextsteps_url.replace('${uuid}', str(
            self.engagement_4_order.uuid)), **{'HTTP_AUTHORIZATION': "token " + self.sshtoken})

        decoded_ns = json.loads(response.content)
        counter = 0
        for next_step in decoded_ns:
            self.assertEqual(next_step['position'], counter)
            counter += 1

    def testCreateDefaultNextStepsWhenENGContactExist(self):
        urlStr = self.urlPrefix + 'engagements/${uuid}/nextsteps/Intake'
        NextStepSvc().create_default_next_steps(self.user, self.engagement_with_contact, self.el_user)
        NextStepSvc().create_default_next_steps_for_user(self.user, self.el_user)
        num_of_steps = 2

        response = self.c.get(urlStr.replace('${uuid}', str(
            self.engagement_with_contact.uuid)), **{'HTTP_AUTHORIZATION': "token " + self.token})

        print('Got response : ' + str(response.status_code))
        print("DATA After JSON Parse:" + str(response.content))

        print('Test that GET nextsteps was successful')
        self.assertEqual(response.status_code, HTTP_200_OK)

        print('Test that GET nextsteps in Intake state returns 3 items ')
        self.assertEqual(len(response.json()), num_of_steps)

    def testAddNextStepToEng(self):
        urlStr = self.urlPrefix + "engagements/" + str(self.engagement_4_createNS.uuid) + "/nextsteps/"

        NextStepSvc().create_default_next_steps(self.user_with_ssh, self.engagement_4_createNS, self.el_user)
        # Would not create any next step, due to the reason that the user already has an SSH
        NextStepSvc().create_default_next_steps_for_user(self.user_with_ssh, self.el_user)

        nsDict = {}
        nsDict["position"] = "4"
        nsDict["creator_uuid"] = str(self.el_user.uuid)
        nsDict[
            "description"] = "Please submit the first version of the VF package. If you have any problems or questions please contact your Engagement Lead (EL)"
        nsDict["state"] = "Incomplete"
        nsDict["engagement_stage"] = "Active"

        myjson = json.dumps([nsDict], ensure_ascii=False)
        print(myjson)

        response = self.c.post(urlStr, myjson, content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        print('Got response : ' + str(response.status_code))
        print("DATA After JSON Parse:" + str(response.content))

        self.assertEqual(response.status_code, HTTP_200_OK)

    def testDelNextStepToEng(self):
        nsObj = NextStep.objects.create(uuid=uuid4(), creator=self.el_user, position=2, description="testDelNextStepToEng",
                                        state='Incomplete', engagement_stage="Intake", engagement=self.engagement)
        urlStr = self.urlPrefix + "nextsteps/" + str(nsObj.uuid)

        response = self.c.delete(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        print('Got response : ' + str(response.status_code))
        print("DATA After JSON Parse:" + str(response.content))

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

    def testNegativeDelNextStepToEngNoHeader(self):
        nsObj = NextStep.objects.create(uuid=uuid4(), creator=self.el_user, position=2, description="testDelNextStepToEng",
                                        state='Incomplete', engagement_stage="Intake", engagement=self.engagement)
        urlStr = self.urlPrefix + "nextsteps/" + str(nsObj.uuid)

        response = self.c.delete(urlStr)
        print('Negative: Expecting response 403, got: ' + str(response.status_code))
        print("DATA After JSON Parse:" + str(response.content))

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def testEditNextSteps(self):
        print(
            '---------------------------------- testEditNextSteps, Expecting 200 ------------------------------------')
        print('---------------------------------- Creating a next step ------------------------------------')
        step = NextStep.objects.create(position="4", creator=self.el_user, engagement=self.engagement,
                                       description="Please submit the first version of the VF package. If you have any problems or questions please contact your Engagement Lead (EL)",
                                       state="TODO", engagement_stage="Active",
                                       uuid=uuid4())
        print('---------------------------------- Editing the next step ------------------------------------')
        urlStr = self.urlPrefix + "nextsteps/" + str(step.uuid)
        body = {}
        files = []
        for i in range(4):
            files.append(self.randomGenerator('randomString'))
        body['files'] = files
        body['duedate'] = "2012-01-03"
        body['description'] = self.randomGenerator('randomString')
        body['assigneesUuids'] = [str(self.user.uuid), str(self.el_user.uuid)]
        myjson = json.dumps(body, ensure_ascii=False)
        print(myjson)
        response = self.c.put(urlStr, myjson, content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        print(urlStr)
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testUserNextSteps(self):
        NextStepSvc().create_default_next_steps(self.user_with_ssh, self.engagement_4_createNS, self.el_user)
        # Needs to return 0 elements for regular user which is not the assignee:
        urlStr = self.urlPrefix + 'engagements/user/nextsteps/'
        response = self.c.get(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.sshtoken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = json.loads(response.content)
        self.assertEqual(data["data"], [])
        self.assertEqual(data["count"], 0)

        # Needs to return 3 elements to el user which is the assignee:
        response = self.c.get(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data["count"], 3)
