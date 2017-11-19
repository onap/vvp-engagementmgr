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


def get_pages_mock(title=""):
    result = [{u'meta_description': u'Content of page #1',
               u'parent': None,
               u'title': u'Page #1',
               u'login_required': True,
               u'children': [],
               u'id': 1,
               u'content': u'<p>Content of page #1</p>',
               u'content_model': u'richtextpage',
               u'publish_date': u'2017-01-01T13:47:15Z',
               u'slug': u'documentation/page#1',
               u'tags': u''},
              {u'meta_description': u'Content of page #2',
               u'parent': None,
               u'title': u'Page #2',
               u'login_required': True,
               u'children': [],
               u'id': 2,
               u'content': u'<p>Content of page #2</p>',
               u'content_model': u'richtextpage',
               u'publish_date': u'2017-01-01T13:47:15Z',
               u'slug': u'documentation/page#2',
               u'tags': u''},
              {u'meta_description': u'Content of page #3',
               u'parent': None,
               u'title': u'Page #3',
               u'login_required': True,
               u'children': [],
               u'id': 3,
               u'content': u'<p>Content of page #3</p>',
               u'content_model': u'richtextpage',
               u'publish_date': u'2017-01-01T13:47:15Z',
               u'slug': u'documentation/page#3',
               u'tags': u''},
              {u'meta_description': u'Content of page #4',
               u'parent': None,
               u'title': u'Page #4',
               u'login_required': True,
               u'children': [],
               u'id': 4,
               u'content': u'<p>Content of page #4</p>',
               u'content_model': u'richtextpage',
               u'publish_date': u'2017-01-01T13:47:15Z',
               u'slug': u'documentation/page#4',
               u'tags': u''},
              {u'meta_description': u'Content of page #5',
               u'parent': None,
               u'title': u'Page #5',
               u'login_required': True,
               u'children': [],
               u'id': 5,
               u'content': u'<p>Content of page #5</p>',
               u'content_model': u'richtextpage',
               u'publish_date': u'2017-01-01T13:47:15Z',
               u'slug': u'documentation/page#5',
               u'tags': u''},
              {u'meta_description': u'Content of page #6',
               u'parent': None,
               u'title': u'Page #6',
               u'login_required': True,
               u'children': [],
               u'id': 6,
               u'content': u'<p>Content of page #6</p>',
               u'content_model': u'richtextpage',
               u'publish_date': u'2017-01-01T13:47:15Z',
               u'slug': u'documentation/page#6',
               u'tags': u''}]
    if title != "":
        return [result[0]]
    else:
        return result


def get_page_mock(id):
    result = {
        u'meta_description': u'Content of page #1',
        u'parent': None,
        u'title': u'Page #1',
        u'login_required': True,
        u'children': [],
        u'id': 1,
        u'content': u'<p>Content of page #1</p>',
        u'content_model': u'richtextpage',
        u'publish_date': u'2017-01-01T13:47:15Z',
        u'slug': u'documentation/page#1',
        u'tags': u''}

    return result


@mock.patch('engagementmanager.apps.cms_client.get_pages', get_pages_mock)
@mock.patch('engagementmanager.apps.cms_client.get_page', get_page_mock)
class CMSGetPagesTestCase(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])
        self.createDefaultRoles()
        self.admin, self.el, self.standard_user = \
            self.creator.createAndGetDefaultRoles()
        self.user = self.creator.createUser(
            Vendor.objects.get(
                name='Other'),
            self.randomGenerator("main-vendor-email"),
            'Aa123456',
            'user',
            self.standard_user,
            True)
        self.token = self.loginAndCreateSessionToken(self.user)

    def testGetPageById(self):
        urlStr = self.urlPrefix + 'cms/pages/1/'
        self.printTestName("testGetPageById [Start]")
        logger.debug("action should success (200), and return page by id")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content["title"], 'Page #1')
        self.printTestName("testGetPageById [End]")

    def testGetPages(self):
        urlStr = self.urlPrefix + 'cms/pages/'
        self.printTestName("testGetPages [Start]")
        logger.debug("action should success (200), and return all pages")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        # Suppose to be 6 The amount of Pages in the mock.
        self.assertEqual(len(json.loads(response.content)), 6)
        self.printTestName("testGetPages [End]")

    def testGetPagesByTitle(self):
        urlStr = self.urlPrefix + 'cms/pages/?title=Documentation'
        print(urlStr)
        self.printTestName("testGetPagesByTitle [Start]")
        logger.debug("action should success (200), and return filtered pages")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        content = json.loads(response.content)
        # Suppose to be 1 The amount of Documentation titled pages in the mock.
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]["title"], 'Page #1')
        self.printTestName("testGetPagesByTitle [End]")
