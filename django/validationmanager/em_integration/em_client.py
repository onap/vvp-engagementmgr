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
"""
Signals sent by ValidationManager

To perform some action when a TestEngine/Jenkins job completes:

    from validationmanager.sig import test_finished
    test_finished.connect(my_test_handler)

To perform some action when new commits are pushed to Gitlab:

    from validationmanager.sig import git_push
    git_push.connect(my_git_push_handler)

Remember that signals are not magically asynchronous or anything. The
webhook call that triggers the signal will not return a response until
all functions listening to these signals return, and they are processed
in sequence. If we end up doing a lot of time-consuming work in response
to webhook notification, we should explore using Celery or some other
background/async task runner instead.

"""

from engagementmanager.vm_integration import em_api


def test_finished(checklist_test_results):
    # A signal that is sent when Jenkins completes running a test job, and
    # notifies us by way of a notification webhook.
    return em_api.test_finished_callback(checklist_test_results)


def git_push(gitlab_data):
    # A signal that is sent when new commits are pushed to Gitlab, which
    # notifies us by way of a notification webhook.
    return em_api.git_push_callback(gitlab_data)
