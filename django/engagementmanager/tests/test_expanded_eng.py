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
import random
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.models import Vendor, VF
from engagementmanager.utils.constants import Constants, EngagementStage
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class testGetExpandedEngsAndSearch(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])

        self.createDefaultRoles()
        # Create a user with role el
        vendor = Vendor.objects.get(
            name=Constants.service_provider_company_name)
        self.el_user = self.creator.createUser(
            vendor,
            self.randomGenerator("main-vendor-email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.el,
            True)
        self.peer_reviewer = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'peer-reviewer user', self.el, True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.el_user.uuid))
        print('Full Name: ' + self.el_user.full_name)
        print('-----------------------------------------------------')

        # Create a user with role standard_user
        self.vendor = Vendor.objects.get(name='Other')
        self.user = self.creator.createUser(
            self.vendor,
            "Johnny@d2ice.com",
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.standard_user,
            True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.user.uuid))
        print('Full Name: ' + self.user.full_name)
        print('-----------------------------------------------------')
        self.service_provider = Vendor.objects.get(
            name=Constants.service_provider_company_name)
        self.peer_reviewer = self.creator.createUser(
            self.service_provider,
            self.randomGenerator("main-vendor-email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.el,
            True)
        logger.debug('-----------------------------------------------------')
        logger.debug('Created Peer Reviewer:')
        logger.debug('UUID: ' + str(self.peer_reviewer.uuid))
        logger.debug('Full Name: ' + self.peer_reviewer.full_name)
        logger.debug('-----------------------------------------------------')

        # Create an Engagement with team
        engStageList = [
            EngagementStage.Intake.name,
            EngagementStage.Active.name,
            EngagementStage.Validated.name,
            EngagementStage.Completed.name]  # @UndefinedVariable
        self.random_stage = engStageList[(random.randint(0, 3) * 2 + 1) % 4]
        self.names_array = list()
        for i in range(0, 14):
            self.engagement = self.creator.createEngagement(
                self.randomGenerator(
                    "randomString"),
                self.randomGenerator("randomString"), None)
            self.engagement.reviewer = self.el_user
            self.engagement.peer_reviewer = self.peer_reviewer
            self.engagement.engagement_manual_id = self.randomGenerator(
                "randomString")
            self.engagement.engagement_team.add(
                self.el_user, self.peer_reviewer)
            self.engagement.engagement_stage = engStageList[(
                random.randint(0, 3) * 2 + 1) % 4]
            self.engagement.save()
            print('-----------------------------------------------------')
            print('Created Engagement:')
            print('UUID: ' + str(self.engagement.uuid))
            print('-----------------------------------------------------')
            self.names_array.append(self.engagement.engagement_manual_id)
            # Create a VF
            self.deploymentTarget = self.creator.createDeploymentTarget(
                self.randomGenerator("randomString"),
                self.randomGenerator("randomString"))
            self.vf = self.creator.createVF(
                "vf_" + str(i),
                self.engagement,
                self.deploymentTarget,
                False,
                vendor)
            self.vf.save()
            self.names_array.append(self.vf.name)
            print('-----------------------------------------------------')
            print('Created VF:')
            print('UUID: ' + str(self.vf.uuid))
            print('-----------------------------------------------------')
            if (i % 2 == 0):
                self.engagement.engagement_team.add(self.user)
                vfc = self.creator.createVFC(
                    "vfc_" + str(i),
                    self.randomGenerator("randomNumber"),
                    self.vendor,
                    self.vf,
                    self.el_user)
                self.names_array.append(vfc.name)
                self.engagement.save()

        self.random_keyword = self.names_array[(
            random.randint(0, len(self.names_array) - 1))]
        self.token = self.loginAndCreateSessionToken(self.user)

    def loggerTestFailedOrSucceded(self, bool_flag):
        if bool_flag:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug(" Test Succeeded")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        else:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug("Test failed")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

    def test_get_expanded_even_numbered_engs_by_standard_user_no_keyword(self):
        urlStr = self.urlPrefix + 'engagement/expanded/'
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(
            " Test started: test_get_expanded_even_numbered_\
            engs_by_standard_user_no_keyword")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        postData = {'stage': 'All', 'keyword': '', 'offset': 0, 'limit': 15}
        datajson = json.dumps(postData, ensure_ascii=False)
        response = self.c.post(urlStr,
                               datajson,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.token})
        status = response.status_code
        logger.debug("Got response : " + str(status))
        if (status != 200):
            logger.error("Got response : " + str(status) +
                         " , wrong http response returned ")
            self.assertEqual(response.status_code, 200)
        logger.debug("Got content : " + str(response.content))
        data = json.loads(response.content)
        if (data['num_of_objects'] != 7):
            self.loggerTestFailedOrSucceded(False)
            logger.error(
                "num of objects returned from server != 7 (all even numbers)")
            self.assertEqual(data['num_of_objects'], 7)
        for x in data['array']:
            shortened_name = x['vf__name'].split('_')
            if (int(shortened_name[1]) % 2 != 0):
                self.loggerTestFailedOrSucceded(False)
                logger.error("Odd VF name returned")
                self.assertEqual(int(shortened_name[1]) % 2, 0)
        self.loggerTestFailedOrSucceded(True)

    def test_get_expanded_engs_with_filter_no_keyword(self):
        urlStr = self.urlPrefix + 'engagement/expanded/'
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(
            " Test started: test_get_expanded_engs_with_filter_no_keyword")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        postData = {'stage': self.random_stage,
                    'keyword': '', 'offset': 0, 'limit': 15}
        datajson = json.dumps(postData, ensure_ascii=False)
        response = self.c.post(urlStr,
                               datajson,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.token})
        status = response.status_code
        logger.debug("Got response : " + str(status))
        if (status != 200):
            logger.error("Got response : " + str(status) +
                         " , wrong http response returned ")
            self.assertEqual(response.status_code, 200)
        logger.debug("Got content : " + str(response.content))
        data = json.loads(response.content)
        print("random stage chosen: " + self.random_stage)
        for x in data['array']:
            print("engagement's stage: " + x['engagement__engagement_stage'])
            if (x['engagement__engagement_stage'] != self.random_stage):
                self.loggerTestFailedOrSucceded(False)
                logger.error(
                    "VF With different stage than \
                    defined filter was retrieved")
                self.assertEqual(
                    x['engagement__engagement_stage'], self.random_stage)
        self.loggerTestFailedOrSucceded(True)

    def test_get_expanded_engs_with_keyword_nofilter(self):
        urlStr = self.urlPrefix + 'engagement/expanded/'
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(
            " Test started: test_get_expanded_engs_with_filter_no_keyword")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        postData = {'stage': 'All', 'keyword': self.random_keyword,
                    'offset': 0, 'limit': 15}
        datajson = json.dumps(postData, ensure_ascii=False)
        response = self.c.post(
            urlStr,
            datajson,
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.token})
        status = response.status_code
        logger.debug("Got response : " + str(status))
        self.assertEqual(response.status_code, 200)
        logger.debug("Got content : " + str(response.content))
        data = json.loads(response.content)
        print("random keyword chosen: " + self.random_keyword)
        for x in data['array']:
            bool_flag = False
            if (
                x['engagement__engagement_manual_id'] != self.random_keyword
                    and x['vf__name'] != self.random_keyword):
                vf = VF.objects.get(engagement__uuid=x['engagement__uuid'])
                urlStr = self.urlPrefix + 'vf/' + str(vf.uuid) + '/vfcs/'
                vfc_of_x_response = self.c.get(
                    urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
                vfc_list = json.loads(vfc_of_x_response.content)
                for vfc in vfc_list:
                    if vfc['name'] == self.random_keyword:
                        bool_flag = True
                        break
                    else:
                        continue
            else:
                bool_flag = True
            if (not bool_flag):
                self.loggerTestFailedOrSucceded(False)
                logger.error(
                    "VF With different stage than filter was retrieved")
                self.assertEqual(
                    x['engagement__engagement_stage'], self.random_stage)
        self.loggerTestFailedOrSucceded(True)

    def test_get_expanded_engs_with_keyword_and_filter(self):
        urlStr = self.urlPrefix + 'engagement/expanded/'
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(
            " Test started: test_get_expanded_engs_with_filter_no_keyword")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        postData = {'stage': self.random_stage,
                    'keyword': self.random_keyword, 'offset': 0, 'limit': 15}
        datajson = json.dumps(postData, ensure_ascii=False)
        response = self.c.post(urlStr,
                               datajson,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.token})
        status = response.status_code
        logger.debug("Got response : " + str(status))
        if (status != 200):
            logger.error("Got response : " + str(status) +
                         " , wrong http response returned ")
            self.assertEqual(response.status_code, 200)
        logger.debug("Got content : " + str(response.content))
        data = json.loads(response.content)
        print("random keyword chosen: " + self.random_keyword)
        for x in data['array']:
            bool_flag = False
            if (x['engagement__engagement_stage'] != self.random_stage):
                self.loggerTestFailedOrSucceded(False)
                logger.error(
                    "VF With different stage than \
                    defined filter was retrieved")
                self.assertEqual(
                    x['engagement__engagement_stage'], self.random_stage)
            if (
                x['engagement__engagement_manual_id'] != self.random_keyword
                    and x['vf__name'] != self.random_keyword):
                vf = VF.objects.get(engagement__uuid=x['engagement__uuid'])
                urlStr = self.urlPrefix + 'vf' + str(vf.uuid) + '/vfcs/'
                vfc_of_x_response = self.c.get(
                    urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
                vfc_list = json.loads(vfc_of_x_response.content)
                for vfc in vfc_list:
                    if (vfc['name'] == self.random_keyword):
                        bool_flag = True
                        break
                    else:
                        continue
            else:
                bool_flag = True
            if (not bool_flag):
                self.loggerTestFailedOrSucceded(False)
                logger.error(
                    "VF With different stage than filter was retrieved")
                self.assertEqual(
                    x['engagement__engagement_stage'], self.random_stage)
        self.loggerTestFailedOrSucceded(True)

    def test_get_expanded_engs_with_keyword_email(self):
        urlStr = self.urlPrefix + 'engagement/expanded/'
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(
            " Test started: test_get_expanded_engs_with_filter_no_keyword")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        email_test = "Johnny@d2ice.com"
        postData = {'stage': 'All', 'keyword': email_test,
                    'offset': 0, 'limit': 15}
        datajson = json.dumps(postData, ensure_ascii=False)
        response = self.c.post(urlStr,
                               datajson,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.token})
        status = response.status_code
        logger.debug("Got response : " + str(status))
        self.assertEqual(response.status_code, 200)
        logger.debug("Got content : " + str(response.content))
        data = json.loads(response.content)
        print("random keyword chosen: " + email_test)
        if data['num_of_objects'] >= 1:
            for vf_record in data['array']:
                vf = VF.objects.get(
                    engagement__uuid=vf_record['engagement__uuid'])
                if (not vf.engagement.engagement_team.filter(
                        uuid=self.user.uuid).exists()):
                    self.loggerTestFailedOrSucceded(False)
                    logger.error(
                        "VF With different stage than filter was retrieved")
                self.loggerTestFailedOrSucceded(True)
        else:
            self.loggerTestFailedOrSucceded(False)
