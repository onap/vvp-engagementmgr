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
from django.utils import timezone
from engagementmanager.bus.messages.new_notification_message \
    import NewNotificationMessage
from engagementmanager.models import IceUserProfile, Activity, Notification
from engagementmanager.utils import activities_data
from engagementmanager.utils.constants import Constants
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class ActivitiesSvc:
    def __init__(self):
        pass

    def generate_activity(self, activity_data):
        if hasattr(activity_data, "users_list") and activity_data.users_list:
            for user in activity_data.users_list:
                activity_data.user = user
                if hasattr(activity_data, "multiple_users_as_owners") and \
                        activity_data.multiple_users_as_owners:
                    activity_data.owner = activity_data.user
                self.set_description(activity_data)
                self.set_metadata(activity_data)
                self.__create_activity(activity_data)
        else:
            self.set_description(activity_data)
            self.set_metadata(activity_data)
            self.__create_activity(activity_data)

    def __create_activity(self, activity_data):
        if activity_data.engagement is None:
            msg = "Engagement provided is a None object, " +\
                "be careful not to generate description and metadata " +\
                "with engagement properties."
            logger.warn(msg)
        if activity_data.owner and not isinstance(activity_data.owner,
                                                  IceUserProfile):
            raise ValueError(
                "owner should be IceUserProfile, was %r", activity_data.owner)
        if activity_data.description is None:
            logger.warn(
                'createActivity called with description=None; setting to ""')
            activity_data.description = ''

        new_activity = Activity.objects.create(
            activity_owner=activity_data.owner,
            description=activity_data.description,
            is_notification=activity_data.is_notification,
            engagement=activity_data.engagement,
            activity_type=activity_data.activity_type.name,
            metadata=json.dumps(activity_data.metadata, ensure_ascii=False),)

        if activity_data.engagement:
            activity_data.engagement.activity_set.add(new_activity)
        new_activity.save()

        if activity_data.is_notification:
            users_to_notify = []

            if activity_data.owner is None:
                if activity_data.engagement:
                    users_to_notify = activity_data.engagement.\
                        engagement_team.all()
            else:
                users_to_notify.append(activity_data.owner)

            for user_to_notify in users_to_notify:
                new_notification = Notification.objects.create(
                    user=user_to_notify, activity=new_activity)
                new_activity.notification_set.add(new_notification)
                user_to_notify.notification_set.add(new_notification)
                new_notification.save()
                from engagementmanager.apps import bus_service
                bus_service.send_message(
                    NewNotificationMessage(new_notification))

    def pull_recent_activities(self, engagement, recent_activities_limit):
        """ expected: engagement object (Activity), recent_activities_limit
        (integer) - number of recent activities
        result: Top-X Dict Activity objects (sort by create_time) """
        logger.debug("Pulling top X activities from DB")
        activities = Activity.objects.filter(
            engagement=engagement, activity_owner=None).order_by(
                '-create_time')[:recent_activities_limit]
        return activities

    def set_description(self, activity_data):
        dt = timezone.now()
        description = ''

        if isinstance(activity_data, activities_data.
                      UserJoinedEngagementActivityData):
            description = "##user_name## joined ##vf_name## "
        elif isinstance(activity_data, activities_data.
                        UpdateNextStepsActivityData):
            description = "##user_name## " + activity_data.\
                update_type.lower() + " a next step"
        elif isinstance(activity_data, activities_data.
                        VFProvisioningActivityData):
            description = "Failed Gitlab and/or Jenkins Provision " +\
                "##vf_name##: " + activity_data.description
        elif isinstance(activity_data, activities_data.
                        TestFinishedActivityData):
            description = "Failure in Jenkins Job: "\
                + activity_data.description
        elif isinstance(activity_data, activities_data.
                        ChangeEngagementStageActivityData):
            description = "Engagement stage is now " + \
                activity_data.stage + " for the following VF: ##vf_name##"
        elif isinstance(activity_data, activities_data.
                        DeleteNextStepsActivityData):
            description = activity_data.user.full_name + \
                " has deleted a next step at " + \
                dt.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(activity_data, activities_data.
                        NoticeEmptyEngagementData):
            description = "You have not added any parts of the VNF package " +\
                "to your engagement ##vf_name## since it was created " \
                + activity_data.delta_days_from_creation + \
                " days ago. Do note that if you have not added any " +\
                "parts of the VNF package by " + \
                activity_data.max_empty_time + ", we will be automatically " +\
                "archive it."
        elif isinstance(activity_data, activities_data.
                        AddNextStepsActivityData):
            description = activity_data.user.full_name + \
                " has added a next step at " + dt.strftime(
                    "%Y-%m-%d %H:%M:%S")
        elif isinstance(activity_data, activities_data.
                        SSHKeyAddedActivityData):
            if activity_data.action == 'add':
                description = "You have added an SSH key to your profile"
            elif activity_data.action == 'set':
                description = "You have set a new SSH key in your profile"
            else:
                description = "SSH key activity"

        activity_data.description = description

    def set_metadata(self, activity_data):
        dt = timezone.now()
        metadata = {}

        if isinstance(activity_data, activities_data.
                      UserJoinedEngagementActivityData):
            activity_data.is_notification = True
            metadata['notification_subject'] = "Someone has joined the " + \
                activity_data.vf.name + " team"
            metadata['notification_message'] = activity_data.user.full_name +\
                " joined the " + activity_data.vf.name + \
                " team. You can reach the dashboard by " +\
                "going to this link: " + \
                Constants.dashboard_href
            metadata['macros'] = {
                '##vf_name##': {
                    'type': 'select_engagement',
                    'short': activity_data.vf.name,
                    'eng_uuid': str(activity_data.engagement.uuid),
                },
                '##user_name##': {
                    'type': 'popover',
                    'short': activity_data.user.full_name,
                    'long': activity_data.user.email,
                }
            }
        elif isinstance(activity_data, activities_data.
                        UpdateNextStepsActivityData):
            metadata['macros'] = {
                '##user_name##': {
                    'type': 'popover',
                    'short': activity_data.user.full_name,
                    'long': activity_data.user.email,
                }
            }
        elif isinstance(activity_data, activities_data.
                        NoticeEmptyEngagementData):
            activity_data.is_notification = True
            metadata['notification_subject'] = "Inactive Engagement Alert - "\
                + activity_data.vf_name

            metadata['notification_message'] = "We have noticed that " +\
                "you have not added any parts of the VNF " +\
                "package to your engagement <em>"\
                + activity_data.engagement.engagement_manual_id + ": "\
                + activity_data.vf_name + "</em> since it was created "\
                + activity_data.delta_days_from_creation +\
                " days ago. If you have any questions around how you add " +\
                "your VNF package please check the relevant parts of the " +\
                "online documentation.<br/><br/>" +\
                "Do note that if you have not added any parts of the VNF " +\
                "package by " + activity_data.max_empty_time + ", we will " +\
                "be automatically archive it."

            metadata['macros'] = {
                '##vf_name##': {
                    'type': 'select_engagement',
                    'short': activity_data.vf_name,
                    'eng_uuid': activity_data.engagement.uuid,
                },
            }

        elif isinstance(activity_data, activities_data.
                        VFProvisioningActivityData):
            activity_data.is_notification = True
            metadata['notification_subject'] = "Failed Gitlab and/or " +\
                "Jenkins Provision: " + activity_data.vf.name
            metadata['notification_message'] = activity_data.description
            metadata['macros'] = {
                '##vf_name##': {
                    'type': 'select_engagement',
                    'short': activity_data.vf.name,
                    'eng_uuid': activity_data.vf.engagement.uuid,
                },
            }
        elif isinstance(activity_data, activities_data.
                        TestFinishedActivityData):
            activity_data.is_notification = True
            metadata['notification_subject'] = "Failed test_finished signal "
            metadata['notification_message'] = activity_data.description
        elif isinstance(activity_data, activities_data.
                        ChangeEngagementStageActivityData):
            activity_data.is_notification = True
            metadata['notification_subject'] = "Engagement stage was " +\
                "changed for the following VF: " + activity_data.vf.name
            metadata['notification_message'] = "Engagement stage is now " \
                + activity_data.stage + " for the following VF: " \
                + activity_data.vf.name
            metadata['macros'] = {
                '##vf_name##': {
                    'type': 'select_engagement',
                    'short': activity_data.vf.name,
                    'eng_uuid': activity_data.engagement.uuid,
                }
            }
        elif isinstance(activity_data,
                        activities_data.AddNextStepsActivityData):
            activity_data.is_notification = True
            metadata['notification_subject'] = "New next-step was " +\
                "added to the following VF: " + activity_data.vf.name
            metadata['notification_message'] = activity_data.user.full_name \
                + " has added a next step at " +\
                dt.strftime("%Y-%m-%d %H:%M:%S") + \
                ", You can reach the dashboard by going to this link: " \
                + Constants.dashboard_href
        elif isinstance(
                activity_data, activities_data.SSHKeyAddedActivityData):
            activity_data.is_notification = True
            metadata['notification_subject'] = "You have set an SSH key"
            metadata['notification_message'] = "You have set an SSH key to " +\
                "your profile. Please allow some time for it to propagate " +\
                "across the system."

        activity_data.metadata = metadata
