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


def get_posts_mock(offset=0, limit=10, category="", date_min=""):
    result = [{u'updated': u'2017-01-17T15:57:19.567778Z', u'title': u'announcement..new.1', u'url': u'http://127.0.0.1:8001/blog/announcementnew1/', u'short_url': u'/blog/announcementnew1/', u'tags': u'', u'excerpt': u'announcement..new.announcement..new.', u'allow_comments': True, u'comments': [], u'slug': u'announcementnew1', u'content': u'<p>announcement..new.announcement..new.</p>', u'publish_date': u'2017-01-14T19:53:52Z', u'user': {u'username': u'al942u', u'first_name': u'', u'last_name': u'', u'email': u'al942u@mail.com', u'is_staff': True, u'id': 1}, u'featured_image': u'', u'comments_count': 0, u'id': 1, u'categories': [{u'slug': u'announcement', u'id': 1, u'title': u'Announcement'}]},
              {u'updated': u'2017-01-16T15:57:19.567778Z', u'title': u'announcement..new.2', u'url': u'http://127.0.0.1:8001/blog/announcementnew2/', u'short_url': u'/blog/announcementnew2/', u'tags': u'', u'excerpt': u'announcement..new.announcement..new.', u'allow_comments': True, u'comments': [], u'slug': u'announcementnew2',
                  u'content': u'<p>announcement..new.announcement..new.</p>', u'publish_date': u'2017-01-15T19:53:52Z', u'user': {u'username': u'al942u', u'first_name': u'', u'last_name': u'', u'email': u'al942u@mail.com', u'is_staff': True, u'id': 1}, u'featured_image': u'', u'comments_count': 0, u'id': 2, u'categories': [{u'slug': u'announcement', u'id': 1, u'title': u'Announcement'}]},
              {u'updated': u'2017-01-15T15:57:19.567778Z', u'title': u'announcement..new.3', u'url': u'http://127.0.0.1:8001/blog/announcementnew3/', u'short_url': u'/blog/announcementnew3/', u'tags': u'', u'excerpt': u'announcement..new.announcement..new.', u'allow_comments': True, u'comments': [], u'slug': u'announcementnew3',
                  u'content': u'<p>announcement..new.announcement..new.</p>', u'publish_date': u'2017-01-16T19:53:52Z', u'user': {u'username': u'al942u', u'first_name': u'', u'last_name': u'', u'email': u'al942u@mail.com', u'is_staff': True, u'id': 1}, u'featured_image': u'', u'comments_count': 0, u'id': 3, u'categories': [{u'slug': u'announcement', u'id': 1, u'title': u'Announcement'}]},
              {u'updated': u'2017-01-14T15:57:19.567778Z', u'title': u'news..new.1', u'url': u'http://127.0.0.1:8001/blog/news1/', u'short_url': u'/blog/news1/', u'tags': u'', u'excerpt': u'news..new.news..new.', u'allow_comments': True, u'comments': [], u'slug': u'news1', u'content': u'<p>news..new.news..new.</p>',
               u'publish_date': u'2017-01-14T19:53:52Z', u'user': {u'username': u'al942u', u'first_name': u'', u'last_name': u'', u'email': u'al942u@mail.com', u'is_staff': True, u'id': 1}, u'featured_image': u'', u'comments_count': 0, u'id': 4, u'categories': [{u'slug': u'news', u'id': 1, u'title': u'News'}]},
              {u'updated': u'2017-01-13T15:57:19.567778Z', u'title': u'news..new.2', u'url': u'http://127.0.0.1:8001/blog/news2/', u'short_url': u'/blog/news2/', u'tags': u'', u'excerpt': u'news..new.news..new.', u'allow_comments': True, u'comments': [], u'slug': u'news2', u'content': u'<p>news..new.news..new.</p>',
               u'publish_date': u'2017-01-15T19:53:52Z', u'user': {u'username': u'al942u', u'first_name': u'', u'last_name': u'', u'email': u'al942u@mail.com', u'is_staff': True, u'id': 1}, u'featured_image': u'', u'comments_count': 0, u'id': 5, u'categories': [{u'slug': u'news', u'id': 1, u'title': u'News'}]},
              {u'updated': u'2017-01-12T15:57:19.567778Z', u'title': u'news..new.3', u'url': u'http://127.0.0.1:8001/blog/news3/', u'short_url': u'/blog/news3/', u'tags': u'', u'excerpt': u'news..new.news..new.', u'allow_comments': True, u'comments': [], u'slug': u'news3', u'content': u'<p>news..new.news..new.</p>', u'publish_date': u'2017-01-16T19:53:52Z', u'user': {u'username': u'al942u', u'first_name': u'', u'last_name': u'', u'email': u'al942u@mail.com', u'is_staff': True, u'id': 1}, u'featured_image': u'', u'comments_count': 0, u'id': 6, u'categories': [{u'slug': u'news', u'id': 1, u'title': u'News'}]}]

    if category == "News":
        return [result[3], result[4], result[5]]
    elif date_min != "":
        return [result[0], result[1]]
    elif category == "Announcement" and limit == 1:
        return [result[0]]
    elif limit != 10:
        return result[:int(limit)]
    else:
        return result


