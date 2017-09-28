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
import json
import mock
from rest_framework.status import HTTP_200_OK
from engagementmanager.models import Vendor
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def search_page_mock(keyword):
    result = [{u'id': 1, u'title': 'exists_title', u'children': [], u'status': '', u'_order': 1}, ]
    return result


def search_empty_page_mock(keyword):
    return []


class TestCMSDocumentationSearch(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])
        self.createDefaultRoles()
        self.admin, self.el, self.standard_user = self.creator.createAndGetDefaultRoles()
        self.user = self.creator.createUser(Vendor.objects.get(name='Other'),
                                            self.randomGenerator("main-vendor-email"), 'Aa123456',
                                            'user', self.standard_user, True)
        self.token = self.loginAndCreateSessionToken(self.user)

    def testSearchEmptyString(self):
        urlStr = self.urlPrefix + 'cms/pages/search/?keyword='
        self.printTestName("testSearchEmptyString [Start]")
        logger.debug("action should success (200), and return empty array")
        response = self.c.get(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content, [])
        self.printTestName("testSearchEmptyString [End]")

    @mock.patch('engagementmanager.apps.cms_client.search_pages', search_empty_page_mock)
    def testSearchNotExistsKeyword(self):
        urlStr = self.urlPrefix + 'cms/pages/search/?keyword=somewordnotexists'
        self.printTestName("testSearchNotExistsKeyword [Start]")
        logger.debug("action should success (200), and return empty array")
        response = self.c.get(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content, [])
        self.printTestName("testSearchNotExistsKeyword [End]")

    @mock.patch('engagementmanager.apps.cms_client.search_pages', search_page_mock)
    def testSearchExistsKeyword(self):
        urlStr = self.urlPrefix + 'cms/pages/search/?keyword=exists_title'
        self.printTestName("testSearchExistsKeyword [Start]")
        logger.debug("action should success (200), and return array with one page (by mock)")
        response = self.c.get(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content[0]['title'], 'exists_title')
        self.printTestName("testSearchExistsKeyword [End]")
