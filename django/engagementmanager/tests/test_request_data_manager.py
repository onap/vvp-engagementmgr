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
from concurrent.futures import ThreadPoolExecutor
import json
from random import randint
import threading
import time
from django.db import connections
from django.test.client import Client
from django.test.testcases import TransactionTestCase
from rest_framework.status import HTTP_401_UNAUTHORIZED, HTTP_200_OK

from django.conf import settings
from engagementmanager.models import Vendor
from engagementmanager.tests.vvpEntitiesCreator import VvpEntitiesCreator
from engagementmanager.utils.authentication import JWTAuthentication
from engagementmanager.utils.constants import Constants
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class TestRequestDataManager(TransactionTestCase):

    def childSetup(self):
        logger.debug("---------------------- TestCase " +
                     self.__class__.__name__ + " ----------------------")
        self.urlPrefix = "/%s/v1/engmgr/" % settings.PROGRAM_NAME_URL_PREFIX
        self.c = Client()
        self.creator = VvpEntitiesCreator()

        for vendor in [Constants.service_provider_company_name, 'Other']:
            vendorUuid, vendor = self.creator.createVendor(vendor)
            logger.debug(vendorUuid)

        self.admin, self.el, self.standard_user = \
            self.creator.createAndGetDefaultRoles()

        # Create a user with role el
        self.el_user = self.creator.createUser(
            Vendor.objects.get(name=Constants.service_provider_company_name),
            self.creator.randomGenerator("main-vendor-email"),
            '55501000199', 'el user', self.el, True)
        self.peer_review_user = self.creator.createUser(
            Vendor.objects.get(name=Constants.service_provider_company_name),
            self.creator.randomGenerator("main-vendor-email"),
            '55501000199', 'peer-reviewer user', self.el, True)
        # Create a user with role standard_user
        self.user = self.creator.createUser(
            Vendor.objects.get(name='Other'), self.creator.randomGenerator(
                "main-vendor-email"),
            '55501000199', 'user', self.standard_user, True)
        self.user_not_team = self.creator.createUser(
            Vendor.objects.get(name='Other'), self.creator.randomGenerator(
                "main-vendor-email"),
            '55501000199', 'user2', self.standard_user, True)
#         # Create an Engagement with team
        self.engagement = self.creator.createEngagement(
            'just-a-fake-uuid', 'Validation', None)
        self.engagement.engagement_team.add(self.user, self.el_user)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.peer_review_user
        self.engagement.save()

        self.jwt_service = JWTAuthentication()
        self.token = self.jwt_service.create_token(self.user.user)
        self.ELtoken = self.jwt_service.create_token(self.el_user.user)

        urlStr = self.urlPrefix + 'engagements/${uuid}/status'
        myjson = json.dumps({"description": "blah blah"}, ensure_ascii=False)
        response = self.c.post(urlStr.replace('${uuid}', str(
            self.engagement.uuid)), myjson, content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        self.created_status = json.loads(response.content)

    def my_task(self, eng_id):
        thread_local_id = threading.currentThread().ident

        # Inject an attribute into request data
        request_data_mgr.set_eng_uuid(eng_id)

        # Inject thread id into requeat data
        request_data_mgr.set_cl_uuid(thread_local_id)

        return self.my_inner_funcion(eng_id)

    def my_inner_funcion(self, eng_id):
        thread_local_id = threading.currentThread().ident

        assert request_data_mgr.get_request_data()

        assert request_data_mgr.get_request_data()._eng_uuid == eng_id
        assert request_data_mgr.get_eng_uuid() == eng_id

        # Checks that the allocated thread from testRequestDataManager is the
        # same thread running in inner function
        assert request_data_mgr.get_request_data()._cl_uuid == thread_local_id
        assert request_data_mgr.get_cl_uuid() == thread_local_id

        print('thread: ' + str(thread_local_id) + '. request data : ' +
              str(request_data_mgr.get_request_data_vars()))
        return "OK"

    def lauchTests(self):
        executor = ThreadPoolExecutor(max_workers=10)

        for i in range(0, 100):
            future1 = executor.submit(self.my_task, "eng#" + str(i))
            assert future1.result() == "OK"

    def testRequestDataManager(self):
        executor = ThreadPoolExecutor(max_workers=2)
        executor.submit(self.lauchTests)
        executor.submit(self.lauchTests)

    def testMultipleRequestsInParallel(self):
        self.childSetup()
        number_of_concurrent_requests = 10
        executor = ThreadPoolExecutor(
            max_workers=number_of_concurrent_requests)

        def close_db_connections(func, *args, **kwargs):
            """
            Decorator to explicitly close db connections,
            during threaded execution.

            Note this is necessary to work around:
            https://code.djangoproject.com/ticket/22420
            """
            def _close_db_connections(*args, **kwargs):
                ret = None
                try:
                    ret = func(*args, **kwargs)
                finally:
                    for conn in connections.all():
                        logger.debug(
                            "Closing DB connection. connection=" + str(conn))
                        conn.close()
                return ret
            return _close_db_connections

        @close_db_connections
        def invokeRequest(metadata, token):
            urlStr = self.urlPrefix + 'engagements/${uuid}/status'

            logger.debug("START - " + metadata)

            myjson = json.dumps(
                {"eng_status_uuid": self.created_status['uuid'],
                 "description": "blah2 blah2"}, ensure_ascii=False)
            response = self.c.put(urlStr.replace('${uuid}', str(
                self.engagement.uuid)), myjson,
                content_type='application/json',
                **{'HTTP_AUTHORIZATION': "token " + self.token})
            print('Got response : ' + str(response.status_code))
            self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

            time.sleep(randint(0, 1))

            myjson = json.dumps(
                {"eng_status_uuid": self.created_status['uuid'],
                 "description": "blah2 blah2"}, ensure_ascii=False)
            response = self.c.put(urlStr.replace('${uuid}', str(
                self.engagement.uuid)), myjson,
                content_type='application/json',
                **{'HTTP_AUTHORIZATION': "token " + token})
            print('Got response : ' + str(response.status_code))
            self.assertEqual(response.status_code, HTTP_200_OK)

            logger.debug("END - " + metadata)

            return metadata

        for i in range(0, number_of_concurrent_requests):
            eluser = self.creator.createUser(
                Vendor.objects.get(name='Other'), self.creator.randomGenerator(
                    "main-vendor-email"),
                '55501000199', 'user' + str(i), self.el, True)
            token = self.jwt_service.create_token(eluser.user)
            self.engagement = self.creator.createEngagement(
                'just-a-fake-uuid', 'Validation', None)
            self.engagement.engagement_team.add(eluser)
            self.engagement.reviewer = eluser
            self.engagement.peer_reviewer = self.peer_review_user
            self.engagement.save()

            metadata = "test " + str(i)
            future = executor.submit(invokeRequest, metadata, token)
            assert future.result() == metadata
