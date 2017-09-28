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
# Generated by Django 1.10.6 on 2017-07-04 06:35
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('engagementmanager', '0032_auto_20170702_1435'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='applicationserviceinfrastructure',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, unique=True),
        ),
        migrations.AlterField(
            model_name='checklist',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='checklistauditlog',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='checklistdecision',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='checklistlineitem',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='checklistsection',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='checklisttemplate',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='deploymenttarget',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='deploymenttargetsite',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='ecomprelease',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='engagement',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=64, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='engagementstatus',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=64, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='feedback',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='iceuserprofile',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, unique=True),
        ),
        migrations.AlterField(
            model_name='invitation',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='nextstep',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='notification',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='recentengagement',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=64, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='role',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, unique=True),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, unique=True),
        ),
        migrations.AlterField(
            model_name='vf',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='vfc',
            name='uuid',
            field=models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False, unique=True),
        ),
    ]
