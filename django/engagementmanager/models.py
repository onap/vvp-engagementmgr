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
from __future__ import unicode_literals
import uuid
from django.contrib.auth.models import User
from django.db import models
from django.db.models.deletion import SET_NULL
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.timezone import timedelta
from engagementmanager.service.logging_service import LoggingServiceFactory
from engagementmanager.utils.constants import EngagementStage, ActivityType, NextStepType, CheckListState, CheckListCategory, CheckListDecisionValue, CheckListLineType, \
    RecentEngagementActionType, NextStepState


logger = LoggingServiceFactory.get_logger()


class Role(models.Model):
    uuid = models.CharField(default=uuid.uuid4, max_length=36, unique=True)
    name = models.CharField(max_length=36, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "ice_role"


class Vendor(models.Model):
    uuid = models.CharField(default=uuid.uuid4, max_length=36, unique=True)
    name = models.CharField(max_length=100, unique=True)
    public = models.BooleanField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "ice_vendor"


class CustomUser(User):
    activation_token = models.CharField(max_length=128, unique=True, null=True)
    activation_token_create_time = models.DateTimeField(
        'activation_token_create_time', default=timezone.now, null=True)
    temp_password = models.CharField(
        max_length=256, null=True, blank=True, default=None)

    def __str__(self):
        return self.email

    class Meta:
        db_table = "ice_custom_user"


class IceUserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, null=False, on_delete=models.CASCADE)
    uuid = models.CharField(default=uuid.uuid4, max_length=36, unique=True)
    company = models.ForeignKey(Vendor, on_delete=models.PROTECT, null=True)
    phone_number = models.CharField(max_length=30)
    full_name = models.CharField(max_length=30)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True)
    # although number of expected users<10^5 we prefer to index it
    email = models.EmailField('email', unique=True, db_index=True)
    create_time = models.DateTimeField('creation time', default=timezone.now)
    ssh_public_key = models.CharField(
        'ssh_public_key', max_length=1024, null=True, blank=True)
    regular_email_updates = models.BooleanField(default=False)
    email_updates_on_every_notification = models.BooleanField(default=True)
    email_updates_daily_digest = models.BooleanField(default=False)
    is_service_provider_contact = models.BooleanField(default=False)
    rgwa_access_key = models.CharField(
        max_length=1024, null=True, blank=True, unique=True)
    rgwa_secret_key = models.CharField(
        max_length=1024, null=True, blank=True, unique=True)
    slack_handle = models.CharField(
        max_length=64, null=True, blank=True, default=None)

    def __str__(self):
        return self.full_name + " - " + self.email

    class Meta:
        db_table = "ice_user_profile"


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user = CustomUser.objects.get(username=instance)
        profile, created = IceUserProfile.objects.get_or_create(
            user=user, email=instance)


post_save.connect(create_user_profile, sender=CustomUser)


# Represents Deployment Target Cloud Version. For example name=AIC version=2.0
class DeploymentTarget(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, primary_key=True)
    name = models.CharField(max_length=45)
    version = models.CharField(max_length=100)
    weight = models.IntegerField(default=1)
    ui_visibility = models.BooleanField(default=True)

    def __str__(self):
        return self.name + ", Version: " + self.version

    class Meta:
        db_table = "ice_deployment_target"
        unique_together = (("name", "version"),)


# Represents ECOMPRelease
class ECOMPRelease(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, primary_key=True)
    name = models.CharField(max_length=45)
    weight = models.IntegerField(default=1)
    ui_visibility = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "ice_ecomp_release"


# Represents Deployment Target site, for example: Willows. It is connected
# to deployment target version
class DeploymentTargetSite(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, primary_key=True)
    name = models.CharField(max_length=45)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "ice_deployment_target_site"


def get_default_target_completion_date():
    return timezone.now() + timedelta(days=16)


