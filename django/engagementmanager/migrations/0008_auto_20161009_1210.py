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
# Generated by Django 1.9.7 on 2016-10-09 12:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('engagementmanager', '0007_auto_20160922_0421'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecentEngagement',
            fields=[
                ('uuid', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('user_uuid', models.CharField(max_length=64)),
                ('action_type', models.CharField(choices=[(b'(3,)', b'GOT_OWNERSHIP_OVER_ENGAGEMENT'), (b'(1,)', b'JOINED_TO_ENGAGEMENT'), (
                    b'(4,)', b'NAVIGATED_INTO_ENGAGEMENT'), (b'(2,)', b'NEXT_STEP_ASSIGNED')], max_length=36)),
                ('last_update', models.DateTimeField(default=django.utils.timezone.now, verbose_name='update time')),
                ('vf', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.VF')),
            ],
            options={
                'db_table': 'ice_recent_engagement',
            },
        ),
        migrations.AddField(
            model_name='engagement',
            name='starred_engagement',
            field=models.ManyToManyField(to='engagementmanager.IceUser'),
        ),
    ]