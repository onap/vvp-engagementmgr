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
# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-13 14:07
from __future__ import unicode_literals

import datetime

from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('uuid', models.CharField(max_length=36, primary_key=True, serialize=False, unique=True)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('description', models.CharField(max_length=512)),
                ('is_notification', models.BooleanField(default=False)),
                ('activity_type', models.CharField(choices=[
                 (b'3', b'eng_validation_request'), (b'4', b'next_steps'), (b'2', b'ssh_key_added'), (b'1', b'user_joined_eng')], max_length=36)),
                ('metadata', models.CharField(max_length=1024)),
            ],
            options={
                'ordering': ['-create_time'],
                'db_table': 'ice_activity',
            },
        ),
        migrations.CreateModel(
            name='ApplicationServiceInfrastructure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('uuid', models.CharField(max_length=36, unique=True)),
            ],
            options={
                'db_table': 'ice_application_service_infrastructure',
            },
        ),
        migrations.CreateModel(
            name='ContactRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('uuid', models.CharField(max_length=36, unique=True)),
                ('fname', models.CharField(max_length=50)),
                ('lname', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254, verbose_name='email')),
                ('company', models.CharField(max_length=50)),
                ('phone_number', models.CharField(max_length=30)),
                ('message', models.TextField()),
            ],
            options={
                'db_table': 'ice_contact_request',
            },
        ),
        migrations.CreateModel(
            name='DeploymentTarget',
            fields=[
                ('uuid', models.CharField(max_length=36, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=45)),
                ('version', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'ice_deployment_target',
            },
        ),
        migrations.CreateModel(
            name='Engagement',
            fields=[
                ('uuid', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('engagement_manual_id', models.CharField(blank=True, max_length=36, null=True)),
                ('progress', models.IntegerField(default=0)),
                ('target_completion_date', models.DateField(blank=True, default=datetime.datetime(
                    2016, 6, 29, 14, 7, 41, 103000, tzinfo=utc), null=True)),
                ('engagement_stage', models.CharField(default=b'Intake', max_length=15)),
            ],
            options={
                'db_table': 'ice_engagement',
            },
        ),
        migrations.CreateModel(
            name='EngagementRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('uuid', models.CharField(max_length=36, unique=True)),
                ('fname', models.CharField(max_length=50)),
                ('lname', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254, verbose_name='email')),
                ('company', models.CharField(max_length=50)),
                ('country_code', models.CharField(max_length=5)),
                ('phone_number', models.CharField(max_length=30)),
                ('vf_csv', models.CharField(max_length=80)),
                ('att_contact_fname', models.CharField(max_length=50)),
                ('att_contact_lname', models.CharField(max_length=50)),
                ('att_contact_email', models.EmailField(max_length=254, verbose_name='email')),
                ('att_contact_phone', models.CharField(max_length=30)),
                ('request_type', models.CharField(max_length=20)),
                ('description', models.TextField()),
                ('mail_subscription', models.BooleanField()),
            ],
            options={
                'db_table': 'ice_engagement_request',
            },
        ),
        migrations.CreateModel(
            name='IceUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=36, unique=True)),
                ('phone_number', models.CharField(max_length=30)),
                ('full_name', models.CharField(max_length=30)),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email')),
                ('password', models.CharField(max_length=256)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last_login')),
                ('ssh_public_key', models.CharField(
                    blank=True, max_length=1024, null=True, verbose_name='ssh_public_key')),
                ('regular_email_updates', models.BooleanField(default=False)),
                ('email_updates_on_every_notification', models.BooleanField(default=True)),
                ('email_updates_daily_digest', models.BooleanField(default=False)),
                ('is_active', models.BooleanField()),
                ('is_att_contact', models.BooleanField()),
                ('activation_token', models.CharField(max_length=128, unique=True)),
                ('activation_token_create_time', models.DateTimeField(
                    default=django.utils.timezone.now, verbose_name='activation_token_create_time')),
            ],
            options={
                'db_table': 'ice_user',
            },
        ),
        migrations.CreateModel(
            name='NextStep',
            fields=[
                ('uuid', models.CharField(max_length=36, primary_key=True, serialize=False)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation time')),
                ('last_update_time', models.DateTimeField(
                    default=django.utils.timezone.now, verbose_name='last update time')),
                ('last_update_type', models.CharField(default='Added', max_length=15)),
                ('position', models.IntegerField()),
                ('description', models.TextField()),
                ('state', models.CharField(max_length=15)),
                ('engagement_stage', models.CharField(max_length=15)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                              related_name='NextStep_creator', to='engagementmanager.IceUser')),
                ('engagement', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Engagement')),
                ('last_updater', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT,
                                                   related_name='NextStep_last_updater', to='engagementmanager.IceUser')),
            ],
            options={
                'db_table': 'ice_next_step',
                'verbose_name_plural': 'Next steps',
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('uuid', models.CharField(max_length=36, primary_key=True, serialize=False, unique=True)),
                ('is_sent', models.BooleanField(default=False)),
                ('is_read', models.BooleanField(default=False)),
                ('activity', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.Activity')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.IceUser')),
            ],
            options={
                'db_table': 'ice_notification',
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=36, unique=True)),
                ('name', models.CharField(max_length=36, unique=True)),
            ],
            options={
                'db_table': 'ice_role',
            },
        ),
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=45)),
                ('uuid', models.CharField(max_length=36, unique=True)),
            ],
            options={
                'db_table': 'ice_test',
            },
        ),
        migrations.CreateModel(
            name='ValidationCycle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=36, unique=True)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('validated_by', models.CharField(max_length=45)),
                ('validated_at', models.DateTimeField()),
                ('peer_reviewer', models.CharField(max_length=45)),
                ('peer_reviewed_at', models.DateTimeField()),
                ('package_uuid', models.CharField(max_length=45)),
                ('package_cksum', models.CharField(max_length=45)),
                ('package_approval_date', models.DateTimeField()),
                ('package_approver', models.CharField(max_length=45)),
                ('image_uuid', models.CharField(max_length=45)),
                ('image_name', models.CharField(max_length=100)),
                ('image_cksum', models.CharField(max_length=100)),
                ('passed', models.BooleanField()),
            ],
            options={
                'db_table': 'ice_validation_cycle',
            },
        ),
        migrations.CreateModel(
            name='ValidationException',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=36, unique=True)),
                ('type', models.CharField(max_length=45)),
                ('external_ref_id', models.CharField(max_length=45)),
            ],
            options={
                'db_table': 'ice_validation_exception',
            },
        ),
        migrations.CreateModel(
            name='ValidationSteps',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=36)),
                ('requirment_id', models.CharField(blank=True, max_length=36, null=True)),
                ('passed', models.BooleanField()),
                ('log', models.BinaryField()),
                ('validation_notes', models.CharField(blank=True, max_length=200, null=True)),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Test')),
                ('validation_cycle', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.ValidationCycle')),
                ('validation_exceptions', models.ManyToManyField(to='engagementmanager.ValidationException')),
            ],
            options={
                'db_table': 'ice_validation_step',
                'verbose_name_plural': 'Validation steps',
            },
        ),
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=36, unique=True)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'db_table': 'ice_vendor',
            },
        ),
        migrations.CreateModel(
            name='VF',
            fields=[
                ('name', models.CharField(max_length=100)),
                ('uuid', models.CharField(max_length=36, primary_key=True, serialize=False, unique=True)),
                ('is_att_internal', models.BooleanField(default=False)),
                ('git_repo_url', models.CharField(blank=True, max_length=512, null=True)),
                ('target_lab_entry_date', models.DateField(verbose_name='target_lab_entry_date')),
                ('deployment_target', models.ForeignKey(blank=True, null=True,
                                                        on_delete=django.db.models.deletion.SET_NULL, to='engagementmanager.DeploymentTarget')),
                ('engagement', models.ForeignKey(blank=True, null=True,
                                                 on_delete=django.db.models.deletion.SET_NULL, to='engagementmanager.Engagement')),
                ('vendor', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Vendor')),
            ],
            options={
                'db_table': 'ice_vf',
            },
        ),
        migrations.CreateModel(
            name='VFC',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=45)),
                ('version', models.CharField(max_length=45)),
                ('uuid', models.CharField(max_length=36, unique=True)),
                ('vf_acronym', models.CharField(blank=True, max_length=100, null=True)),
                ('vf', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.VF')),
            ],
            options={
                'db_table': 'ice_vfc',
            },
        ),
        migrations.AlterUniqueTogether(
            name='validationexception',
            unique_together=set([('uuid', 'type')]),
        ),
        migrations.AddField(
            model_name='validationcycle',
            name='vfc',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.VFC'),
        ),
        migrations.AddField(
            model_name='iceuser',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Vendor'),
        ),
        migrations.AddField(
            model_name='iceuser',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Role'),
        ),
        migrations.AddField(
            model_name='engagement',
            name='contact_user',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.IceUser'),
        ),
        migrations.AddField(
            model_name='engagement',
            name='engagement_team',
            field=models.ManyToManyField(related_name='members', to='engagementmanager.IceUser'),
        ),
        migrations.AlterUniqueTogether(
            name='deploymenttarget',
            unique_together=set([('name', 'version')]),
        ),
        migrations.AlterUniqueTogether(
            name='applicationserviceinfrastructure',
            unique_together=set([('name', 'uuid')]),
        ),
        migrations.AddField(
            model_name='activity',
            name='activity_owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='engagementmanager.IceUser'),
        ),
        migrations.AddField(
            model_name='activity',
            name='engagement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='engagementmanager.Engagement'),
        ),
        migrations.AlterUniqueTogether(
            name='vfc',
            unique_together=set([('name', 'version')]),
        ),
        migrations.AlterUniqueTogether(
            name='validationsteps',
            unique_together=set([('uuid', 'requirment_id')]),
        ),
    ]