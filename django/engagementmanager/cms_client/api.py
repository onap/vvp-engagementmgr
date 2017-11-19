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

from django.conf import settings
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests_oauthlib import OAuth2Session
from rest_framework.status import HTTP_401_UNAUTHORIZED
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class CMSClient(object):
    """
    ICE CMS (Mezzanine) API Client SDK
    """

    def __init__(self):
        """
        Ice CMS client constructor ->
        :param MZN_ID: from env vars.
        :param MZN_Secret: from env vars.
        """
        super(CMSClient, self).__init__()

        self.client_id = settings.CMS_APP_CLIENT_ID
        self.client_secret = settings.CMS_APP_CLIENT_SECRET
        self.api_url = settings.CMS_URL
        self.token = self.generateToken(self.client_id, self.client_secret)
        self.session = OAuth2Session(self.client_id, token=self.token)

    # PROBLEM TO REMOVE TRY AND CATCH
    def generateToken(self, client_id, client_secret):
        """
        Create oauth2 token by id and secret (via cms server)
        :param client_id: client id (from env vars)
        :param client_secret: client secret (from env vars)
        :return: return the result token.
        """
        token = None

        try:
            client = BackendApplicationClient(client_id=client_id)
            oatuh = OAuth2Session(client=client)
            token = oatuh.fetch_token(
                token_url=self.api_url +
                'oauth2/token/',
                client_id=client_id,
                client_secret=client_secret)
        except Exception as exception:
            logger.error(
                'Could not create CMS token, error message: ' + str(exception))

        return token

    @staticmethod
    def json_serialize(obj):
        """
        Returns JSON serialization of object
        """
        return json.dumps(obj)

    @staticmethod
    def json_deserialize(string):
        """
        Returns deserialization of JSON
        """
        return json.loads(string)

    def get(self, resource, params=None):
        """
        Make a GET HTTP request
        """
        response = None
        try:
            response = self.session.get(self.api_url + resource,
                                        params=params)
            if response.status_code == HTTP_401_UNAUTHORIZED:
                logger.error(
                    'Token expired (401 status excepted), \
                    will renew cms token now')
                self.__init__()
                response = self.session.get(
                    self.api_url + resource, params=params)
        except TokenExpiredError as exception:
            logger.error(
                'Token expired (TokenExpiredError exception excepted),'
                ' will renew cms token now: ' + str(exception))
            self.__init__()
            response = self.session.get(self.api_url + resource,
                                        params=params)
        item = self.json_deserialize(response.content.decode('utf-8'))
        return item

    def get_posts(self, offset=0, limit=10, category="", date_min=""):
        """
        Get published blog posts
        :param date_min: all the posts returned will be after this date
        :param offset: pagination offset
        :param limit: pagination limit
        :param category: the category which the post related to
        :param limit: date_min of posts to return
        :return: list of dicts for most recently published blog posts
        """
        return self.get(
            'posts?offset={}&limit={}&category_name={}&date_min={}'.format(
                int(offset),
                int(limit),
                category,
                date_min))['results']

    def get_pages(self, title=""):
        """
        Get all pages and it's children.
        :param title: The title of the page we want
        :return: list of pages by out filters declaration
        """
        return self.get('pages?title={}'.format(title))['results']

    def get_page(self, id):
        """
        Return specific page by id
        :param id: The id of the page we want to require
        :return: the page result
        """
        return self.get('pages/{}'.format(int(id)))

    def search_pages(self, keyword):
        """
        Return pages by keyword contained in title or content
        :param keyword: The keyword which will be searched in title and content
        :return: the pages as result
        """

        return self.get('pages/search/?keyword={}'.format(keyword))