class Engagement(models.Model):
    # no need to index this since index already exists thanks to it PK
    # characteristics
    uuid = models.CharField(
        default=uuid.uuid4, max_length=64, primary_key=True)
    engagement_team = models.ManyToManyField(
        IceUserProfile, related_name='members')
    creator = models.ForeignKey(
        IceUserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name='Engagement_creator')
    contact_user = models.ForeignKey(
        IceUserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name='Engagement_contact_user')
    engagement_manual_id = models.CharField(
        max_length=36, null=False, blank=False, default=-1, db_index=True)  # index in favor of dashboard search
    progress = models.IntegerField(default=0)
    target_completion_date = models.DateField(
        null=True, blank=True, default=get_default_target_completion_date)
    engagement_stage = models.CharField(max_length=15, default=EngagementStage.Intake.name, choices=EngagementStage.choices(
    ), db_index=True)  # Can be: Intake, Active, Validated, Completed @UndefinedVariable
    create_time = models.DateTimeField('creation time', default=timezone.now)
    peer_reviewer = models.ForeignKey(
        IceUserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name='Engagement_peer_reviewer')
    reviewer = models.ForeignKey(
        IceUserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name='Engagement_el_reviewer')
    starred_engagement = models.ManyToManyField(
        IceUserProfile, default=None, blank=True)
    heat_validated_time = models.DateTimeField(
        'heat validated time', null=True, blank=True)
    image_scan_time = models.DateTimeField(
        'image scan time', null=True, blank=True)
    aic_instantiation_time = models.DateTimeField(
        'aic instantiation time', null=True, blank=True)
    asdc_onboarding_time = models.DateTimeField(
        'asdc onboarding time', null=True, blank=True)
    started_state_time = models.DateTimeField(
        'started state time', null=True, blank=True)
    intake_time = models.DateTimeField('intake time', null=True, blank=True)
    active_time = models.DateTimeField('active time', null=True, blank=True)
    validated_time = models.DateTimeField(
        'validated time', null=True, blank=True)
    completed_time = models.DateTimeField(
        'completed time', null=True, blank=True)
    archive_reason = models.TextField(default=None, null=True)
    archived_time = models.DateTimeField(
        'archived time', null=True, blank=True)
    is_with_files = models.BooleanField(default=False)

    def __str__(self):
        return " uuid: " + str(self.uuid)

    class Meta:
        db_table = "ice_engagement"


class EngagementStatus(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=64, primary_key=True)
    engagement = models.ForeignKey(Engagement, on_delete=models.PROTECT)
    description = models.CharField(max_length=256)
    creator = models.ForeignKey(
        IceUserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name='status_creator')
    create_time = models.DateTimeField(default=timezone.now)
    update_time = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "ice_engagement_status"


class Activity(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, unique=True, primary_key=True)
    create_time = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=512)
    is_notification = models.BooleanField(default=False)
    engagement = models.ForeignKey(
        Engagement, on_delete=models.PROTECT, db_index=True, null=True)
    activity_type = models.CharField(
        max_length=36, choices=ActivityType.choices())
    activity_owner = models.ForeignKey(IceUserProfile, null=True, blank=True)
    metadata = models.CharField(max_length=1024)

    def __str__(self):
        return 'Activity created at ' + str(self.create_time) + ', Description: ' + self.description + ', Notification:' + str(self.is_notification) + ', ActivityType=' + str(self.activity_type)

    class Meta:
        ordering = ['-create_time']
        db_table = "ice_activity"
        # index in favor of pullRecentActivities
        index_together = ["engagement", "activity_owner"]


class Notification(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, unique=True, primary_key=True)
    user = models.ForeignKey(IceUserProfile, on_delete=models.CASCADE)
    is_sent = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.user) + ' ' + str(self.is_sent) + ' ' + str(self.is_read)

    class Meta:
        db_table = "ice_notification"
        # index in favor of Notification screen (pull_recent_notifications,
        # num_of_notifications_for_user)
        index_together = ["user", "is_read"]