@mock.patch('engagementmanager.apps.cms_client.get_posts', get_posts_mock)
class CMSGetPostsTestCase(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])
        self.createDefaultRoles()
        self.admin, self.el, self.standard_user = self.creator.createAndGetDefaultRoles()
        self.user = self.creator.createUser(Vendor.objects.get(name='Other'),
                                            self.randomGenerator("main-vendor-email"), 'Aa123456',
                                            'user', self.standard_user, True)
        self.token = self.loginAndCreateSessionToken(self.user)

    def testGetPostsByCategory(self):
        urlStr = self.urlPrefix + 'cms/posts/?category=News'
        print(urlStr)
        self.printTestName("GetPostsByCategoryTest [Start]")
        logger.debug("action should success (200), and return filtered posts")
        response = self.c.get(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(json.loads(response.content)), 3)  # Suppose to be 3 The amount of News in the mock.
        self.printTestName("GetPostsByCategoryTest [End]")

    def testGetAllPosts(self):
        urlStr = self.urlPrefix + 'cms/posts/?limit=10'
        self.printTestName("GetAllPostsTest [Start]")
        logger.debug("action should success (200), and return all posts")
        response = self.c.get(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        # Suppose to be 6 items like the amount of items of the mock.
        self.assertEqual(len(json.loads(response.content)), 6)
        self.printTestName("GetAllPostsTest [End]")

    def testGetLimitedPosts(self):
        limit = 2
        urlStr = self.urlPrefix + 'cms/posts/?limit=' + str(limit)
        self.printTestName("GetLimitedPostsTest [Start]")
        logger.debug("action should success (200), and filtered with limit all posts")
        response = self.c.get(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(json.loads(response.content)), limit)  # Suppose to be {{limit}} amount of items
        self.printTestName("GetLimitedPostsTest [End]")

    def testGetPostsByDateMin(self):
        urlStr = self.urlPrefix + 'cms/posts/?fromLastDays=2&limit=10'
        self.printTestName("GetPostsByDateMinTest [Start]")
        logger.debug("action should success (200), and return filtered posts")
        response = self.c.get(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(json.loads(response.content)), 2)  # Suppose to be 2 items that are after this date
        self.printTestName("GetPostsByDateMinTest [End]")

    def testGetOneAnnouncementPost(self):
        urlStr = self.urlPrefix + 'cms/posts/?limit=1&category=Announcement'
        self.printTestName("GetOneAnnouncementPostTest [Start]")
        logger.debug("action should success (200), and return one announcement post")
        response = self.c.get(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(json.loads(response.content)), 1)  # Suppose to be just 1 item like that.
        self.printTestName("GetOneAnnouncementPostTest [End]")
