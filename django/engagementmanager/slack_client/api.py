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
import concurrent.futures
from django.conf import settings
from slacker import Slacker, Error
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


class SlackClient(object):
    """
    ICE Slack API Client
    """

    def __init__(self):
        """
        Ice Slack client constructor ->
        """
        super(SlackClient, self).__init__()

        # create the slack client
        self.client = None
        if settings.SLACK_API_TOKEN is not None and \
                settings.SLACK_API_TOKEN != "":
            try:
                self.client = Slacker(settings.SLACK_API_TOKEN)
            except Exception as exception:
                logger.error(
                    'Unknown error while creating the a slack client: ' +
                    str(exception))

    # post a message via the Slack API
    def trigger_slack_chat_post_message(self, to, message):
        """
        # Syntax for chat.post_message
        def post_message(self, channel, text=None, username=None, as_user=None,
             parse=None, link_names=None, attachments=None,
             unfurl_links=None, unfurl_media=None, icon_url=None,
             icon_emoji=None):
             """
        try:
            # Send a message to a channel or a user
            self.client.chat.post_message(to, message)
        except Error as e:
            logger.error('Invalid Slack API token was provided: ' + str(e))
        except Exception as exception:
            logger.error(
                'Unknown error while posting a message to Slack: ' +
                str(exception))

    # asynchronously post a message
    def post_message(self, to, message):
        """
        Post a message to a channel or user
        """
        if self.client is None:
            return None

        if to and message:
            logger.debug('Trigger Slack API - chat.post_message')
            executor.submit(
                self.trigger_slack_chat_post_message, to, message)
            logger.debug(
                'Continuing after triggering the Slack API - \
                chat.post_message')

    # send slack message to the engagement channel
    def update_engagement_channel(self, message, notify_channel=False):
        prefix = ''
        if notify_channel:
            prefix = '<!channel> '
        if settings.ENGAGEMENTS_CHANNEL:
            # post to the engagement channel
            self.post_message(settings.ENGAGEMENTS_CHANNEL, prefix + message)

    # send slack message to the devops channel
    def update_devops_channel(self, message, notify_channel=False):
        prefix = ''
        if notify_channel:
            prefix = '<!channel> '
        if settings.DEVOPS_CHANNEL:
            # post to the engagement channel
            self.post_message(settings.DEVOPS_CHANNEL, prefix + message)

    # send slack message to a user
    def send_message_to_user(self, user, message):
        # send Slack message to the newly assigned user
        if user and user.slack_handle:
            self.post_message('@' + user.slack_handle, message)

    # update reviewer or peer reviewer when a new engagement is created
    def update_reviewer_or_peer_reviewer(
            self,
            engagement_manual_id,
            vf_name,
            user,
            old_user,
            notification_type='reviewer'):
        # construct the Slack messages
        user_message = 'You have been assigned as the \
        _{}_ for the engagement _{}: {}_. '.format(
            notification_type, engagement_manual_id, vf_name)
        old_user_message_postfix = 'The assigned _{}_ is now _{}_.'.format(
            notification_type, user.full_name)

        user_message_postfix = ""
        old_user_message = ""
        if old_user is not None:
            user_message_postfix = 'The previously assigned _{}_ was _{}_ in \
            case you need to reach out for questions.'.format(
                notification_type, old_user.full_name)
            old_user_message = 'You are no longer the assigned _{}_ for the \
            engagement _{}: {}_. '.format(
                notification_type, engagement_manual_id, vf_name)

        # send Slack messages
        self.send_message_to_user(user, user_message + user_message_postfix)
        self.send_message_to_user(
            old_user, old_user_message + old_user_message_postfix)

    # update the engagement channel when a new engagement is created
    def update_engagement_channel_for_new_engagement(
            self, engagement_manual_id, vf_name, reviewer,
            peer_reviewer, creator):
        new_engagement_message = '_{}_ created a new engagement _{}: {}_. \
        _{}_ was assigned as the reviewer and \
        _{}_ as the peer reviewer'.format(
            creator.full_name, engagement_manual_id, vf_name,
            reviewer.full_name, peer_reviewer.full_name)
        self.update_engagement_channel(new_engagement_message, True)

    # update reviewer, peer reviewer and the engagement channel when a new
    # engagement is created
    def send_slack_notifications_for_new_engagement(
            self,
            engagement_manual_id,
            vf_name,
            reviewer,
            peer_reviewer,
            creator):
        self.update_reviewer_or_peer_reviewer(
            engagement_manual_id, vf_name, reviewer, None, 'reviewer')
        self.update_reviewer_or_peer_reviewer(
            engagement_manual_id, vf_name, peer_reviewer, None,
            'peer reviewer')
        self.update_engagement_channel_for_new_engagement(
            engagement_manual_id, vf_name, reviewer, peer_reviewer, creator)

    def send_slack_notifications_for_new_feedback(self, feedback, user):
        new_feedback_message = 'Created a new Feedback by {} Description : \
        {}.'.format(
            user.full_name, feedback.description)
        self.update_engagement_channel(new_feedback_message, True)
        self.update_devops_channel(new_feedback_message, True)

    # update the engagement channel when the stage is changed for an engagement
    def update_for_change_of_the_engagement_stage(
            self, engagement_manual_id, vf_name, stage):
        change_engagement_stage_message = 'The engagement _{}: \
        {}_ was moved to the _{}_ stage.'.format(
            engagement_manual_id, vf_name, stage)
        self.update_engagement_channel(change_engagement_stage_message)

    # update the engagement channel when an engagement is archived
    def update_for_archived_engagement(
            self, engagement_manual_id, vf_name, reason):
        archived_engagement_message = 'The engagement _{}: \
        {}_ was archived because of this reason: _{}_.'.format(
            engagement_manual_id, vf_name, reason)
        self.update_engagement_channel(archived_engagement_message)

    # update the reviewer and peer reviewer when the git repository is updated
    def send_notifications_on_git_push(
            self,
            engagement_manual_id,
            vf_name,
            reviewer,
            peer_reviewer,
            committed_files):
        str_committed_files = "The following files was added \
        or changed as part of the commit:\n\n- %s" % '\n- '.join(
            committed_files)
        message = 'The Git repository for the engagement _{}: \
        {}_ in which you are assigned as a _{}_ was updated. ' + \
            str_committed_files
        self.send_message_to_user(reviewer, message.format(
            engagement_manual_id, vf_name, 'reviewer'))
        self.send_message_to_user(peer_reviewer, message.format(
            engagement_manual_id, vf_name, 'peer_reviewer'))

    def send_notifications_bucket_image_update(
            self,
            engagement_manual_id,
            vf_name,
            reviewer,
            peer_reviewer,
            bucket_name):
        str_committed_files = "The following bucket was updated with new image files: %s" % bucket_name
        message = 'The rgwa bucket for the engagement _{}: {}_ in which you are assigned as a _{}_ was updated. ' + \
            str_committed_files
        self.send_message_to_user(
            reviewer,
            message.format(
                engagement_manual_id,
                vf_name,
                'reviewer'))
        self.send_message_to_user(
            peer_reviewer,
            message.format(
                engagement_manual_id,
                vf_name,
                'peer_reviewer'))

    # update the reviewer when the automation phase is completed for a
    # checklist
    def send_notification_to_reviewer_when_automation_completes(
            self, engagement_manual_id, vf_name, reviewer, checklist_name):
        message = 'The automation phase completed for the checklist _{}_ under the engagement _{}: {}_. You can now start your review of it.'
        self.send_message_to_user(
            reviewer,
            message.format(
                checklist_name,
                engagement_manual_id,
                vf_name))

    # update the peer reviewer when the review phase is completed for a
    # checklist
    def send_notification_to_peer_reviewer_when_the_review_completes(
            self, engagement_manual_id, vf_name, reviewer, peer_reviewer,
            checklist_name):
        message = 'The review phase was completed by _{}_ for the checklist \
        _{}_ under the engagement _{}: {}_. \
        You can now start your peer review of it.'
        self.send_message_to_user(peer_reviewer, message.format(
            reviewer.full_name, checklist_name,
            engagement_manual_id, vf_name))

    # update the admins when the review and peer reviews have been completed
    # for a checklist
    def send_notification_to_admins_when_the_peer_review_completes(
            self,
            engagement_manual_id,
            vf_name,
            reviewer,
            peer_reviewer,
            admins,
            checklist_name):
        message = 'The manual reviews have been completed by the reviewer \
        _{}_ and peer reviewer _{}_ for the checklist _{}_ under the \
        engagement _{}: {}_. It is now waiting for an approval by you \
        or any other admin.'
        for admin in admins:
            self.send_message_to_user(
                admin,
                message.format(
                    reviewer.full_name,
                    peer_reviewer.full_name,
                    checklist_name,
                    engagement_manual_id,
                    vf_name))

    # update reviewer when a checklist is approved
    def send_notification_to_reviewer_when_approved(
            self, engagement_manual_id, vf_name, reviewer, checklist_name):
        message = 'The checklist _{}_ under the engagement _{}: {}_ is \
        now approved. You can now hand off the artifacts and close \
        out the checklist.'
        self.send_message_to_user(reviewer, message.format(
            checklist_name, engagement_manual_id, vf_name))

    # update reviewer, peer reviewer and admins when a checklist is closed
    def send_notifications_when_closed(
            self,
            engagement_manual_id,
            vf_name,
            reviewer,
            peer_reviewer,
            admins,
            checklist_name):
        message = 'The checklist _{}_ under the engagement _{}: {}_ has now \
        been closed and all the asssociated artifacts are validated. The \
        reviewer was _{}_ and the peer reviewer was _{}_.'
        self.send_message_to_user(
            reviewer,
            message.format(
                checklist_name,
                engagement_manual_id,
                vf_name,
                reviewer.full_name,
                peer_reviewer.full_name))
        self.send_message_to_user(
            peer_reviewer,
            message.format(
                checklist_name,
                engagement_manual_id,
                vf_name,
                reviewer.full_name,
                peer_reviewer.full_name))
        for admin in admins:
            self.send_message_to_user(
                admin,
                message.format(
                    checklist_name,
                    engagement_manual_id,
                    vf_name,
                    reviewer.full_name,
                    peer_reviewer.full_name))
