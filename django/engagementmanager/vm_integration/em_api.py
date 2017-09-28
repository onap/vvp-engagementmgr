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
from django.core.exceptions import ObjectDoesNotExist
from engagementmanager.slack_client.api import SlackClient
from engagementmanager.models import Checklist, VF
from engagementmanager.service.checklist_service import CheckListSvc
from engagementmanager.service.checklist_state_service import set_state
from engagementmanager.utils import dict_path_get
from engagementmanager.utils.constants import CheckListCategory, CheckListState, EngagementStage
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def test_finished_callback(checklist_test_results):
    logger.debug(
        "test_finished_callback has signaled that a test has finished with test results %r", checklist_test_results)

    if not checklist_test_results:
        msg = "Couldn't find payload argument inside kwargs array, aborting signal"
        logger.error(msg)
        raise KeyError(msg)

    checklist_test_results['description'] = "Validation manager has indicated that checklist {} tests has been completed with results".format(
        checklist_test_results['checklist_uuid'])

    checklist = Checklist.objects.get(
        uuid=checklist_test_results['checklist_uuid'])
    request_data_mgr.set_cl_uuid(checklist.uuid)
    data = CheckListSvc().setChecklistDecisionsFromValMgr(
        user=checklist.owner,
        checklist_uuid=checklist_test_results['checklist_uuid'],
        decisions=checklist_test_results['decisions'],
        checklist_results_from_jenkins=checklist_test_results
    )
    return data


def git_push_callback(gitlab_data):
    """
    When we are notified that a repo has received a push, we must reject any checklists not in the
    closed or archived state whose associated files have been modified.
    """
    logger.debug("Validation manager has signaled that a git push has occurred")
    msg = "OK"
    data = None

    # sanity check provided arguments
    for key in ['project', 'project/git_ssh_url', 'commits']:
        if not dict_path_get(gitlab_data, key):
            msg = "{!r} in the git_push signal gitlab_data is missing or empty.".format(
                key)
            logger.error(msg)
            raise KeyError(msg)

    # For now, ignore pushes made to any branch other than 'master'.
    if gitlab_data['ref'] != u'refs/heads/master':
        logger.warn("A non-master ref %r was updated. Ignoring.",
                    gitlab_data['ref'])
        return None

    # sanity check payload data
    if int(gitlab_data['total_commits_count']) == 0:
        logger.debug("total_commits_count = %s",
                     gitlab_data['total_commits_count'])
        msg = "Something is wrong: Number of commits is 0 even after a push event has been invoked from validation manager to engagement manager"
        logger.warn(msg)
        raise ValueError(msg)

    if gitlab_data['before'] == '0000000000000000000000000000000000000000':
        logger.debug('This is the first commit pushed to master.')

    git_ssh_url = gitlab_data['project']['git_ssh_url']

    vf = VF.objects.filter(git_repo_url=git_ssh_url)

    if len(vf) == 0:
        msg = "Couldn't fetch any VF"
        logger.error(msg)
        raise ObjectDoesNotExist(msg)
    else:
        vf = VF.objects.get(git_repo_url=git_ssh_url)

    checklists = (Checklist.objects
                  .filter(engagement=vf.engagement)
                  # @UndefinedVariable
                  .exclude(state=CheckListState.archive.name)
                  .exclude(state=CheckListState.closed.name))  # @UndefinedVariable

    committed_files = set(file
                          for commit in gitlab_data['commits']
                          for status in ['added', 'modified', 'removed']
                          for file in commit[status])
    logger.debug("Committed files list: [%s]" % ', '.join(committed_files))

    # send notifications to reviewers and peer reviewers when the git repo is
    # updated
    vf_name = vf.name
    engagement_manual_id = vf.engagement.engagement_manual_id
    reviewer = vf.engagement.reviewer
    peer_reviewer = vf.engagement.peer_reviewer
    slack_client = SlackClient()
    slack_client.send_notifications_on_git_push(
        engagement_manual_id, vf_name, reviewer, peer_reviewer, committed_files)

    # loop through the checklists and start automation if necessary
    for checklist in checklists:
        user = checklist.owner
        template_category = checklist.template.category
        mutual_files = committed_files.intersection(
            json.loads(checklist.associated_files))
        logger.debug("Mutual files list for checklist %s: [%s]" % (
            checklist.uuid, ', '.join(committed_files)))
        if not mutual_files and\
           template_category == CheckListCategory.heat.name and\
           not any(file
                   for file in committed_files
                   for extension in ['.yaml', '.yml', '.env']
                   if file.lower().endswith(extension)):
            continue
        if checklist.state == CheckListState.pending.name:  # @UndefinedVariable
            description = "Checklist {checklist.name} (part of VF {vf.name}/{vf.uuid}) in Pending state will transition to Automation due to a push action on files [{mutual_files}]. chosen EL: {user.full_name}".format(
                checklist=checklist,
                vf=vf,
                mutual_files=", ".join(mutual_files),
                user=user,
            )
        else:
            description = "Checklist {checklist.uuid} (part of VF {vf.name}/{vf.uuid}) has been rejected due to a push action made on files [{mutual_files}]. chosen EL is: {user.full_name}".format(
                checklist=checklist,
                vf=vf,
                mutual_files=", ".join(mutual_files),
                user=user,
            )
        logger.debug(description)
        # FIXME Setting parameters into a global before calling a function that will break without
        # them is TERRIBLE. We must fix this before we open-source this code.
        request_data_mgr.set_cl_uuid(checklist.uuid)
        request_data_mgr.set_user(user)
        data = set_state(  # means that the checklist will be declined and a cloned one is
            # created in PENDING status
            decline=True,
            checklist_uuid=checklist.uuid,
            # means the checklist will be triggered into automation cycle
            isMoveToAutomation=True,
            description="This change was triggered by an update to the engagement git repository.")

        logger.debug("set_state returned (%r)" % data)

    return data
