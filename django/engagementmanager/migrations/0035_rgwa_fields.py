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
# Generated by Django 1.10.6 on 2017-07-25 07:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('engagementmanager', '0034_engagement_is_with_files'),
    ]

    operations = [
        migrations.AddField(
            model_name='iceuserprofile',
            name='rgwa_access_key',
            field=models.CharField(
                blank=True,
                max_length=1024,
                null=True,
                unique=True),
        ),
        migrations.AddField(
            model_name='iceuserprofile',
            name='rgwa_secret_key',
            field=models.CharField(
                blank=True,
                max_length=1024,
                null=True,
                unique=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='activity_type',
            field=models.CharField(
                choices=[
                    ('user_joined_eng',
                     'user_joined_eng'),
                    ('ssh_key_added',
                     'ssh_key_added'),
                    ('eng_validation_request',
                     'eng_validation_request'),
                    ('update_next_steps',
                     'update_next_steps'),
                    ('vfc',
                     'vfc'),
                    ('change_checklist_state',
                     'change_checklist_state'),
                    ('vf_provisioning_event',
                     'vf_provisioning_event'),
                    ('test_finished_event',
                     'test_finished_event'),
                    ('change_engagement_stage',
                     'change_engagement_stage'),
                    ('add_next_steps',
                     'add_next_steps'),
                    ('delete_next_steps',
                     'delete_next_steps'),
                    ('notice_empty_engagement',
                     'notice_empty_engagement')],
                max_length=36),
        ),
    ]
