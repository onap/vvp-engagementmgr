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
from boto.s3.connection import S3Connection, OrdinaryCallingFormat
from django.conf import settings
from validationmanager.rados.rgwa_client import RGWAClient


class RGWAClientFactory(object):
    __standard_client = None
    __admin_client = None

    def __init__(self):
        if self.__standard_client is None:
            self.__set_standard_client()

        if self.__admin_client is None:
            self.__set_admin_client()

    @classmethod
    def __set_standard_client(cls):
        if cls.__standard_client is None:
            cls.__standard_client = S3Connection(
                host=settings.AWS_S3_HOST,
                port=settings.AWS_S3_PORT,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                calling_format=OrdinaryCallingFormat(),
                is_secure=True)
            cls.__standard_client.num_retries = 0

    @classmethod
    def __set_admin_client(cls):
        if cls.__admin_client is None:
            cls.__admin_client = RGWAClient(
                base_url='https://{S3_HOST}:{S3_PORT}/admin'.format(
                    S3_HOST=settings.AWS_S3_HOST,
                    S3_PORT=settings.AWS_S3_PORT, ))

    @classmethod
    def standard(cls):
        if cls.__standard_client is None:
            cls.__set_standard_client()
        return cls.__standard_client

    @classmethod
    def admin(cls):
        if cls.__admin_client is None:
            cls.__set_admin_client()
        return cls.__admin_client