class Feedback(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, unique=True, primary_key=True)
    create_time = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(IceUserProfile, null=False)
    description = models.TextField('feedback_description')

    def __str__(self):
        return 'Feedback created at ' + str(self.create_time) + ' ' + str(self.user) + ', Description: ' + self.description

    class Meta:
        db_table = "ice_feedback"
        # index in favor of Notification screen (pull_recent_notifications,
        # num_of_notifications_for_user)
        index_together = ["user"]


class ApplicationServiceInfrastructure(models.Model):
    name = models.CharField(max_length=100, unique=True)
    uuid = models.CharField(default=uuid.uuid4, max_length=36, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "ice_application_service_infrastructure"
        unique_together = (('name', 'uuid'),)


class VF(models.Model):
    # in favor of dashboard search by keyword
    name = models.CharField(max_length=100, db_index=True)
    # in favor of dashboard search by keyword
    version = models.CharField(max_length=100, db_index=True, null=True)
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, unique=True, primary_key=True)
    # index in favor of getRecentEng, getStarredEng
    engagement = models.OneToOneField(
        Engagement, null=False, blank=False, default=-1, db_index=True)
    deployment_target = models.ForeignKey(
        DeploymentTarget, on_delete=models.SET_NULL, null=True, blank=True)
    ecomp_release = models.ForeignKey(ECOMPRelease, null=True, blank=False)
    deployment_target_sites = models.ManyToManyField(
        DeploymentTargetSite, default=None, blank=True, related_name='DeployTarget_sites')
    is_service_provider_internal = models.BooleanField(default=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    git_repo_url = models.CharField(max_length=512, blank=False, default=-1)
    target_lab_entry_date = models.DateField(
        'target_lab_entry_date', null=False)

    def jenkins_job_name(self):
        if not self.engagement.engagement_manual_id:
            raise ValueError(
                "engagement_manual_id (%s) is not valid for jenkins job name" % self.engagement.engagement_manual_id)
        return "{self.name}_{self.engagement.engagement_manual_id}".format(self=self)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "ice_vf"


class VFC(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, unique=True, primary_key=True)
    vf = models.ForeignKey(VF, on_delete=models.PROTECT, db_index=True)
    # in favor of dashboard search by keyword
    name = models.CharField(max_length=100, db_index=True)
    external_ref_id = models.CharField(max_length=20, default='')
    ice_mandated = models.BooleanField(default=False)
    company = models.ForeignKey(Vendor, on_delete=SET_NULL, null=True)
    create_time = models.DateTimeField('creation time', default=timezone.now)
    creator = models.ForeignKey(
        IceUserProfile, on_delete=models.PROTECT, null=True, blank=True, related_name='Vfc_creator')

    def __str__(self):
        return self.name

    class Meta:
        db_table = "ice_vfc"


class RecentEngagement(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=64, primary_key=True)
    vf = models.ForeignKey(VF, on_delete=models.CASCADE)
    user_uuid = models.CharField(max_length=64)
    action_type = models.CharField(
        max_length=36, choices=RecentEngagementActionType.choices())
    last_update = models.DateTimeField('update time', default=timezone.now)

    def __str__(self):
        return " uuid: " + str(self.uuid)

    class Meta:
        db_table = "ice_recent_engagement"

# _________________________ C H E C K - L I S T __________________________


class ChecklistTemplate(models.Model):  # Reference Table
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, primary_key=True)
    name = models.CharField('template name', max_length=255)
    category = models.CharField(max_length=36, choices=CheckListCategory.choices(
    ), default=CheckListCategory.overall.name)  # @UndefinedVariable
    version = models.IntegerField('template version')
    create_time = models.DateTimeField('creation time', default=timezone.now)
    update_time = models.DateTimeField(
        'last update time', null=True, blank=True)

    def __str__(self):
        return self.name + ' ' + self.category

    class Meta:
        db_table = "ice_checklist_template"


