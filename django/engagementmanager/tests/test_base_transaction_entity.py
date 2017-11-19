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
from abc import ABCMeta, abstractmethod
import http.client
import django
from django.conf import settings
from django.test.client import Client
from django.test.testcases import TransactionTestCase
from engagementmanager.tests.vvpEntitiesCreator import VvpEntitiesCreator
from engagementmanager.service.logging_service import LoggingServiceFactory
django.setup()
logger = LoggingServiceFactory.get_logger()


class TestBaseTransactionEntity(TransactionTestCase):
    __metaclass__ = ABCMeta

    def setUp(self):
        logger.debug("---------------------- TransactionTestCase " +
                     self.__class__.__name__ + " ----------------------")
        self.urlPrefix = "/%s/v1/engmgr/" % settings.PROGRAM_NAME_URL_PREFIX
        self.conn = http.client.HTTPConnection(
            "127.0.0.1", 8000)  # @UndefinedVariable
        self.c = Client()
        self.creator = VvpEntitiesCreator()
        settings.IS_SIGNAL_ENABLED = False
        self.childSetup()

    def tearDown(self):
        settings.IS_SIGNAL_ENABLED = True
        self.conn.close()
        logger.debug("----------------------  TransactionTestCase " +
                     self.__class__.__name__ + " ---------------------- ")

    @abstractmethod
    def childSetup(self):
        pass

    def randomGenerator(self, typeOfValue, numberOfDigits=0):
        return self.creator.randomGenerator(typeOfValue, numberOfDigits)

    def loginAndCreateSessionToken(self, user):
        return self.creator.loginAndCreateSessionToken(user)
