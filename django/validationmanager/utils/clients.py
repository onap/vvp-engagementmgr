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
"""validationmanager.utils.clients

We provide accessor methods that instantiate gitlab and Jenkins clients
with appropriate authentication information.

This way, the gitlab and Jenkins client code (copied from simci) may
remain general-purpose and perhaps extracted into a separate library
later, while modules using this code need not concern themselves with
authentication information.

"""
from django.conf import settings

from validationmanager.git.gitlab_client import GitlabClient
from validationmanager.jenkins.jenkins_client import JenkinsClient


def get_jenkins_client():
    return JenkinsClient(
        settings.JENKINS_URL,
        settings.JENKINS_USERNAME,
        settings.JENKINS_PASSWORD,
    )


def get_gitlab_client():
    return GitlabClient(settings.GITLAB_URL, settings.GITLAB_TOKEN)
