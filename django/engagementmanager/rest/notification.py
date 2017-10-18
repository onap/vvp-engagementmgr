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
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT,\
    HTTP_400_BAD_REQUEST

from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
import engagementmanager.models
from engagementmanager.notifications import num_of_notifications_for_user, reset_num_of_notifications_for_user,\
    pull_recent_notifications
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.utils.request_data_mgr import request_data_mgr


@classDecorator([logFuncEntry])
class PullNotifCount4User(VvpApiView):

    def get(self, request):
        user = request_data_mgr.get_user()
        dataToJson = {}
        notificationCtr = num_of_notifications_for_user(user.uuid)
        dataToJson['notifications_number'] = str(notificationCtr)
        return Response(dataToJson)


@classDecorator([logFuncEntry])
class NotificationOps(VvpApiView):

    @auth(Permissions.delete_notification)
    def delete(self, request, notif_uuid):
        notif = self.get_entity(
            engagementmanager.models.Notification, notif_uuid)
        notif.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    # PullRecentNotif4User
    def get(self, request, user_uuid, offset, limit):
        user = request_data_mgr.get_user()
        serilizedActivitySet, num_of_objects = pull_recent_notifications(user.uuid, offset, limit)
        if serilizedActivitySet is not None:
            data = {'serilizedActivitySet': serilizedActivitySet, 'num_of_objects': num_of_objects}
            return Response(data)
        else:
            return Response("Activity set wasn't found", status=HTTP_400_BAD_REQUEST)

    # Reset the number of an unread notifications
    def put(self, request):
        user = request_data_mgr.get_user()
        reset_num_of_notifications_for_user(user.uuid)
        return Response()
