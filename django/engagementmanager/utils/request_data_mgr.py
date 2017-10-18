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
import threading
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class RequsetData():
    _thread_id = None
    _cl_uuid = None
    _eng_uuid = None
    _user = None
    _ns_uuid = None
    _notification_uuid = None

    def __init__(self):
        pass


class RequsetDataMgr:

    threadLocal = threading.local()

    '''
        Managing the request data per each request
    '''

    def __init__(self):
        pass

    '''
        Private method
    '''

    def get_request_data(self):
        request_data = getattr(self.threadLocal, 'request_data', None)
        if request_data is None:
            request_data = RequsetData()
            self.threadLocal.request_data = request_data

        return request_data

    def get_user(self):
        return self.get_request_data()._user

    def get_eng_uuid(self):
        return self.get_request_data()._eng_uuid

    def get_cl_uuid(self):
        return self.get_request_data()._cl_uuid

    def get_ns_uuid(self):
        return self.get_request_data()._ns_uuid

    def get_notification_uuid(self):
        return self.get_request_data()._notification_uuid

    def set_user(self, user):
        self.get_request_data()._user = user

    def set_eng_uuid(self, eng_uuid):
        self.get_request_data()._eng_uuid = eng_uuid

    def set_cl_uuid(self, cl_uuid):
        self.get_request_data()._cl_uuid = cl_uuid

    def set_ns_uuid(self, ns_uuid):
        self.get_request_data()._ns_uuid = ns_uuid

    def set_notification_uuid(self, notification_uuid):
        self.get_request_data()._notification_uuid = notification_uuid

    def get_request_data_vars(self):
        return {
            'cl_uuid': self.get_request_data()._cl_uuid,
            'eng_uuid': self.get_request_data()._eng_uuid,
            'user': self.get_request_data()._user,
            'ns_uuid': self.get_request_data()._ns_uuid,
            'notification_uuid': self.get_request_data()._notification_uuid,
        }

    '''
        Called from the verify_token decorator which is a central place that populates the user and all other attributes in RequestData object
    '''

    def clear_old_request_data(self):
        self.threadLocal.request_data = RequsetData()


# singleton pattern, allocated on server startup
request_data_mgr = RequsetDataMgr()
