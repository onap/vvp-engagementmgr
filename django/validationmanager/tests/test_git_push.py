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

from django.conf import settings
from rest_framework.status import HTTP_200_OK

from engagementmanager.models import Vendor, ChecklistSection, Checklist
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import CheckListState, EngagementType, Constants


class TestGitPushSignalCase(TestBaseEntity):

    def childSetup(self):
        token = getattr(settings, 'WEBHOOK_TOKEN', None)
        self.urlStr = "v//hook/git-push" + token
        self.data = dict()
        self.gitRepoURL = "git@example.com:mike/diaspora.git"
        self.fileAdded = "CHANGELOG"
        self.fileModified = "app/controller/application.rb"
#         self.associatedFiles = [self.fileAdded, self.fileModified]
        self.associatedFiles = "[\"" + self.fileAdded + "\",\"" + self.fileModified + "\"]"

        # Create full engagement:
        self.createVendors([Constants.service_provider_company_name, 'Amdocs'])
        self.createDefaultRoles()
        self.el_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"), '55501000199', 'el user', self.el, True)
        self.user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"), '55501000199', 'user', self.standard_user, True)
        self.peer_reviewer = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"), '55501000199', 'peer-reviewer user', self.el, True)
        self.template = self.creator.createDefaultCheckListTemplate()
        self.engagement = self.creator.createEngagement(
            'just-a-fake-uuid', EngagementType.Validation.name, None)  # @UndefinedVariable
        self.engagement.engagement_team.add(self.el_user, self.user)
        self.checklist = self.creator.createCheckList('some-checklist', CheckListState.review.name, 1,
                                                      self.associatedFiles, self.engagement, self.template, self.el_user, self.el_user)  # @UndefinedVariable
        self.section = ChecklistSection.objects.create(uuid=uuid4(), name=self.randomGenerator("randomString"), weight=1.0, description=self.randomGenerator(
            "randomString"), validation_instructions=self.randomGenerator("randomString"), template=self.template)
        self.vendor = Vendor.objects.get(name=Constants.service_provider_company_name)
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"), self.randomGenerator("randomString"))
        self.vf = self.creator.createVF("TestVF-GitPush", self.engagement,
                                        self.deploymentTarget, False, self.vendor, git_repo_url=self.gitRepoURL)

    def initBody(self):  # Create JSON for body REST request.
        self.data['object_kind'] = "push"
        self.data['ref'] = "refs/heads/master"
        projectData = dict()
        projectData['git_ssh_url'] = "git@example.com:mike/diaspora.git"
        projectData['git_http_url'] = "http://example.com/mike/diaspora.git"
        projectData['url'] = self.gitRepoURL
        self.data['project'] = projectData
        commitsList = []
        totalCommits = 0
        for _ in range(2):
            commitsData = dict()
            commitsData['added'] = [self.fileAdded]
            commitsData['modified'] = [self.fileModified]
            commitsData['removed'] = []
            commitsList.append(commitsData)
            for a in commitsData.values():  # Count number of commits in commitsData.
                if a != []:
                    totalCommits += 1
        self.data['commits'] = commitsList
        self.data['total_commits_count'] = totalCommits

    ### TESTS ###
    def test_git_push_event_positive(self):
        if not settings.IS_SIGNAL_ENABLED:
            return
        checklistState = Checklist.objects.get(uuid=self.checklist.uuid)
        print("Checklist state (start): " + checklistState.state)

        self.initBody()
        datajson = json.dumps(self.data, ensure_ascii=False)
        print(datajson)
        headers = {'HTTP_X_GITLAB_EVENT': "Push Hook"}

        response = self.c.post(self.urlStr, datajson, content_type='application/json', **headers)
        print("Got response: " + str(response.status_code) +
              ", Expecting 200. Response body: " + response.reason_phrase)
        self.assertEqual(response.status_code, HTTP_200_OK)

        checklistState = Checklist.objects.get(uuid=self.checklist.uuid)
        print("Checklist state (final, should be 'archive'): " + checklistState.state)
        self.assertEqual(checklistState.state, CheckListState.archive.name)  # @UndefinedVariable
