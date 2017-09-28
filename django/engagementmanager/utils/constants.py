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
from enum import Enum
from engagementmanager.utils.choice_enum import ChoiceEnum


class Roles(Enum):
    standard_user = 1
    el = 2
    admin = 3
    admin_ro = 4


class Constants(object):
    service_provider_company = None
    role_el = None
    role_standard_user = None
    role_admin = None
    role_admin_ro = None
    service_provider_company_name = "ExampleServiceProvider"
    service_provider_mail_domain = ["example.com"]
    service_provider_admin_mail = "admin@example.com"
    service_provider_admin_ro_mail = "admin_ro@example.com"
    ice_base_ctx = "/vvp/v1/engmgr/"
    rgwa_base_url ='http://localhost:8123/admin'
    default_vfc_version = "1.0.0"
    dbConnectionStr = "dbname='icedb' user='iceuser' host='localhost' password='Aa123456' port='5433'"
    dashboard_href = "<A href=" + \
        str(settings.DOMAIN) + "/#/dashboard/" + ">Dashboard</A>"
    prodDomain = 'https://www.vvp.example.com'
    invite_template_dir = "emails/invite/"
    activate_template_dir = "emails/activate/"
    notification_template_dir = "emails/notification/"
    reset_pwd_template_dir = "emails/reset_pwd/"
    activation_prefix = "/#/activate/"
    program_name = "VVP"


class TemplatesConstants(object):
    logo_url = "https://www.d2ice.att.io/styles/images/d2sandbox_logos-150x30.png"
    contact_mail = "d2ice@att.com"
    context = {"service_provider": Constants.service_provider_company_name,
               "program_name": Constants.program_name,
               "logo_url": logo_url,
               "contact_mail": contact_mail,
               }


'''
In order to get Enum Value as String use: EngagementType.Validation.name
'''
class EngagementModelValidationDate:
    HEAT_VALIDATED = "heat_validated_time"
    IMAGE_SCAN = "image_scan_time"
    AIC_INSTANTIATION = "aic_instantiation_time"
    ASDC_ONBOARDING = "asdc_onboarding_time"


class JenkinsBuildParametersNames:
    CHECKLIST_UUID = "checklist_uuid"
    GIT_REPO_URL = "git_repo_url"


class MockJenkinsBuildLog:
    TEXT = "from server: Started by user admin \n \
            Building in workspace /var/jenkins_home/workspace/{vf_name}_{eng_man_id} \n \
            [{vf_name}_{eng_man_id}] $ /bin/sh /tmp/jenkins{random_id}.sh \n \
            Cloning into '/var/jenkins_home/workspace/{vf_name}_{eng_man_id}/VF'"


class ChecklistDefaultNames:
    HEAT_TEMPLATES = "Heat Templates"
    IMAGE_VALIDATION = "Image Validation"
    AIC_INSTANTIATION = "AIC Instantiation"
    ASDC_ONBOARDING = "ASDC Onboarding"
    VALIDATION_DATE_ARRAY = {
        HEAT_TEMPLATES: EngagementModelValidationDate.HEAT_VALIDATED,
        IMAGE_VALIDATION: EngagementModelValidationDate.IMAGE_SCAN,
        AIC_INSTANTIATION: EngagementModelValidationDate.AIC_INSTANTIATION,
        ASDC_ONBOARDING: EngagementModelValidationDate.ASDC_ONBOARDING
    }


class EngagementType(Enum):
    Validation = 1
    Other = 2


class EngagementStage(ChoiceEnum):
    Intake = 1,
    Active = 2,
    Validated = 3,
    Completed = 4,
    Archived = 5


class NextStepState(ChoiceEnum):
    Incomplete = 1,
    Completed = 2


class RGWApermission:
    READ = 'READ',
    WRITE = 'WRITE'


class NextStepType(ChoiceEnum):
    set_ssh = 1,
    trial_agreements = 2,
    add_contact_person = 3,
    submit_vf_package = 4,
    el_handoff = 5,
    user_defined = 6


class ExceptionType(Enum):
    TSS = 1
    STAT = 2


# NOTE: For each added activity that you wish to send notification mail,
# add an "if" in activity_log::getSubjectAndDescByActivityType
class ActivityType(ChoiceEnum):
    user_joined_eng = 1
    ssh_key_added = 2
    eng_validation_request = 3
    update_next_steps = 4
    vfc = 5
    change_checklist_state = 6
    vf_provisioning_event = 7
    test_finished_event = 8
    change_engagement_stage = 9
    add_next_steps = 10
    delete_next_steps = 11
    notice_empty_engagement = 12


class CheckListLineType(ChoiceEnum):
    auto = 1,
    manual = 2


class CheckListState(ChoiceEnum):
    automation = 1,
    review = 2,
    peer_review = 3,
    approval = 4,
    handoff = 5,
    closed = 6,
    archive = 7,
    pending = 8


class CheckListCategory(ChoiceEnum):
    overall = 1,
    heat = 2,
    glance = 3
    instantiation = 4
    asdc = 5


class CheckListDecisionValue(ChoiceEnum):
    approved = 1,
    denied = 2,
    not_relevant = 3,
    na = 4


class RecentEngagementActionType(ChoiceEnum):
    JOINED_TO_ENGAGEMENT = 1,
    NEXT_STEP_ASSIGNED = 2,
    GOT_OWNERSHIP_OVER_ENGAGEMENT = 3,
    NAVIGATED_INTO_ENGAGEMENT = 4,
    NEW_VF_CREATED = 5,
