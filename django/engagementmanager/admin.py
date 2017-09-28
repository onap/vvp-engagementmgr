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
from django.contrib import admin

from engagementmanager import models


@admin.register(models.Activity)
class ActivityModelAdmin(admin.ModelAdmin):

    list_display = ["engagement_manual_id", "vf_name", "description",
                    "activity_type", "activity_owner", "create_time", "is_notification"]
    list_filter = ["activity_type", "is_notification"]

    def engagement_manual_id(self, obj):
        if obj.engagement:
            return obj.engagement.engagement_manual_id
        else:
            return ""

    def vf_name(self, obj):
        if obj.engagement:
            return models.VF.objects.get(engagement=obj.engagement).name
        else:
            return ""

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('create_time',)
        return self.readonly_fields


@admin.register(models.Checklist)
class ChecklistModelAdmin(admin.ModelAdmin):

    list_display = ["name", "state", "engagement_manual_id", "vf_name", "validation_cycle",
                    "weight", "template", "owner", "creator", "associated_files", "create_time", "update_time"]
    list_filter = ["template", "state"]
    search_fields = ["name", "associated_files"]

    def engagement_manual_id(self, obj):
        return obj.engagement.engagement_manual_id

    def vf_name(self, obj):
        return models.VF.objects.get(engagement=obj.engagement).name


@admin.register(models.ChecklistAuditLog)
class ChecklistAuditLogModelAdmin(admin.ModelAdmin):

    list_display = ["description", "creator", "checklist", "create_time", "update_time"]
    list_filter = ["category"]
    search_fields = ["description"]


@admin.register(models.ChecklistDecision)
class ChecklistDecisionModelAdmin(admin.ModelAdmin):

    list_display = ["checklist", "lineitem", "review_value", "peer_review_value", "create_time", "update_time"]
    list_filter = ["template"]
    search_fields = ["name"]


@admin.register(models.ChecklistLineItem)
class ChecklistLineItemModelAdmin(admin.ModelAdmin):

    list_display = ["name", "weight", "template", "section", "create_time", "update_time"]
    list_filter = ["template", "section"]
    search_fields = ["name"]


@admin.register(models.ChecklistSection)
class ChecklistSectionModelAdmin(admin.ModelAdmin):

    list_display = ["name", "weight", "template", "parent_section", "create_time", "update_time"]
    list_filter = ["template"]


@admin.register(models.ChecklistTemplate)
class ChecklistTemplateModelAdmin(admin.ModelAdmin):

    list_display = ["name", "category", "version", "create_time", "update_time"]
    list_filter = ["category", "version"]
    search_fields = ["name"]
    search_fields = ["name"]


@admin.register(models.DeploymentTarget)
class DeploymentTargetModelAdmin(admin.ModelAdmin):

    list_display = ["name", "version"]
    list_filter = ["version"]


@admin.register(models.DeploymentTargetSite)
class DeploymentTargetSiteModelAdmin(admin.ModelAdmin):

    list_display = ["name"]


@admin.register(models.Engagement)
class EngagementModelAdmin(admin.ModelAdmin):

    list_display = ["engagement_manual_id", "vf_name", "deployment_target_name", "ecomp_release", "progress", "target_completion_date",
                    "target_lab_entry_date", "engagement_stage", "create_time"]
    list_editable = ["progress", "target_completion_date", "engagement_stage"]
    list_filter = ["engagement_stage"]
    search_fields = ["engagement_stage", "engagement_manual_id"]

    def vf_name(self, obj):
        return models.VF.objects.get(engagement=obj).name

    def target_lab_entry_date(self, obj):
        return models.VF.objects.get(engagement=obj).target_lab_entry_date

    def ecomp_release(self, obj):
        return models.VF.objects.get(engagement=obj).ecomp_release

    def deployment_target_name(self, obj):
        e = models.VF.objects.get(engagement=obj)
        return e.deployment_target.name + " " + e.deployment_target.version

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('create_time',)
        return self.readonly_fields


@admin.register(models.EngagementStatus)
class EngagementStatusModelAdmin(admin.ModelAdmin):

    list_display = ["engagement_manual_id", "vf_name", "description", "creator_full_name", "create_time", "update_time"]
    list_filter = ["creator"]
    search_fields = ["description"]

    def engagement_manual_id(self, obj):
        return obj.engagement.engagement_manual_id

    def vf_name(self, obj):
        return models.VF.objects.get(engagement=obj.engagement).name

    def creator_full_name(self, obj):
        return obj.creator.full_name


@admin.register(models.ECOMPRelease)
class ECOMPReleaseModelAdmin(admin.ModelAdmin):

    list_display = ["name"]
    search_fields = ["name"]


@admin.register(models.IceUserProfile)
class IceUserProfileModelAdmin(admin.ModelAdmin):

    list_display = ["full_name", "email", "phone_number", "company_name", "role_name", "is_service_provider_contact", "has_ssh_key",
                    "create_time", "role"]
    list_editable = ["phone_number", "is_service_provider_contact", "role"]
    list_filter = ["is_service_provider_contact", "role", "company"]
    search_fields = ["full_name", "email", "phone_number"]

    def company_name(self, obj):
        return obj.company.name

    def role_name(self, obj):
        return obj.role.name

    def has_ssh_key(self, obj):
        if obj.ssh_public_key:
            return True
        else:
            return False

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('create_time',)
        return self.readonly_fields


