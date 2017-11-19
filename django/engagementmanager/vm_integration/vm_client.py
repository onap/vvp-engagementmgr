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
from django.conf import settings
from django.db.models import Q
from engagementmanager.apps import bus_service
from engagementmanager.bus.messages.activity_event_message import \
    ActivityEventMessage
from engagementmanager.models import VF, Role, IceUserProfile
from engagementmanager.utils.constants import Roles
from engagementmanager.utils.activities_data import \
    VFProvisioningActivityData
import concurrent.futures
import validationmanager.em_integration.vm_api as vm_api
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def send_jenkins_job_and_gitlab_repo_exists(vf):
    # A signal which check if jenkins job was created and also if gitlab repo
    logger.debug(
        "Sending a call to validation manager." +
        "Call=jenkins_job_and_gitlab_repo_exists_callback. vf=%s", vf.uuid)
    is_ready = vm_api.jenkins_job_and_gitlab_repo_exists_callback(vf=vf)
    return is_ready


def send_cl_from_pending_to_automation_event(checkListObj):
    # A signal that is sent when Engagement MAnager moves CL from Pending to
    # Automation (for example when a CL is rejected by other signal from
    # validation manager)
    vf = VF.objects.get(engagement=checkListObj.engagement)
    logger.debug(
        "Sending a call to validation manager." +
        "Call=send_cl_from_pending_to_automation_event." +
        "checklistUuid=%s", checkListObj.uuid)
    vm_api.cl_from_pending_to_automation_callback(
        vf=vf, checklist=checkListObj)


def send_ssh_key_created_or_updated_event(user):
    # A signal which is sent from the EM to the VM when a user is adding or
    # updating their ssh key
    logger.debug(
        "Sending a call to validation manager. " +
        "Call=send_ssh_key_created_or_updated_event. user=%s", user.uuid)
    vm_api.ssh_key_created_or_updated_callback(user=user)


def send_create_user_in_rgwa_event(user):
    # A signal which is sent from the EM to the VM when a user is adding or
    # updating their ssh key
    logger.debug(
        "Sending a call to validation manager. " +
        "Call=send_create_user_in_rgwa_event. user=%s", user.full_name)
    vm_api.create_user_rgwa(user=user)


def send_remove_all_standard_users_from_project_event(
        gitlab, project_id, formatted_vf):
    logger.debug(
        "Sending a call to validation manager." +
        "Call=send_remove_all_standard_users_from_project_event.")
    vm_api.remove_all_standard_users_from_project(
        gitlab, project_id, formatted_vf)


def send_get_project_by_vf_event(vf, gitlab):
    if not settings.IS_SIGNAL_ENABLED:
        return None
    logger.debug(
        "Sending a call to validation manager." +
        "Call=send_get_project_by_vf_event.")
    vm_api.get_project_by_vf(vf, gitlab)


def send_provision_new_vf_event(vf):
    # A signal which is sent from the EM to the
    # VM when a new VF is created. VM will than create a
    # gitlab repo for that new VF.
    #
    # Note: despite its name, this signal is not
    # used only for new vfs, but to update existing gitlab
    # and jenkins provisioning when a vf changes e.g. when team members are
    # added or removed.
    try:
        vm_api.provision_new_vf_callback(vf=vf)
        logger.debug(
            "Sending a call to validation manager. " +
            "Call=send_provision_new_vf_event. vf=%s", vf.uuid)
    except Exception as e:
        el_role = Role.objects.get(name=Roles.el.name)  # @UndefinedVariable
        admin_role = Role.objects.get(
            name=Roles.admin.name)  # @UndefinedVariable
        el_admin_list = IceUserProfile.objects.all().filter(
            Q(role=el_role) | Q(role=admin_role))
        activity_data = VFProvisioningActivityData(
            vf, el_admin_list, vf.engagement, e)
        bus_service.send_message(ActivityEventMessage(activity_data))


def send_get_list_of_repo_files_event(vf):
    # A signal which is sent from the EM to the VM when a NextStep is created
    # and we need the VF associated files in the git repository
    files = vm_api.get_list_of_repo_files_callback(vf=vf)
    logger.debug(
        "Sending a call to validation manager. " +
        "Call=send_get_list_of_repo_files_event. vf=%s", vf.uuid)

    formatted_repo_files = []

    for file in files:
        formatted_repo_files.append(file['name'])
        logger.debug(file['name'])

    return formatted_repo_files


'''''''''''''''''''''''''''
 UTIL FUNCTIONS FOR SIGNALS
'''''''''''''''''''''''''''


def fire_event_in_bg(function_name, obj):
    event_function = globals()[function_name]
    logger.debug(
        " . . . . . . . . . . . . Fire event in background started: %s " +
        ". . . . . . . . .  . . . ", function_name)
    executor.submit(event_function, obj)
    logger.debug("Main thread continue without blocking...")
