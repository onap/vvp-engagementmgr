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
'''
Each entity has a model serializer that save/update the object in its create()/update() methods and a regular dictionary (map) serializer that return a new/updated instance of the object

'''
from rest_framework import serializers

from engagementmanager.models import NextStep, Notification, Activity, \
    ChecklistTemplate, Checklist, ChecklistAuditLog, ChecklistDecision, \
    ChecklistLineItem, ECOMPRelease, EngagementStatus, CustomUser, \
    ChecklistSection

from .models import IceUserProfile, VFC, Engagement, VF, DeploymentTarget, Role, Vendor, DeploymentTargetSite


class RoleModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = '__all__'


class VendorModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vendor
        fields = '__all__'


class ThinVendorModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vendor
        fields = ('uuid', 'name')


class SuperThinCustomUserModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ('is_active', 'email', 'activation_token')


class ThinCustomUserModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ('email', 'activation_token', 'is_active',
                  'activation_token_create_time')


class IceUserProfileModelSerializer(serializers.ModelSerializer):
    role = RoleModelSerializer(many=False)
    company = VendorModelSerializer(many=False)
    user = ThinCustomUserModelSerializer(many=False)

    class Meta:
        model = IceUserProfile


class SuperThinIceUserProfileModelSerializer(serializers.ModelSerializer):
    role = RoleModelSerializer(many=False)
    company = VendorModelSerializer(many=False)
    user = SuperThinCustomUserModelSerializer(many=False)

    class Meta:
        model = IceUserProfile
        fields = ('full_name', 'email', 'uuid', 'role',
                  'user', 'company', 'phone_number')


class SuperThinIceUserProfileModelSerializerForSignals(serializers.ModelSerializer):
    role = RoleModelSerializer(many=False)

    class Meta:
        model = IceUserProfile
        fields = ('full_name', 'email', 'role', 'uuid', 'ssh_public_key')


class ThinIceUserProfileModelSerializer(serializers.ModelSerializer):
    role = RoleModelSerializer(many=False)
    company = VendorModelSerializer(many=False)
    user = SuperThinCustomUserModelSerializer(many=False)

    class Meta:
        model = IceUserProfile
        fields = ('email', 'full_name', 'user', 'is_service_provider_contact', 'phone_number', 'role', 'uuid', 'company',
                  'ssh_public_key', 'regular_email_updates', 'email_updates_on_every_notification',
                  'email_updates_daily_digest', 'rgwa_access_key')


class EngagementStatusModelSerializer(serializers.ModelSerializer):
    creator = SuperThinIceUserProfileModelSerializer(many=False)

    class Meta:
        model = EngagementStatus
        fields = '__all__'


class EngagementModelSerializer(serializers.ModelSerializer):
    engagement_team = SuperThinIceUserProfileModelSerializer(many=True)
    contact_user = SuperThinIceUserProfileModelSerializer(many=False)
    creator = SuperThinIceUserProfileModelSerializer(many=False)
    peer_reviewer = SuperThinIceUserProfileModelSerializer(many=False)
    reviewer = SuperThinIceUserProfileModelSerializer(many=False)
    starred_engagement = SuperThinIceUserProfileModelSerializer(many=True)

    class Meta:
        model = Engagement
        fields = '__all__'


class ThinEngagementModelSerializer(serializers.ModelSerializer):
    creator = SuperThinIceUserProfileModelSerializer(many=False)
    engagement_team = SuperThinIceUserProfileModelSerializer(many=True)
    peer_reviewer = SuperThinIceUserProfileModelSerializer(many=False)
    reviewer = SuperThinIceUserProfileModelSerializer(many=False)

    class Meta:
        model = Engagement
        fields = ('uuid', 'engagement_manual_id', 'creator',
                  'engagement_team', 'peer_reviewer', 'reviewer')


class DeploymentTargetModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeploymentTarget
        fields = ('uuid', 'name', 'version', 'weight', 'ui_visibility')


class ECOMPReleaseModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ECOMPRelease
        fields = ('uuid', 'name', 'weight', 'ui_visibility')


class ThinVFModelSerializer(serializers.ModelSerializer):
    engagement = ThinEngagementModelSerializer(many=False)

    class Meta:
        model = VF
        fields = (
            'uuid', 'name', 'engagement', 'is_service_provider_internal', 'ecomp_release')


class ThinDeploymentTargetSiteModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeploymentTargetSite
        fields = ('uuid', 'name')


class DeploymentTargetSiteModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeploymentTargetSite
        fields = '__all__'


class VFModelSerializer(serializers.ModelSerializer):
    engagement = EngagementModelSerializer(many=False)
    deployment_target = DeploymentTargetModelSerializer(many=False)
    ecomp_release = ECOMPReleaseModelSerializer(many=False)
    deployment_target_sites = ThinDeploymentTargetSiteModelSerializer(
        many=True)
    vendor = VendorModelSerializer(many=False)

    class Meta:
        model = VF
        fields = '__all__'


class VFCModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = VFC
        fields = '__all__'


class ActivityModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Activity
        fields = '__all__'


class ThinActivityModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Activity
        fields = ('uuid', 'description', 'create_time', 'metadata')


class NotificationModelSerializer(serializers.ModelSerializer):
    activity = ActivityModelSerializer(many=False)

    class Meta:
        model = Notification
        fields = '__all__'


class ThinNotificationModelSerializer(serializers.ModelSerializer):
    activity = ThinActivityModelSerializer(many=False)

    class Meta:
        model = Notification
        fields = '__all__'


class ChecklistTemplateModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChecklistTemplate
        exclude = ('create_time', 'update_time', 'category', 'version')


class ThinChecklistTemplateModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChecklistTemplate
        fields = ('uuid', 'name')


class ChecklistModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Checklist
        fields = '__all__'


class SuperThinChecklistModelSerializer(serializers.ModelSerializer):
    owner = ThinIceUserProfileModelSerializer(many=False)

    class Meta:
        model = Checklist
        fields = ('uuid', 'name', 'state', 'owner')


class ThinChecklistModelSerializer(serializers.ModelSerializer):
    engagement = ThinEngagementModelSerializer(many=False)
    template = ThinChecklistTemplateModelSerializer(many=False)
    owner = ThinIceUserProfileModelSerializer(many=False)

    class Meta:
        model = Checklist
        fields = ('uuid', 'name', 'state', 'owner', 'weight',
                  'associated_files', 'engagement', 'template')


class ThinPostChecklistResponseModelSerializer(serializers.ModelSerializer):
    template = ThinChecklistTemplateModelSerializer(many=False)

    class Meta:
        model = Checklist
        fields = ('uuid', 'name', 'state', 'associated_files', 'template')


class UserNextStepModelSerializer(serializers.ModelSerializer):
    engagement_manual_id = serializers.CharField(
        source='engagement.engagement_manual_id')
    engagement_uuid = serializers.CharField(source='engagement.uuid')
    creator_full_name = serializers.CharField(source='creator.full_name')
    vf_name = serializers.CharField(source='engagement.vf.name')

    class Meta:
        model = NextStep
        fields = ('due_date', 'engagement_manual_id', 'description',
                  'create_time', 'creator_full_name', 'vf_name', 'engagement_uuid')


class NextStepModelSerializer(serializers.ModelSerializer):
    engagement = EngagementModelSerializer(many=False)
    creator = SuperThinIceUserProfileModelSerializer(many=False)
    last_updater = SuperThinIceUserProfileModelSerializer(many=False)
    assignees = SuperThinIceUserProfileModelSerializer(many=True)

    class Meta:
        model = NextStep
        fields = '__all__'


class ThinNextStepModelSerializer(serializers.ModelSerializer):
    assignees = SuperThinIceUserProfileModelSerializer(many=True)
    last_updater = SuperThinIceUserProfileModelSerializer(many=False)

    class Meta:
        ordering = ('position')
        model = NextStep
        fields = '__all__'


class TestEngineChecklistModelSerializer(serializers.ModelSerializer):
    template_id = serializers.CharField(source='template.uuid')
    engagement_manual_id = serializers.CharField(
        source='engagement.engagement_manual_id')
    engagement_id = serializers.CharField(source='engagement.uuid')
    creator_id = serializers.CharField(source='engagement.creator.uuid')

    class Meta:
        model = Checklist
        fields = ('uuid', 'state', 'associated_files', 'template_id',
                  'engagement_manual_id', 'engagement_id', 'creator_id')


class ChecklistAuditLogModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChecklistAuditLog
        fields = '__all__'


class ThinChecklistAuditLogModelSerializer(serializers.ModelSerializer):
    creator = SuperThinIceUserProfileModelSerializer(many=False)

    class Meta:
        model = ChecklistAuditLog
        fields = ('uuid', 'category', 'description', 'create_time', 'creator')


class ChecklistSectionModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChecklistSection
        exclude = ('template', 'parent_section', 'create_time', 'update_time')


class ChecklistLineItemModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChecklistLineItem
        exclude = ('section', 'template', 'create_time', 'update_time')


class ThinChecklistSectionModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChecklistLineItem
        fields = ('uuid', 'name', 'weight', 'description')


class ThinChecklistLineItemModelSerializer(serializers.ModelSerializer):
    section = ThinChecklistSectionModelSerializer(many=False)

    class Meta:
        model = ChecklistLineItem
        fields = ('uuid', 'name', 'line_type', 'weight',
                  'description', 'validation_instructions', 'section')


class ThinChecklistDecisionModelSerializer(serializers.ModelSerializer):
    lineitem = ThinChecklistLineItemModelSerializer(many=False)

    class Meta:
        model = ChecklistDecision
        fields = ('uuid', 'review_value', 'peer_review_value', 'lineitem')


class EngagementModelSerializerForSignal(serializers.ModelSerializer):
    engagement_team = SuperThinIceUserProfileModelSerializerForSignals(
        many=True)
    contact_user = SuperThinIceUserProfileModelSerializerForSignals(many=False)
    creator = SuperThinIceUserProfileModelSerializerForSignals(many=False)
    peer_reviewer = SuperThinIceUserProfileModelSerializerForSignals(
        many=False)
    reviewer = SuperThinIceUserProfileModelSerializerForSignals(many=False)
    starred_engagement = SuperThinIceUserProfileModelSerializerForSignals(
        many=True)

    class Meta:
        model = Engagement
        fields = '__all__'


class VFModelSerializerForSignal(serializers.ModelSerializer):
    engagement = EngagementModelSerializerForSignal(many=False)
    deployment_target = DeploymentTargetModelSerializer(many=False)
    ecomp_release = ECOMPReleaseModelSerializer(many=False)
    deployment_target_sites = ThinDeploymentTargetSiteModelSerializer(
        many=True)
    vendor = VendorModelSerializer(many=False)

    class Meta:
        model = VF
        fields = '__all__'