class ChecklistSection(models.Model):  # Reference Table
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, primary_key=True)
    name = models.CharField('section name', max_length=255)
    weight = models.FloatField('checklist weight')
    description = models.TextField('section description')
    validation_instructions = models.TextField(
        'section validation instructions')
    create_time = models.DateTimeField('creation time', default=timezone.now)
    update_time = models.DateTimeField(
        'last update time', null=True, blank=True)
    parent_section = models.ForeignKey("self", null=True, blank=True)
    template = models.ForeignKey(
        ChecklistTemplate, on_delete=models.PROTECT, null=False, blank=False)

    def __str__(self):
        return self.name + ' ' + self.description

    class Meta:
        db_table = "ice_checklist_section"


class ChecklistLineItem(models.Model):  # Reference Table
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, primary_key=True)
    name = models.CharField('line name', max_length=255)
    weight = models.FloatField('line weight')
    description = models.TextField('line description')
    line_type = models.CharField(max_length=36, choices=CheckListLineType.choices(
    ), default=CheckListLineType.auto.name)  # @UndefinedVariable
    validation_instructions = models.TextField('line validation instructions')
    create_time = models.DateTimeField('creation time', default=timezone.now)
    update_time = models.DateTimeField(
        'last update time', null=True, blank=True)
    template = models.ForeignKey(
        ChecklistTemplate, on_delete=models.CASCADE, null=False, blank=False)
    section = models.ForeignKey(
        ChecklistSection, on_delete=models.CASCADE, null=False, blank=False)

    def save(self, *args, **kwargs):
        if (self.template != self.section.template != None):
            raise ValueError("ChecklistLineItem can't be saved/updated since the template " +
                             self.template.name + " is not equal to its section's template " + self.section.template.name)
        super(ChecklistLineItem, self).save(*args, **kwargs)

    def __str__(self):
        return self.name + ' ' + self.description

    class Meta:
        db_table = "ice_checklist_line_item"


class Checklist(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, primary_key=True)
    name = models.CharField('checklist name', max_length=255)
    state = models.CharField(max_length=36, choices=CheckListState.choices(
    ), default=CheckListState.pending.name)  # @UndefinedVariable
    # On each validation cycle this counter is increased
    validation_cycle = models.IntegerField('validation cycle')
    weight = models.FloatField('checklist weight', default=0)
    associated_files = models.TextField('list of files from gitlab')
    create_time = models.DateTimeField('creation time', default=timezone.now)
    update_time = models.DateTimeField(
        'last update time', null=True, blank=True)
    # index in favor of get StarredEngagements (especially for admin and EL)
    engagement = models.ForeignKey(
        Engagement, on_delete=models.CASCADE, db_index=True)
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.PROTECT)
    # The EL that opened the modal.
    creator = models.ForeignKey(
        IceUserProfile, on_delete=models.CASCADE, related_name='checklist_creator')
    # The user who currently validates the checklist
    owner = models.ForeignKey(
        IceUserProfile, on_delete=models.CASCADE, related_name='checklist_owner')

    def __str__(self):
        return self.name + ' ' + self.state

    class Meta:
        db_table = "ice_checklist"


class NextStep(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, primary_key=True)
    create_time = models.DateTimeField('creation time', default=timezone.now)
    creator = models.ForeignKey(
        IceUserProfile, on_delete=models.PROTECT, related_name="NextStep_creator")
    last_update_time = models.DateTimeField(
        'last update time', default=timezone.now)
    last_updater = models.ForeignKey(
        IceUserProfile, on_delete=models.PROTECT, null=True, related_name="NextStep_last_updater")
    # Can be: Modified, Added, Completed, Denied
    last_update_type = models.CharField(max_length=15, default='Added')
    position = models.IntegerField()
    description = models.TextField()
    # Can be: Incomplete, Completed
    state = models.CharField(max_length=15, choices=NextStepState.choices())
    # Can be: Intake, Active, Validated, Completed. This field is used to
    # correlate between the engagement stage to the next step stage in favor
    # of UI.
    engagement_stage = models.CharField(max_length=15)
    engagement = models.ForeignKey(
        Engagement, on_delete=models.PROTECT, null=True, blank=True)
    owner = models.ForeignKey(
        IceUserProfile, on_delete=models.PROTECT, null=True, blank=True)
    next_step_type = models.CharField(max_length=36, choices=NextStepType.choices(
    ), default=NextStepType.user_defined.name)  # @UndefinedVariable
    files = models.TextField('list of files', null=True)
    assignees = models.ManyToManyField(
        IceUserProfile, related_name='assignees')
    due_date = models.DateField('due_date', null=True)

    def __str__(self):
        return self.engagement_stage + ' ' + self.state + ' ' + self.description

    class Meta:
        db_table = "ice_next_step"
        verbose_name_plural = 'Next steps'
        # index in favor of nextstep_service.get_next_steps
        index_together = ["engagement_stage", "owner"]


