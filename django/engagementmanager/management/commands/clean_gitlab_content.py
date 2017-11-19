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
""" clean_gitlab_content
Will delete content from gitlab to create initial environment:
1.Projects
2.Groups
3.Users

This command uses gitlab client rest api to remove data.
This command is part of clean_vvp_system
command but can be used separately as well.

WARNING: It will delete almost everything, if you have
necessary data DO NOT USE THIS COMMAND!
"""
from django.conf import settings
from django.core.management.base import BaseCommand
import requests
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("***************************************")
        logger.info(">>git-lab is about to be cleaned up!")
        logger.info("***************************************")

        entities = ['projects', 'groups', 'users', ]
        headers = dict()
        headers['Content-type'] = 'application/json'
        headers['PRIVATE-TOKEN'] = settings.GITLAB_TOKEN

        for entity in entities:
            entities_deleted = []
            gitlab_entity_url = settings.GITLAB_URL + "api/v3/%s/" % entity
            r1 = requests.get(gitlab_entity_url, headers=headers,
                              verify=False)
            data = r1.json()

            while len(data) > 1:
                for record in data:
                    try:
                        if record['id'] not in entities_deleted \
                                and record['name'] != 'Administrator':
                            requests.delete(gitlab_entity_url +
                                            str(record['id']),
                                            headers=headers,
                                            verify=False)
                            logger.info(
                                "Entity '%s' with id %s Will be deleted"
                                " in a bit (type: %s)" %
                                (record['name'], record['id'], entity,))

                            entities_deleted.append(record['id'])
                    except Exception as e:
                        logger.error("Some problem occurred... We give it "
                                     "another shot...", e)

                r1 = requests.get(gitlab_entity_url, headers=headers,
                                  verify=False)
                data = r1.json()

            logger.info("***************************************")
            logger.info(">>>>All %s deleted from git-lab" % entity)
            logger.info("***************************************")

        logger.info("***************************************")
        logger.info(">>git-lab is now clean!")
        logger.info("***************************************")
