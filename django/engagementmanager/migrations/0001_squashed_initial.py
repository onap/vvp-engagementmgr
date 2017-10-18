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
from django.conf import settings
import django.contrib.auth.models
from django.db import models
import django.db.models.deletion
from django.utils.timezone import utc
import django.utils.timezone
import engagementmanager.models
import uuid
import os
from django.db import migrations, connection
import engagementmanager
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def forwards(apps, schema_editor):
    if not schema_editor.connection.alias == 'default' \
            or settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
        return

    cursor = connection.cursor()
    cursor.execute(open(os.path.join(os.path.dirname(engagementmanager.__file__),
                                     'sql-scripts/generate_excel_overview_sheet_procedure.sql'), "r").read())


def create_user_for_pre_user_profiles(apps, schema_editor):
    CustomUser = apps.get_model("engagementmanager", "CustomUser")
    IceUserProfile = apps.get_model("engagementmanager", "IceUserProfile")
    users_list = IceUserProfile.objects.filter(user=None)
    count = 0
    for profile in users_list:
        try:
            custom_user, created = CustomUser.objects.get_or_create(username=profile.email)
            custom_user.is_active = profile.is_active
            custom_user.email = profile.email
            custom_user.activation_token = profile.activation_token
            custom_user.password = profile.password
            custom_user.activation_token_create_time = profile.activation_token_create_time
            custom_user.save()
            profile.user = custom_user
            profile.save()

        except Exception as e:
            logger.error("migrations fail, error:")
            logger.error(e.message)


