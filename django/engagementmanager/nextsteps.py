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
from django.utils import timezone
from django.utils.timezone import timedelta
from engagementmanager.models import NextStep
from engagementmanager.service.logging_service import LoggingServiceFactory
from engagementmanager.utils.constants import Constants, NextStepType


logger = LoggingServiceFactory.get_logger()

default_next_steps = [


    {
        'position': 2,
        'stage': 'Intake',
        'text': 'Please work with your Engagement Lead (EL) to complete the necessary trial agreements.',
        'condition': lambda x, y: True,
        'type': NextStepType.trial_agreements.name  # @UndefinedVariable
    },
    {
        'position': 3,
        'stage': 'Intake',
        'text': 'Please add your ' + Constants.service_provider_company_name + ' sponsor or vendor contact information.',
        'condition': lambda user, eng: False if (eng.contact_user) else True,
        'type': NextStepType.add_contact_person.name  # @UndefinedVariable
    },
    {
        'position': 1,
        'stage': 'Active',
        'text': 'Please submit the first version of the VF package. If you have any problems or questions, please contact your Engagement Lead (EL)',
        'condition': lambda x, y: True,
        'type': NextStepType.submit_vf_package.name  # @UndefinedVariable
    },
    {
        'position': 1,
        'stage': 'Validated',
        'text': 'Please schedule a time with your Engagement Lead (EL) to complete the handoff.',
        'condition': lambda x, y: True,
        'type': NextStepType.el_handoff.name  # @UndefinedVariable
    }
]


def create_default_next_steps_for_user(user, el_user):
    """
    This method is for personal default next step only since it has an owner
    """
    def cond(user): return False if (user.ssh_public_key and user.ssh_public_key != '') else True
    if cond(user):
        desc = "Please add your SSH key to be able to contribute."
        nextstep = NextStep.objects.create(creator=el_user, last_updater=el_user, position=1, description=desc, last_update_type='Added', state='Incomplete',
                                           engagement_stage='Intake', engagement=None, owner=user, next_step_type=NextStepType.set_ssh.name, due_date=timezone.now() + timedelta(days=1))  # @UndefinedVariable
        nextstep.assignees.add(user)
        nextstep.save()


def create_default_next_steps(user, engagement, el_user):
    """
    This method is for non-personal default next step only since it doesn't have an owner
    """
    for step in default_next_steps:
        cond = step['condition']
        desc = step['text']
        ns_type = step['type']
        if cond(user, engagement):
            if (user.company == Constants.service_provider_company):
                desc = desc.replace('$Contact', 'Vendor Contact')
            else:
                desc = desc.replace('$Contact', Constants.service_provider_company_name + ' Sponsor Contact')
            logger.debug('Creating default next step : ' + desc)
            nextstep = NextStep.objects.create(creator=el_user, last_updater=el_user, position=step['position'], description=desc, state='Incomplete', engagement_stage=step[
                                               'stage'], engagement=engagement, next_step_type=ns_type, due_date=timezone.now() + timedelta(days=1))
            nextstep.assignees.add(el_user)
            nextstep.save()
        else:
            logger.debug('Skipping creation of default next step : ' + desc)
