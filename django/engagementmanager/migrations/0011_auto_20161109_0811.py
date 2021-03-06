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
# Generated by Django 1.9.7 on 2016-11-09 08:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('engagementmanager', '0010_auto_20161025_0838'),
    ]

    operations = [
        migrations.AlterField(
            model_name='engagement',
            name='engagement_manual_id',
            field=models.CharField(
                max_length=36),
        ),
        migrations.AlterField(
            model_name='engagement',
            name='starred_engagement',
            field=models.ManyToManyField(
                blank=True,
                default=None,
                to='engagementmanager.IceUser'),
        ),
        migrations.AlterField(
            model_name='vf',
            name='ecomp_release',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='engagementmanager.ECOMPRelease'),
        ),
        migrations.AlterField(
            model_name='vf',
            name='engagement',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='engagementmanager.Engagement'),
        ),
        migrations.AlterField(
            model_name='vf',
            name='git_repo_url',
            field=models.CharField(
                default='',
                max_length=512),
            preserve_default=False,
        ),
    ]
