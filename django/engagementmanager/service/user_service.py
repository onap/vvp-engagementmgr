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
from django.contrib.auth import get_user_model
from sshpubkeys import SSHKey

from engagementmanager.apps import bus_service
from engagementmanager.bus.messages.activity_event_message\
    import ActivityEventMessage
from engagementmanager.models import IceUserProfile, Role, VF
from engagementmanager.serializers import\
    SuperThinIceUserProfileModelSerializerForSignals
from engagementmanager.service.base_service import BaseSvc
from engagementmanager.utils.cryptography import CryptographyText
from engagementmanager.utils.activities_data import SSHKeyAddedActivityData
from engagementmanager.utils.vvp_exceptions import VvpBadRequest
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.views_helper import checkAndModifyIfSSHNextStepExist, \
    getFirstEngByUser, addUsersToEngTeam
from engagementmanager.vm_integration import vm_client


class UserService(BaseSvc):

    def validate_ssh_key(self, sshkey):
        ssh = SSHKey(sshkey)

        try:
            ssh.parse()
        except Exception as e:
            msg = """ssh provided by the user is invalid,""" +\
                """type of exception: """ + str(e)
            self.logger.error(msg)
            msg = "Updating SSH Key failed due to invalid key."
            raise VvpBadRequest(msg)

        # remove comment from ssh key
        # ssh.comment returns comment attached to key
        if ssh.comment is not None:
            striped_key = sshkey.replace(ssh.comment, '').strip()
        else:
            striped_key = sshkey.strip()
        try:
            user_with_ssh = IceUserProfile.objects.get(
                ssh_public_key__startswith=striped_key)
        except IceUserProfile.DoesNotExist:
            return True
        except Exception as e:
            self.logger.error(
                "Exception thrown while looking for ssh - %s.", e)
            msg = "Updating SSH Key failed."
            raise Exception(msg)
        else:
            self.logger.debug(
                "SSH key already taken by another user - uuid: %s",
                user_with_ssh.uuid)
            msg = "Updating SSH Key failed due to invalid key."
            raise VvpBadRequest(msg)

    def setSSH(self, user, ssh, action):
        user.ssh_public_key = ssh
        checkAndModifyIfSSHNextStepExist(user)
        eng = getFirstEngByUser(user)

        activity_data = SSHKeyAddedActivityData(action, eng, user)
        bus_service.send_message(ActivityEventMessage(activity_data))

    def get_el_list(self):
        el_role = Role.objects.get(name='el')
        engagement_leads_users = IceUserProfile.objects.filter(role=el_role)
        return SuperThinIceUserProfileModelSerializerForSignals(
            engagement_leads_users, many=True).data

    def get_user_by_email(self, email):
        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get(email=email)
        except UserModel.DoesNotExist:
            return None
        return user

    def addUserToEngAndFireProvisionVfSig(self, user_profile, inviteObj):
        addUsersToEngTeam(inviteObj.engagement_uuid, [user_profile])
        vfObj = VF.objects.get(engagement__uuid=inviteObj.engagement_uuid)
        vm_client.fire_event_in_bg('send_provision_new_vf_event', vfObj)

    def get_user_rgwa_secret(self):
        secret = request_data_mgr.get_user().rgwa_secret_key
        decoded_key = CryptographyText.decrypt(secret)
        return decoded_key
