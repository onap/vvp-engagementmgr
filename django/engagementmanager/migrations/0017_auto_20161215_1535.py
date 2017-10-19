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
# Generated by Django 1.9.7 on 2016-12-15 13:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('engagementmanager', '0016_auto_20161208_0842'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('uuid', models.CharField(max_length=36, primary_key=True, serialize=False)),
                ('engagement_uuid', models.CharField(db_index=True, max_length=64)),
                ('invited_by_user_uuid', models.CharField(db_index=True, max_length=64)),
                ('email', models.CharField(max_length=255)),
                ('invitation_token', models.CharField(max_length=1024)),
                ('accepted', models.BooleanField(default=False)),
                ('create_time', models.DateTimeField(
                    default=django.utils.timezone.now, verbose_name='invitation creation time')),
            ],
            options={
                'db_table': 'ice_invitation',
            },
        ),
        migrations.AlterUniqueTogether(
            name='invitation',
            unique_together=set([('engagement_uuid', 'email')]),
        ),
    ]