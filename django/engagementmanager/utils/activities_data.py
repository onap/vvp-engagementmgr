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
from engagementmanager.utils.constants import ActivityType


class ActivityData:
    def __init__(self, engagement, activity_type, owner=None):
        self.engagement = engagement
        self.description = ''
        self.metadata = {}
        self.activity_type = activity_type
        self.is_notification = False
        self.owner = owner
        self.multiple_users_as_owners = False
        self.user = None


class UserJoinedEngagementActivityData(ActivityData):
    def __init__(self, vf, users_list, engagement, owner=None):
        super(UserJoinedEngagementActivityData, self).__init__(engagement, ActivityType.user_joined_eng, owner)
        self.vf = vf
        self.users_list = users_list


class VFProvisioningActivityData(ActivityData):
    def __init__(self, vf, users_list, engagement, description="There was an error provisioning the VF", owner=None):
        super(VFProvisioningActivityData, self).__init__(engagement, ActivityType.vf_provisioning_event, owner)
        self.vf = vf
        self.description = description
        self.users_list = users_list


class TestFinishedActivityData(ActivityData):
    def __init__(self, users_list, engagement, description="There was an error in Test"
                                                           " Finished signal from Jenkins", owner=None):
        super(TestFinishedActivityData, self).__init__(engagement, ActivityType.test_finished_event, owner)
        self.description = description
        self.users_list = users_list


class ChangeEngagementStageActivityData(ActivityData):
    def __init__(self, vf, stage, engagement, owner=None):
        super(ChangeEngagementStageActivityData, self).__init__(engagement, ActivityType.change_engagement_stage, owner)
        self.vf = vf
        self.stage = stage


class AddNextStepsActivityData(ActivityData):
    def __init__(self, vf, user, engagement, owner=None):
        super(AddNextStepsActivityData, self).__init__(engagement, ActivityType.add_next_steps, owner)
        self.vf = vf
        self.user = user


class NoticeEmptyEngagementData(ActivityData):
    def __init__(self, vf_name, max_empty_time, git_repo_url, delta_days_from_creation, engagement, owner=None):
        super(NoticeEmptyEngagementData, self).__init__(engagement, ActivityType.notice_empty_engagement, owner)
        self.max_empty_time = max_empty_time
        self.vf_name = vf_name
        self.git_repo_url = git_repo_url
        self.delta_days_from_creation = delta_days_from_creation


class UpdateNextStepsActivityData(ActivityData):
    def __init__(self, update_type, user, engagement, owner=None):
        super(UpdateNextStepsActivityData, self).__init__(engagement, ActivityType.update_next_steps, owner)
        self.update_type = update_type
        self.user = user


class DeleteNextStepsActivityData(ActivityData):
    def __init__(self, user, engagement, owner=None):
        super(DeleteNextStepsActivityData, self).__init__(engagement, ActivityType.delete_next_steps, owner)
        self.user = user


class SSHKeyAddedActivityData(ActivityData):
    def __init__(self, action, engagement, owner=None):
        super(SSHKeyAddedActivityData, self).__init__(engagement, ActivityType.ssh_key_added, owner)
        self.action = action