class Migration(migrations.Migration):
    replaces = [('engagementmanager', '0001_initial'), ('engagementmanager', '0002_auto_20160704_1028'),
                ('engagementmanager', '0003_auto_20160713_0929'), ('engagementmanager', '0004_auto_20160720_2143'),
                ('engagementmanager', '0005_auto_20160815_1248'), ('engagementmanager', '0006_auto_20160825_0644'),
                ('engagementmanager', '0007_auto_20160922_0421'), ('engagementmanager', '0008_auto_20161009_1210'),
                ('engagementmanager', '0009_auto_20161018_0740'), ('engagementmanager', '0010_auto_20161025_0838'),
                ('engagementmanager', '0011_auto_20161109_0811'), ('engagementmanager', '0012_auto_20161109_0822'),
                ('engagementmanager', '0013_auto_20161128_1159'), ('engagementmanager', '0014_auto_20161129_1145'),
                ('engagementmanager', '0015_engagementstatus'), ('engagementmanager', '0016_auto_20161208_0842'),
                ('engagementmanager', '0017_auto_20161215_1535'), ('engagementmanager', '0018_set_old_notif_true'),
                ('engagementmanager', '0019_auto_20170104_1715'), ('engagementmanager', '0020_add_indexes_20170108'),
                ('engagementmanager', '0021_generate_excel_overview_sheet_procedure_20170110'),
                ('engagementmanager', '0022_auto_20170118_1520'), ('engagementmanager', '0023_auto_20170123_1445'),
                ('engagementmanager', '0024_auto_20170227_1224'),
                ('engagementmanager', '0025_change_nextsteps_to_new_state'),
                ('engagementmanager', '0026_add_slack_handle_to_ice_user_profile'),
                ('engagementmanager', '0027_add_version_to_vf'), ('engagementmanager', '0028_auto_20170425_1310'),
                ('engagementmanager', '0029_auto_20170504_0749'),
                ('engagementmanager', '0030_engagement_archived_time'),
                ('engagementmanager', '0031_auto_20170620_1312'), ('engagementmanager', '0032_auto_20170702_1435'),
                ('engagementmanager', '0033_auto_20170704_0635'),
                ('engagementmanager', '0034_engagement_is_with_files'), ('engagementmanager', '0035_rgwa_fields'),
                ('engagementmanager', '0036_auto_20170906_0935')]

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('description', models.CharField(max_length=512)),
                ('is_notification', models.BooleanField(default=False)),
                ('activity_type', models.CharField(choices=[('user_joined_eng', 'user_joined_eng'), ('ssh_key_added', 'ssh_key_added'), ('eng_validation_request', 'eng_validation_request'), ('update_next_steps', 'update_next_steps'), ('vfc', 'vfc'), ('change_checklist_state', 'change_checklist_state'), ('vf_provisioning_event', 'vf_provisioning_event'), ('test_finished_event', 'test_finished_event'), ('change_engagement_stage', 'change_engagement_stage'), ('add_next_steps', 'add_next_steps'), ('delete_next_steps', 'delete_next_steps'), ('notice_empty_engagement', 'notice_empty_engagement')], max_length=36)),
                ('metadata', models.CharField(max_length=1024)),
            ],
            options={
                'db_table': 'ice_activity',
                'ordering': ['-create_time'],
            },
        ),
        migrations.CreateModel(
            name='ApplicationServiceInfrastructure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, unique=True)),
            ],
            options={
                'db_table': 'ice_application_service_infrastructure',
            },
        ),
        migrations.CreateModel(
            name='Checklist',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='checklist name')),
                ('state', models.CharField(choices=[('automation', 'automation'), ('review', 'review'), ('peer_review', 'peer_review'), ('approval', 'approval'), ('handoff', 'handoff'), ('closed', 'closed'), ('archive', 'archive'), ('pending', 'pending')], default='pending', max_length=36)),
                ('validation_cycle', models.IntegerField(verbose_name='validation cycle')),
                ('weight', models.FloatField(default=0, verbose_name='checklist weight')),
                ('associated_files', models.TextField(verbose_name='list of files from gitlab')),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('update_time', models.DateTimeField(blank=True, null=True, verbose_name='last update time')),
            ],
            options={
                'db_table': 'ice_checklist',
            },
        ),
        migrations.CreateModel(
            name='ChecklistAuditLog',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('category', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('update_time', models.DateTimeField(blank=True, null=True, verbose_name='last update time')),
                ('checklist', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.Checklist')),
            ],
            options={
                'db_table': 'ice_checklist_audit_log',
            },
        ),
        migrations.CreateModel(
            name='ChecklistDecision',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('review_value', models.CharField(choices=[('approved', 'approved'), ('denied', 'denied'), ('not_relevant', 'not_relevant'), ('na', 'na')], max_length=36)),
                ('peer_review_value', models.CharField(choices=[('approved', 'approved'), ('denied', 'denied'), ('not_relevant', 'not_relevant'), ('na', 'na')], max_length=36)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('update_time', models.DateTimeField(blank=True, null=True, verbose_name='last update time')),
                ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.Checklist')),
            ],
            options={
                'db_table': 'ice_checklist_decision',
            },
        ),
        migrations.CreateModel(
            name='ChecklistLineItem',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='line name')),
                ('weight', models.FloatField(verbose_name='line weight')),
                ('description', models.TextField(verbose_name='line description')),
                ('line_type', models.CharField(choices=[('auto', 'auto'), ('manual', 'manual')], default='auto', max_length=36)),
                ('validation_instructions', models.TextField(verbose_name='line validation instructions')),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('update_time', models.DateTimeField(blank=True, null=True, verbose_name='last update time')),
            ],
            options={
                'db_table': 'ice_checklist_line_item',
            },
        ),
        migrations.CreateModel(
            name='ChecklistSection',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='section name')),
                ('weight', models.FloatField(verbose_name='checklist weight')),
                ('description', models.TextField(verbose_name='section description')),
                ('validation_instructions', models.TextField(verbose_name='section validation instructions')),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('update_time', models.DateTimeField(blank=True, null=True, verbose_name='last update time')),
                ('parent_section', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.ChecklistSection')),
            ],
            options={
                'db_table': 'ice_checklist_section',
            },
        ),
        migrations.CreateModel(
            name='ChecklistTemplate',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='template name')),
                ('category', models.CharField(choices=[('overall', 'overall'), ('heat', 'heat'), ('glance', 'glance'), ('instantiation', 'instantiation'), ('asdc', 'asdc')], default='overall', max_length=36)),
                ('version', models.IntegerField(verbose_name='template version')),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('update_time', models.DateTimeField(blank=True, null=True, verbose_name='last update time')),
            ],
            options={
                'db_table': 'ice_checklist_template',
            },
        ),
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('activation_token', models.CharField(max_length=128, null=True, unique=True)),
                ('activation_token_create_time', models.DateTimeField(default=django.utils.timezone.now, null=True, verbose_name='activation_token_create_time')),
                ('temp_password', models.CharField(blank=True, default=None, max_length=256, null=True)),
            ],
            options={
                'db_table': 'ice_custom_user',
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='DeploymentTarget',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=45)),
                ('version', models.CharField(max_length=100)),
                ('weight', models.IntegerField(default=1)),
                ('ui_visibility', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'ice_deployment_target',
            },
        ),
        migrations.CreateModel(
            name='DeploymentTargetSite',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=45)),
            ],
            options={
                'db_table': 'ice_deployment_target_site',
            },
        ),
        migrations.CreateModel(
            name='ECOMPRelease',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=45)),
                ('weight', models.IntegerField(default=1)),
                ('ui_visibility', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'ice_ecomp_release',
            },
        ),
        migrations.CreateModel(
            name='Engagement',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=64, primary_key=True, serialize=False)),
                ('engagement_manual_id', models.CharField(db_index=True, default=-1, max_length=36)),
                ('progress', models.IntegerField(default=0)),
                ('target_completion_date', models.DateField(blank=True, default=engagementmanager.models.get_default_target_completion_date, null=True)),
                ('engagement_stage', models.CharField(choices=[('Intake', 'Intake'), ('Active', 'Active'), ('Validated', 'Validated'), ('Completed', 'Completed'), ('Archived', 'Archived')], db_index=True, default='Intake', max_length=15)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('heat_validated_time', models.DateTimeField(blank=True, null=True, verbose_name='heat validated time')),
                ('image_scan_time', models.DateTimeField(blank=True, null=True, verbose_name='image scan time')),
                ('aic_instantiation_time', models.DateTimeField(blank=True, null=True, verbose_name='aic instantiation time')),
                ('asdc_onboarding_time', models.DateTimeField(blank=True, null=True, verbose_name='asdc onboarding time')),
                ('started_state_time', models.DateTimeField(blank=True, null=True, verbose_name='started state time')),
                ('intake_time', models.DateTimeField(blank=True, null=True, verbose_name='intake time')),
                ('active_time', models.DateTimeField(blank=True, null=True, verbose_name='active time')),
                ('validated_time', models.DateTimeField(blank=True, null=True, verbose_name='validated time')),
                ('completed_time', models.DateTimeField(blank=True, null=True, verbose_name='completed time')),
                ('archive_reason', models.TextField(default=None, null=True)),
                ('archived_time', models.DateTimeField(blank=True, null=True, verbose_name='archived time')),
                ('is_with_files', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'ice_engagement',
            },
        ),
        migrations.CreateModel(
            name='EngagementStatus',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=64, primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=256)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'ice_engagement_status',
            },
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('description', models.TextField(verbose_name='feedback_description')),
            ],
            options={
                'db_table': 'ice_feedback',
            },
        ),
        migrations.CreateModel(
            name='IceUserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, unique=True)),
                ('phone_number', models.CharField(max_length=30)),
                ('full_name', models.CharField(max_length=30)),
                ('email', models.EmailField(db_index=True, max_length=254, unique=True, verbose_name='email')),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('ssh_public_key', models.CharField(blank=True, max_length=1024, null=True, verbose_name='ssh_public_key')),
                ('regular_email_updates', models.BooleanField(default=False)),
                ('email_updates_on_every_notification', models.BooleanField(default=True)),
                ('email_updates_daily_digest', models.BooleanField(default=False)),
                ('is_service_provider_contact', models.BooleanField(default=False)),
                ('rgwa_access_key', models.CharField(blank=True, max_length=1024, null=True, unique=True)),
                ('rgwa_secret_key', models.CharField(blank=True, max_length=1024, null=True, unique=True)),
                ('slack_handle', models.CharField(blank=True, default=None, max_length=64, null=True)),
            ],
            options={
                'db_table': 'ice_user_profile',
            },
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('engagement_uuid', models.CharField(db_index=True, max_length=64)),
                ('invited_by_user_uuid', models.CharField(db_index=True, max_length=64)),
                ('email', models.CharField(max_length=255)),
                ('invitation_token', models.CharField(db_index=True, max_length=1024)),
                ('accepted', models.BooleanField(default=False)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='invitation creation time')),
            ],
            options={
                'db_table': 'ice_invitation',
            },
        ),
        migrations.CreateModel(
            name='NextStep',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('last_update_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last update time')),
                ('last_update_type', models.CharField(default='Added', max_length=15)),
                ('position', models.IntegerField()),
                ('description', models.TextField()),
                ('state', models.CharField(choices=[('Incomplete', 'Incomplete'), ('Completed', 'Completed')], max_length=15)),
                ('engagement_stage', models.CharField(max_length=15)),
                ('next_step_type', models.CharField(choices=[('set_ssh', 'set_ssh'), ('trial_agreements', 'trial_agreements'), ('add_contact_person', 'add_contact_person'), ('submit_vf_package', 'submit_vf_package'), ('el_handoff', 'el_handoff'), ('user_defined', 'user_defined')], default='user_defined', max_length=36)),
                ('files', models.TextField(null=True, verbose_name='list of files')),
                ('due_date', models.DateField(null=True, verbose_name='due_date')),
                ('assignees', models.ManyToManyField(related_name='assignees', to='engagementmanager.IceUserProfile')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='NextStep_creator', to='engagementmanager.IceUserProfile')),
                ('engagement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Engagement')),
                ('last_updater', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='NextStep_last_updater', to='engagementmanager.IceUserProfile')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.IceUserProfile')),
            ],
            options={
                'verbose_name_plural': 'Next steps',
                'db_table': 'ice_next_step',
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('is_sent', models.BooleanField(default=False)),
                ('is_read', models.BooleanField(default=False)),
                ('activity', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.Activity')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.IceUserProfile')),
            ],
            options={
                'db_table': 'ice_notification',
            },
        ),
        migrations.CreateModel(
            name='RecentEngagement',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=64, primary_key=True, serialize=False)),
                ('user_uuid', models.CharField(max_length=64)),
                ('action_type', models.CharField(choices=[('JOINED_TO_ENGAGEMENT', 'JOINED_TO_ENGAGEMENT'), ('NEXT_STEP_ASSIGNED', 'NEXT_STEP_ASSIGNED'), ('GOT_OWNERSHIP_OVER_ENGAGEMENT', 'GOT_OWNERSHIP_OVER_ENGAGEMENT'), ('NAVIGATED_INTO_ENGAGEMENT', 'NAVIGATED_INTO_ENGAGEMENT'), ('NEW_VF_CREATED', 'NEW_VF_CREATED')], max_length=36)),
                ('last_update', models.DateTimeField(default=django.utils.timezone.now, verbose_name='update time')),
            ],
            options={
                'db_table': 'ice_recent_engagement',
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, unique=True)),
                ('name', models.CharField(max_length=36, unique=True)),
            ],
            options={
                'db_table': 'ice_role',
            },
        ),
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, unique=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('public', models.BooleanField()),
            ],
            options={
                'db_table': 'ice_vendor',
            },
        ),
        migrations.CreateModel(
            name='VF',
            fields=[
                ('name', models.CharField(db_index=True, max_length=100)),
                ('version', models.CharField(db_index=True, max_length=100, null=True)),
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('is_service_provider_internal', models.BooleanField(default=False)),
                ('git_repo_url', models.CharField(default=-1, max_length=512)),
                ('target_lab_entry_date', models.DateField(verbose_name='target_lab_entry_date')),
                ('deployment_target', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='engagementmanager.DeploymentTarget')),
                ('deployment_target_sites', models.ManyToManyField(blank=True, default=None, related_name='DeployTarget_sites', to='engagementmanager.DeploymentTargetSite')),
                ('ecomp_release', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.ECOMPRelease')),
                ('engagement', models.OneToOneField(default=-1, on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.Engagement')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Vendor')),
            ],
            options={
                'db_table': 'ice_vf',
            },
        ),
        migrations.CreateModel(
            name='VFC',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('external_ref_id', models.CharField(default='', max_length=20)),
                ('ice_mandated', models.BooleanField(default=False)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('company', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='engagementmanager.Vendor')),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='Vfc_creator', to='engagementmanager.IceUserProfile')),
                ('vf', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.VF')),
            ],
            options={
                'db_table': 'ice_vfc',
            },
        ),
        migrations.AddField(
            model_name='recentengagement',
            name='vf',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.VF'),
        ),
        migrations.AlterUniqueTogether(
            name='invitation',
            unique_together=set([('engagement_uuid', 'email')]),
        ),
        migrations.AddField(
            model_name='iceuserprofile',
            name='company',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Vendor'),
        ),
        migrations.AddField(
            model_name='iceuserprofile',
            name='role',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Role'),
        ),
        migrations.AddField(
            model_name='iceuserprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.CustomUser'),
        ),
        migrations.AddField(
            model_name='feedback',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.IceUserProfile'),
        ),
        migrations.AddField(
            model_name='engagementstatus',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='status_creator', to='engagementmanager.IceUserProfile'),
        ),
        migrations.AddField(
            model_name='engagementstatus',
            name='engagement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Engagement'),
        ),
        migrations.AddField(
            model_name='engagement',
            name='contact_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='Engagement_contact_user', to='engagementmanager.IceUserProfile'),
        ),
        migrations.AddField(
            model_name='engagement',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='Engagement_creator', to='engagementmanager.IceUserProfile'),
        ),
        migrations.AddField(
            model_name='engagement',
            name='engagement_team',
            field=models.ManyToManyField(related_name='members', to='engagementmanager.IceUserProfile'),
        ),
        migrations.AddField(
            model_name='engagement',
            name='peer_reviewer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='Engagement_peer_reviewer', to='engagementmanager.IceUserProfile'),
        ),
        migrations.AddField(
            model_name='engagement',
            name='reviewer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='Engagement_el_reviewer', to='engagementmanager.IceUserProfile'),
        ),
        migrations.AddField(
            model_name='engagement',
            name='starred_engagement',
            field=models.ManyToManyField(blank=True, default=None, to='engagementmanager.IceUserProfile'),
        ),
        migrations.AlterUniqueTogether(
            name='deploymenttarget',
            unique_together=set([('name', 'version')]),
        ),
        migrations.AddField(
            model_name='checklistsection',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.ChecklistTemplate'),
        ),
        migrations.AddField(
            model_name='checklistlineitem',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.ChecklistSection'),
        ),
        migrations.AddField(
            model_name='checklistlineitem',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.ChecklistTemplate'),
        ),
        migrations.AddField(
            model_name='checklistdecision',
            name='lineitem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.ChecklistLineItem'),
        ),
        migrations.AddField(
            model_name='checklistdecision',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.ChecklistTemplate'),
        ),
        migrations.AddField(
            model_name='checklistauditlog',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.IceUserProfile'),
        ),
        migrations.AddField(
            model_name='checklistauditlog',
            name='decision',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.ChecklistDecision'),
        ),
        migrations.AddField(
            model_name='checklist',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist_creator', to='engagementmanager.IceUserProfile'),
        ),
        migrations.AddField(
            model_name='checklist',
            name='engagement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.Engagement'),
        ),
        migrations.AddField(
            model_name='checklist',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist_owner', to='engagementmanager.IceUserProfile'),
        ),
        migrations.AddField(
            model_name='checklist',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.ChecklistTemplate'),
        ),
        migrations.AlterUniqueTogether(
            name='applicationserviceinfrastructure',
            unique_together=set([('name', 'uuid')]),
        ),
        migrations.AddField(
            model_name='activity',
            name='activity_owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.IceUserProfile'),
        ),
        migrations.AddField(
            model_name='activity',
            name='engagement',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Engagement'),
        ),
        migrations.AlterIndexTogether(
            name='notification',
            index_together=set([('user', 'is_read')]),
        ),
        migrations.AlterIndexTogether(
            name='nextstep',
            index_together=set([('engagement_stage', 'owner')]),
        ),
        migrations.AlterIndexTogether(
            name='feedback',
            index_together=set([('user',)]),
        ),
        migrations.AlterIndexTogether(
            name='activity',
            index_together=set([('engagement', 'activity_owner')]),
        ),
        migrations.RunPython(forwards),
        migrations.RunPython(create_user_for_pre_user_profiles),
    ]
