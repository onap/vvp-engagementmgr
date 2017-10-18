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
""" clean_vvp_db
Will delete content from database (almost all entities) to create initial environment.

This command uses django orm to remove data.
This command is part of clean_vvp_system command but can be used separately as well.

WARNING: It will delete almost everything, if you have necessary data DO NOT USE THIS COMMAND!
"""
from django.core.management.base import BaseCommand
from engagementmanager import models
from engagementmanager.management.commands.initial_populate_db import admin_dummy_users, admin_ro_dummy_users, \
    dummy_users, el_dummy_users
from engagementmanager.service.logging_service import LoggingServiceFactory
from engagementmanager.utils.constants import Constants

logger = LoggingServiceFactory.get_logger()


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("***************************************")
        logger.info(">>%s db is about to be cleaned up!" % Constants.program_name)
        logger.info("***************************************")

        excluded_emails = [dummy_users[0][1], dummy_users[1][1],
                           el_dummy_users[0][1], el_dummy_users[1][1],
                           admin_dummy_users[0][1], admin_ro_dummy_users[0][1], ]

        try:
            models.EngagementStatus.objects.all().delete()
            models.Invitation.objects.all().delete()
            models.Notification.objects.all().delete()
            models.Activity.objects.all().delete()
            models.NextStep.objects.all().delete()
            models.ChecklistAuditLog.objects.all().delete()
            models.ChecklistDecision.objects.all().delete()
            models.Checklist.objects.all().delete()
            models.ChecklistLineItem.objects.all().delete()
            models.ChecklistSection.objects.all().delete()
            models.ChecklistTemplate.objects.all().delete()
            models.RecentEngagement.objects.all().delete()
            models.VFC.objects.all().delete()
            models.VF.objects.all().delete()
            models.EngagementStatus.objects.all().delete()
            models.Engagement.objects.all().delete()
            models.IceUserProfile.objects.exclude(email__in=excluded_emails)\
                .delete()
            models.CustomUser.objects.exclude(user_ptr_id__in=models.IceUserProfile.objects.all().values('id')).delete()

            models.DeploymentTarget.objects.all().delete()
            models.DeploymentTargetSite.objects.all().delete()
            models.ECOMPRelease.objects.all().delete()
            logger.info("***************************************")
            logger.info(">>%s db is now clean!" % Constants.program_name)
            logger.info("***************************************")
        except Exception as exception:
            logger.error("Something went wrong while trying"
                         " to clean %s db" % Constants.program_name, exception)
