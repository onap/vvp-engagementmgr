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
from uuid import uuid4
from django.utils import timezone
import string
import random
from engagementmanager.service.logging_service import LoggingServiceFactory
from engagementmanager.utils.authentication import JWTAuthentication
from engagementmanager.models import Vendor, IceUserProfile, Role, \
    Engagement, DeploymentTarget, ApplicationServiceInfrastructure, VF,\
    NextStep, ChecklistTemplate, DeploymentTargetSite, VFC, \
    Checklist, ChecklistSection, ChecklistLineItem,\
    CustomUser
from engagementmanager.utils.constants import Constants

logger = LoggingServiceFactory.get_logger()


class VvpEntitiesCreator:

    def __init__(self):
        pass

    def createUserTemplate(self, company, email, full_name, role,
                           is_service_provider_contact, ssh_key=None, ):
        return {
            'company': company,
            'email': email,
            'phone_number': '555019900',
            'full_name': full_name,
            'role': role,
            'create_time': timezone.now(),
            'is_service_provider_contact': is_service_provider_contact,
            'ssh_public_key': ssh_key,
        }

    def createEngagementTemplate(self, engagement_type, engagement_team):
        return {
            #                 'engagement_type' : engagement_type,
            #                 'members' : engagement_team,
            #                 'start_date' : timezone.now(),
            'progress': 0
        }

    def createVendor(self, vendorName):
        ven = Vendor.objects.filter(name=vendorName)
        if (not ven.exists()):
            vendor = Vendor.objects.create(name=vendorName, public=True)
        else:
            vendor = Vendor.objects.get(name=vendorName)
        return vendor.uuid, vendor

    def createDeploymentTarget(self, name, version):
        deployment = DeploymentTarget.objects.create(
            name=name, version=version)
        return deployment

    def createDeploymentTargetSite(self, name):
        dtsite = DeploymentTargetSite.objects.create(name=name)
        return dtsite

    def createApplicationServiceInfrastructure(self, name):
        asinfrastructure = ApplicationServiceInfrastructure.objects.create(
            name=name)
        return asinfrastructure

    def getOrCreateIfNotExist(self, entity, getCriteria, creationFields):
        obj = None
        try:
            logger.debug("about to look for object: " + str(getCriteria))
            obj = entity.objects.get(**getCriteria)
            logger.debug('found object')
        except entity.DoesNotExist:
            logger.error('not found. Trying to create...')
            obj = entity.objects.create(**creationFields)
        return obj

    def createAndGetDefaultRoles(self):
        admin = self.getOrCreateIfNotExist(
            Role, {'name': 'admin'}, {'name': 'admin'})
        el = self.getOrCreateIfNotExist(Role, {'name': 'el'}, {'name': 'el'})
        standard_user = self.getOrCreateIfNotExist(
            Role, {'name': 'standard_user'}, {
                'name': 'standard_user'})
        return admin, el, standard_user

    def createUser(self, company, email, phone, fullName, role,
                   is_active=False, ssh_key=None,
                   activation_token_create_time=timezone.now()):
        try:
            user, is_user_created = CustomUser.objects.get_or_create(
                username=email, defaults={
                    'email': email, 'password': '12345678',
                    'activation_token': uuid4(),
                    'activation_token_create_time': timezone.now(),
                    'last_login': timezone.now(), 'is_active': is_active})
            user_profile, is_profile_created = \
                IceUserProfile.objects.update_or_create(
                    email=email, defaults=self.createUserTemplate(
                        company, email, fullName, role, False, ssh_key))
        except Exception as e:
            logger.error("VvpEntitiesCreator - createUser - error:")
            logger.error(e)
            return None
        return user_profile

    def createEngagement(self, uuid, engagement_type, engagement_team):
        return self.getOrCreateIfNotExist(
            Engagement, {'uuid': uuid}, self.createEngagementTemplate(
                engagement_type, engagement_team))

    def createVF(self, name, engagement, deployment,
                 is_service_provider_internal, vendor, **kwargs):
        vf = VF.objects.create(
            name=name, engagement=engagement,
            deployment_target=deployment,
            is_service_provider_internal=is_service_provider_internal,
            vendor=vendor,
            target_lab_entry_date=timezone.now(), **kwargs)
        return vf

    def createNextStep(self, uuid, createFields):
        return self.getOrCreateIfNotExist(
            NextStep, {'uuid': uuid}, createFields)

    def createDefaultCheckListTemplate(self):
        checklist_templates = [
            {
                'name': 'Heat',
                'category': 'first category',
                'version': 1,
                'sections': [
                    {
                        'name': 'Parameter Specification',
                        'weight': 1,
                        'description': 'section description',
                        'validation_instructions': 'valid instructions',
                        'lineitems': [
                            {
                                'name': 'Parameters',
                                'weight': 1,
                                'description': 'Numeric parameters ' +
                                'should include range and/or allowed values.',
                                'validation_instructions': 'Here are some ' +
                                'useful tips for how to validate this item ' +
                                ' in the most awesome way:<br><br><ul><li>' +
                                'Here is my awesome tip 1</li><li>Here is ' +
                                'my awesome tip 2</li><li>' +
                                'Here is my awesome ' +
                                'tip 3</li></ul>',
                                'line_type': 'auto',
                            },
                            {
                                'name': 'String parameters',
                                'weight': 1,
                                'description': 'Numeric parameters ' +
                                'should include range and/or allowed values.',
                                'validation_instructions': 'Here are some ' +
                                'useful tips for how to validate this item ' +
                                'in the most awesome way:<br><br><ul><li>' +
                                'Here is my awesome tip 1</li><li>Here is ' +
                                'my awesome tip 2</li><li>' +
                                'Here is my awesome ' +
                                'tip 3</li></ul>',
                                'line_type': 'auto',
                            },
                            {
                                'name': 'Numeric parameters',
                                'weight': 1,
                                'description': 'Numeric parameters should ' +
                                'include range and/or allowed values.',
                                'validation_instructions': 'Here are some ' +
                                'useful tips for how to ' +
                                'validate this item in ' +
                                'the most awesome way:<br><br><ul><li>' +
                                'Here is ' +
                                'my awesome tip 1</li><li>' +
                                'Here is my awesome ' +
                                'tip 2</li><li>Here is my awesome tip 3' +
                                '</li></ul>',
                                'line_type': 'auto',
                            }
                        ]
                    },
                    {
                        'name': 'External References',
                        'weight': 1,
                        'description': 'section descripyion',
                        'validation_instructions': 'valid instructions',
                        'lineitems': [
                            {
                                'name': 'Normal references',
                                'weight': 1,
                                'description': 'Numeric parameters should ' +
                                'include range and/or allowed values.',
                                'validation_instructions': 'Here are ' +
                                'some useful tips for how to validate ' +
                                'this item in the most awesome way:' +
                                '<br><br><ul><li>Here is my awesome ' +
                                'tip 1</li><li>Here is my awesome tip 2' +
                                '</li><li>Here is my awesome tip 3</li></ul>',
                                'line_type': 'manual',
                            },
                            {
                                'name': 'VF image',
                                'weight': 1,
                                'description': 'Numeric parameters should ' +
                                'include range and/or allowed values.',
                                'validation_instructions': 'Here are some ' +
                                'useful tips for how to validate this item ' +
                                'in the most awesome way:<br><br><ul><li>' +
                                'Here is my awesome tip 1</li><li>Here ' +
                                'is my awesome tip 2</li><li>Here is my ' +
                                'awesome tip 3</li></ul>',
                                'line_type': 'auto',
                            }
                        ]

                    }
                ]
            }
        ]

        for template in checklist_templates:
            created_template = ChecklistTemplate.objects.get_or_create(
                name=template['name'], defaults={
                    'category': template['category'],
                    'version': template['version'],
                    'create_time': timezone.now()
                })
            created_template = ChecklistTemplate.objects.get(
                name=template['name'])
            for section in template['sections']:
                created_section = ChecklistSection.objects.get_or_create(
                    name=section['name'],
                    template_id=created_template.uuid,
                    defaults={
                        'weight': section['weight'],
                        'description': section['description'],
                        'validation_instructions': section[
                            'validation_instructions']

                    })
                created_section = ChecklistSection.objects.get(
                    name=section['name'], template_id=created_template.uuid)
                for lineitem in section['lineitems']:
                    ChecklistLineItem.objects.get_or_create(
                        name=lineitem['name'],
                        template_id=created_template.uuid,
                        defaults={
                            'weight': lineitem['weight'],
                            'description': lineitem['description'],
                            'validation_instructions': lineitem[
                                'validation_instructions'],
                            'line_type': lineitem['line_type'],
                            'section_id': created_section.uuid,
                        })

        self.defaultCheklistTemplate = ChecklistTemplate.objects.get(
            name="Heat")

        return self.defaultCheklistTemplate

    def createCheckList(self, name, state, validation_cycle, associated_files,
                        engagement, template, creator, owner):
        if (not associated_files):
            associated_files = '{}'
        return self.getOrCreateIfNotExist(Checklist, {'name': name}, {
            'state': state,
            'name': name,
            'validation_cycle': 1,
            'associated_files': associated_files,
            'engagement': engagement,
            'template': template,
            'creator': creator,
            'owner': owner
        })

    def createVFC(self, name, ext_ref, company, vf, creator):
        obj = None
        try:
            obj = VFC.objects.get(name=name)
        except VFC.DoesNotExist:
            return VFC.objects.create(name=name, external_ref_id=ext_ref,
                                      company=company, creator=creator, vf=vf)
        return obj

    def randomGenerator(self, typeOfValue, numberOfDigits=0):
        lettersAndNumbers = string.ascii_letters + string.digits
        if typeOfValue == 'email':
            myEmail = ''.join(
                random.choice(lettersAndNumbers) for _ in range(4)) + "@" + \
                ''.join(random.choice(string.ascii_uppercase)
                        for _ in range(4)) + ".com"
            return myEmail
        elif typeOfValue == 'main-vendor-email':
            myEmail = ''.join(
                random.choice(lettersAndNumbers) for _ in range(4)) + "@" + \
                Constants.service_provider_mail_domain[0]
            return myEmail
        elif typeOfValue == 'randomNumber':
            randomNumber = ''.join("%s" % random.randint(0, 9)
                                   for _ in range(0, (numberOfDigits + 1)))
            return randomNumber
        elif typeOfValue == 'randomString':
            randomString = "".join(random.sample(lettersAndNumbers, 5))
            return randomString
        else:
            logger.debug("Error on randonGenerator - given bad value.")
            exit

    def loginAndCreateSessionToken(self, user):
        jwt_service = JWTAuthentication()
        token = jwt_service.create_token(user.user)
        logger.debug("token " + token)
        return token
