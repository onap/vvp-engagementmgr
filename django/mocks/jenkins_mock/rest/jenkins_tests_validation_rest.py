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
from mocks.jenkins_mock.services.jenkins_tests_validation_service \
    import JenkinsTestsResultsSvc
from validationmanager.em_integration import em_client


class JenkinsTestsResultsREST():

    mock_tests_results_svc_obj = JenkinsTestsResultsSvc()

    def post(self, git_repo_url, checklist_uuid):
        response = self.mock_tests_results_svc_obj.\
            retrieve_tests_results_for_cl(
                checklist_uuid)
        em_client.test_finished(response)

    def get(self, eng_manual_id, vf_name):
        log = self.mock_tests_results_svc_obj.retrieve_jenkins_build_log(
            eng_manual_id, vf_name)
        return log