@admin.register(models.Invitation)
class InvitationModelAdmin(admin.ModelAdmin):

    list_display = ["email", "engagement_manual_id", "vf_name",
                    "invited_by_user", "accepted", "create_time", "invitation_token"]
    list_filter = ["accepted"]
    search_fields = ["email", "invitation_token"]

    def invited_by_user(self, obj):
        return models.IceUserProfile.objects.get(uuid=obj.invited_by_user_uuid).full_name

    def engagement_manual_id(self, obj):
        return models.Engagement.objects.get(uuid=obj.engagement_uuid).engagement_manual_id

    def vf_name(self, obj):
        e = models.Engagement.objects.get(uuid=obj.engagement_uuid)
        return models.VF.objects.get(engagement=e).name


@admin.register(models.NextStep)
class NextStepModelAdmin(admin.ModelAdmin):

    list_display = ["engagement_manual_id", "vf_name", "description", "files", "due_date", "last_updater_full_name", "last_update_time",
                    "last_update_type", "creator_full_name", "create_time", "state", "next_step_type", "owner_full_name"]
    list_filter = ["next_step_type", "state"]
    search_fields = ["description", "files"]

    def engagement_manual_id(self, obj):
        e = obj.engagement
        if e:
            return e.engagement_manual_id
        else:
            return ""

    def vf_name(self, obj):
        e = obj.engagement
        if e:
            return models.VF.objects.get(engagement=e).name
        else:
            return ""

    def creator_full_name(self, obj):
        c = obj.creator
        if c:
            return c.full_name
        else:
            return ""

    def last_updater_full_name(self, obj):
        lu = obj.last_updater
        if lu:
            return lu.full_name
        else:
            return ""

    def owner_full_name(self, obj):
        o = obj.owner
        if o:
            return o.full_name
        else:
            return ""

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('state',)
        return self.readonly_fields


@admin.register(models.Notification)
class NotificationModelAdmin(admin.ModelAdmin):

    list_display = ["activity_description", "activity_type", "engagement_manual_id",
                    "vf_name", "is_sent", "is_read", "activity_create_time"]
    list_filter = ["is_sent", "is_read"]

    def activity_description(self, obj):
        return obj.activity.description

    def activity_type(self, obj):
        return obj.activity.activity_type

    def activity_create_time(self, obj):
        return obj.activity.create_time

    def engagement_manual_id(self, obj):
        if obj.activity.engagement:
            return obj.activity.engagement.engagement_manual_id
        else:
            return ""

    def vf_name(self, obj):
        if obj.activity.engagement:
            return models.VF.objects.get(engagement=obj.activity.engagement).name
        else:
            return ""


@admin.register(models.RecentEngagement)
class RecentEngagementModelAdmin(admin.ModelAdmin):

    list_display = ["engagement_manual_id", "vf_name", "ice_user", "action_type", "last_update"]
    list_filter = ["action_type"]

    def vf_name(self, obj):
        return obj.vf.name

    def engagement_manual_id(self, obj):
        return obj.vf.engagement.engagement_manual_id

    def ice_user(self, obj):
        return models.IceUserProfile.objects.get(uuid=obj.user_uuid).full_name


@admin.register(models.Role)
class RoleModelAdmin(admin.ModelAdmin):

    list_display = ["name"]


@admin.register(models.Vendor)
class VendorModelAdmin(admin.ModelAdmin):

    list_display = ["name", "public"]
    list_editable = ["public"]
    search_fields = ["name"]


@admin.register(models.VF)
class VFModelAdmin(admin.ModelAdmin):

    list_display = ["name", "deployment_target", "ecomp_release", "progress", "target_completion_date",
                    "target_lab_entry_date", "is_service_provider_internal", "git_repo_url", "engagement_stage", "engagement_manual_id"]
    list_filter = ["deployment_target", "ecomp_release", "is_service_provider_internal", "vendor"]
    list_editable = ["is_service_provider_internal"]
    search_fields = ["name", "git_repo_url"]

    def engagement_manual_id(self, obj):
        return obj.engagement.engagement_manual_id

    def progress(self, obj):
        return obj.engagement.progress

    def target_completion_date(self, obj):
        return obj.engagement.target_completion_date

    def engagement_stage(self, obj):
        return obj.engagement.engagement_stage


@admin.register(models.VFC)
class VFCModelAdmin(admin.ModelAdmin):

    list_display = ["name", "external_ref_id", "ice_mandated", "vf_name", "company_name", "engagement_manual_id"]
    list_filter = ["ice_mandated", "company"]
    list_editable = ["external_ref_id", "ice_mandated"]
    search_fields = ["name", "external_ref_id"]

    def vf_name(self, obj):
        return obj.vf.name

    def engagement_manual_id(self, obj):
        return obj.vf.engagement.engagement_manual_id

    def company_name(self, obj):
        return obj.company.name
