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
""" clean_vvp_system
Will clean all program data:
1. Deletes all gitlab projects/users/groups.
2. Deletes all data stored in database.
3. Deletes all jobs stored in jenkins.

It's recommended to clean the vvp system if you desire in a fresh copy of the vvp program
without installing it all over again.

WARNING: It will delete almost everything, if you have necessary data DO NOT USE THIS COMMAND!
"""
from django.core.management.base import BaseCommand
from engagementmanager.management.commands import clean_gitlab_content
from engagementmanager.management.commands import clean_jenkins_jobs
from engagementmanager.management.commands import clean_vvp_db
from engagementmanager.management.commands import initial_populate_db
from engagementmanager.service.logging_service import LoggingServiceFactory
from engagementmanager.utils.constants import Constants

logger = LoggingServiceFactory.get_logger()


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("***************************************")
        logger.info("%s system is about to be cleaned up!" % Constants.program_name)
        logger.info("***************************************")

        try:
            clean_gitlab_content_command = clean_gitlab_content.Command()
            clean_gitlab_content_command.handle(args, options)
        except Exception as e:
            logger.error("There was a problem cleaning git-lab", e)

        try:
            clean_jenkins_jobs_command = clean_jenkins_jobs.Command()
            clean_jenkins_jobs_command.handle(args, options)
        except Exception as e:
            logger.error("There was a problem cleaning Jenkins", e)

        try:
            clean_vvp_db_command = clean_vvp_db.Command()
            clean_vvp_db_command.handle(args, options)
        except Exception as e:
            logger.error("There was a problem cleaning %s db" % Constants.program_name, e)

        try:
            initial_populate_db_command = initial_populate_db.Command()
            initial_populate_db_command.handle(args, options)
        except Exception as e:
            logger.error("There was a problem populate %s db after cleaning" % Constants.program_name, e)

        logger.info("***************************************")
        logger.info("Done!")
        logger.info("***************************************")
