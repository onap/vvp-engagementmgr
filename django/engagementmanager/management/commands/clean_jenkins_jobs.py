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
""" clean_jenkins_jobs
Will delete content(jobs) from jenkins to create initial environment.

This command uses jenkins_client api to remove data.
This command is part of clean_vvp_system command but can be used separately as well.

WARNING: It will delete almost everything, if you have necessary data DO NOT USE THIS COMMAND!
"""
from validationmanager.utils.clients import get_jenkins_client
from django.core.management.base import BaseCommand
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("***************************************")
        logger.info(">>Jenkins is about to be cleaned up!")
        logger.info("***************************************")

        try:
            jenkins_client = get_jenkins_client()
            job_names = jenkins_client.get_jobs_names()

            for job_name in job_names:
                jenkins_client.delete_job(job_name)
                logger.info("Jenkins job '%s' deleted successfully." % job_name)
        except Exception as e:
            logger.error("Some problem occurred while trying "
                         "cleaning Jenkins...", e)

        logger.info("***************************************")
        logger.info(">>Jenkins is now clean!")
        logger.info("***************************************")
