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
# Generated by Django 1.9.7 on 2016-10-10 08:49
from __future__ import unicode_literals

import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('engagementmanager', '0007_auto_20160922_0421'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActiveJob',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('url', models.URLField(
                    help_text=b'            The jenkins job URL, which should uniquely identify one\n            execution of the TestEngine.')),
                ('checklist', models.ForeignKey(help_text=b'            The checklist associated with this job.',
                                                on_delete=django.db.models.deletion.CASCADE, to='engagementmanager.Checklist')),
            ],
            options={
                'db_table': 'ice_vm_active_job',
            },
        ),
        migrations.CreateModel(
            name='ValidationTest',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('line_items', models.ManyToManyField(
                    to='engagementmanager.ChecklistLineItem', verbose_name=b'Satisfies Line Items')),
            ],
            options={
                'db_table': 'ice_vm_validation_test',
            },
        ),
    ]