class ChecklistDecision(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, primary_key=True)
    review_value = models.CharField(
        max_length=36, choices=CheckListDecisionValue.choices())  # @UndefinedVariable
    peer_review_value = models.CharField(
        max_length=36, choices=CheckListDecisionValue.choices())  # @UndefinedVariable
    create_time = models.DateTimeField('creation time', default=timezone.now)
    update_time = models.DateTimeField(
        'last update time', null=True, blank=True)
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE)
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE)
    lineitem = models.ForeignKey(ChecklistLineItem, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if (self.template != self.checklist.template != None):
            raise ValueError("ChecklistDecision can't be saved/updated since the template " +
                             self.template.name + " is not equal to its checklist's template " + self.checklist.template.name)
        if (self.template != self.lineitem.section.template != None):
            raise ValueError("ChecklistDecision can't be saved/updated since the template " + self.template.name +
                             " is not equal to its lineitem/section's template " + self.lineitem.section.template)
        if (self.checklist.template != self.lineitem.section.template != None):
            raise ValueError("ChecklistDecision can't be saved/updated since its checklist's template " +
                             self.checklist.template + " is not equal to its lineitem/section's template " + self.lineitem.section.template)
        super(ChecklistDecision, self).save(*args, **kwargs)

    def __str__(self):
        return 'decision:' + self.uuid + ' ' + self.template.name + ' ' + self.review_value + ' ' + self.peer_review_value

    class Meta:
        db_table = "ice_checklist_decision"


class ChecklistAuditLog(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, primary_key=True)
    category = models.CharField(max_length=255)
    description = models.TextField()
    create_time = models.DateTimeField('creation time', default=timezone.now)
    update_time = models.DateTimeField(
        'last update time', null=True, blank=True)
    creator = models.ForeignKey(IceUserProfile)
    # should be None if decisions is populated
    checklist = models.ForeignKey(
        Checklist, on_delete=models.CASCADE, null=True, blank=True)
    # should be None if checklist is populated
    decision = models.ForeignKey(
        ChecklistDecision, on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        if (self.checklist != None and self.decision != None):
            raise ValueError(
                "ChecklistAuditLog can't be attached to both checklist and decision. Please remove one of them and retry the operation")
        super(ChecklistAuditLog, self).save(*args, **kwargs)

    def __str__(self):
        return self.category + ' ' + self.description

    class Meta:
        db_table = "ice_checklist_audit_log"


class Invitation(models.Model):
    uuid = models.CharField(
        default=uuid.uuid4, max_length=36, primary_key=True)
    engagement_uuid = models.CharField(
        max_length=64, null=False, blank=False, db_index=True)
    invited_by_user_uuid = models.CharField(
        max_length=64, null=False, blank=False, db_index=True)
    email = models.CharField(max_length=255, null=False, blank=False)
    invitation_token = models.CharField(
        max_length=1024, null=False, blank=False, db_index=True)  # index in favor of signup
    accepted = models.BooleanField(default=False)
    create_time = models.DateTimeField(
        'invitation creation time', default=timezone.now)

    def __str__(self):
        return "Invite from " + self.invited_by_user_uuid + " to " + self.email + " for joining engagement " + self.engagement_uuid

    class Meta:
        db_table = "ice_invitation"
        unique_together = (("engagement_uuid", "email"),)
