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
from random import randint

from engagementmanager.models import Checklist, ChecklistLineItem
from engagementmanager.utils.constants import MockJenkinsBuildLog


class JenkinsTestsResultsSvc():

    num_of_auto_tests = 2

    def retrieve_tests_results_for_cl(self, checklist_uuid):
        response = dict()
        response['checklist_uuid'] = checklist_uuid
        checklist = Checklist.objects.get(uuid=checklist_uuid)
        line_items = ChecklistLineItem.objects.filter(
            template=checklist.template)[
                :JenkinsTestsResultsSvc().num_of_auto_tests]
        optional_results = ['approved', 'denied']
        optional_text = ['Mock: All required tests passed',
                         'Mock: At least one of the required tests failed']
        response['decisions'] = list()
        for lineitem in line_items:
            # random_result = random.choice(optional_results)
            random_result = optional_results[0]
            # audit_log_text = optional_text[0] if random_result ==
            # optional_results[0] else optional_text[1]
            audit_log_text = optional_text[0]
            response['decisions'].append(
                {
                    'line_item_id': lineitem.uuid,
                    'value': random_result,
                    'audit_log_text': audit_log_text
                }
            )
        return response

    def prepare_log_with_paramaters(self, raw_text, eng_manual_id, vf_name):
        raw_text = raw_text.replace('{vf_name}', vf_name)
        raw_text = raw_text.replace('{eng_man_id}', eng_manual_id)
        return raw_text.replace('{random_id}', str(randint(1, 10**10)))

    def retrieve_jenkins_build_log(self, eng_manual_id, vf_name):
        log = self.prepare_log_with_paramaters(
            MockJenkinsBuildLog.TEXT, eng_manual_id, vf_name)
        return log
