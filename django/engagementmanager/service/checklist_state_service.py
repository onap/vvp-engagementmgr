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
from django.db.models import Q
from django.utils import timezone
from engagementmanager.decorator.auth import auth
from engagementmanager.slack_client.api import SlackClient
from engagementmanager.models import ChecklistDecision, Checklist, \
    IceUserProfile, VF, ChecklistLineItem, ChecklistAuditLog, Role
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.service.checklist_audit_log_service import \
    addAuditLogToChecklist
from engagementmanager.service.engagement_service import \
    update_or_insert_to_recent_engagements, update_eng_validation_details
from engagementmanager.utils.constants import CheckListState, \
    CheckListDecisionValue, Roles, RecentEngagementActionType
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.vm_integration.vm_client import \
    send_cl_from_pending_to_automation_event
from rest_framework.exceptions import MethodNotAllowed
import random
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def insert_to_recent_engagements(owner=None, action=None, vf=None):
    if not vf:
        # If VF wasn't supplied let's fetch it using checklist and
        # checklist.engagement
        checkListObj = Checklist.objects.get(
            uuid=request_data_mgr.get_cl_uuid())
        vf = VF.objects.get(engagement=checkListObj.engagement)

    logger.debug("Adding vf " + str(vf.uuid) +
                 " to recent engagements table for user " + owner.full_name)
    update_or_insert_to_recent_engagements(
        owner.uuid, vf, action)  # @UndefinedVariable


def description_creator(checklist, next_state, additional_comment=""):
    if additional_comment:
        description = "The " + checklist.name + " \
        checklist was changed to the " +\
            next_state.lower() + " state. " + "\n" +\
            additional_comment
    else:
        description = "The " + checklist.name + \
            " checklist was changed to the " +\
                      next_state.lower() + " state."
    return description


'''
 If kwargs['isMoveToAutomation']==True than the CL will not be \
 cloned but reverted to automation, else (False) will be cloned \
 and returned in pending
'''


def set_state(decline, checklist_uuid, isMoveToAutomation=True,
              description=None):
    logger.debug('set_state(decline=%r,checklist_uuid=%r,\
    get_request_data_vars= %r)',
                 decline, checklist_uuid,
                 request_data_mgr.get_request_data_vars())

    if checklist_uuid:
        request_data_mgr.set_cl_uuid(checklist_uuid)

    if any(x is None for x in [checklist_uuid,
                               request_data_mgr.get_user(), description]):
        msg = "checklist uuid or user or description is None"
        logger.error(msg)
        msg = "checklist state wasn't change due to bad parameters"
        raise KeyError(msg)

    additional_comment = description

    checklist = retrieve_checklist_object(checklist_uuid)

    # get metadata for slack notifications
    slack_client = SlackClient()
    checklist_name = checklist.name
    engagement = checklist.engagement
    reviewer = engagement.reviewer
    peer_reviewer = engagement.peer_reviewer
    engagement_manual_id = ''
    if engagement is not None:
        engagement_manual_id = engagement.engagement_manual_id

    vf = VF.objects.get(engagement__uuid=engagement.uuid)
    vf_name = ""
    if vf is not None:
        vf_name = vf.name

    if not checklist:
        msg = "checklist state wasn't change due to bad parameters"
        raise KeyError(msg)

    # @UndefinedVariable
    if checklist.state == CheckListState.closed.name or \
            checklist.state == CheckListState.archive.name:
        msg = "attempt to change state to the next one \
        from 'closed'/'archive', no actions were made."
        logger.error(msg)
        msg = "checklist's state is already closed/archive, \
        can not move forward in states."
        raise FileExistsError(msg)

    elif decline and checklist.state != CheckListState.pending.name:
        logger.debug(
            'set_state: decline and not pending -< about to set the \
            state to ARCHIVE and duplicate the checklist')
        set_state_to_archive(isMoveToAutomation, description)

        # @UndefinedVariable
        return check_sts(checklist, request_data_mgr.get_user(),
                         CheckListState.archive.name, additional_comment)

    elif checklist.state == CheckListState.pending.name:  # @UndefinedVariable
        logger.debug('set_state: pending to automation')
        set_state_to_automation()

        # @UndefinedVariable
        return check_sts(checklist, request_data_mgr.get_user(),
                         CheckListState.automation.name, additional_comment)

    # this case is when getting a signal from VM that jenkins has finished all
    # tests
    elif checklist.state == CheckListState.automation.name:
        logger.debug('set_state: automation to review')
        set_state_to_review(checklist)
        slack_client.send_notification_to_reviewer_when_automation_completes(
            engagement_manual_id, vf_name, reviewer, checklist_name)

        # @UndefinedVariable
        return check_sts(checklist, request_data_mgr.get_user(),
                         CheckListState.review.name, additional_comment)

    elif checklist.state == CheckListState.review.name:
        logger.debug('set_state: review to peer review')
        set_state_to_peer_review()
        slack_client.\
            send_notification_to_peer_reviewer_when_the_review_completes(
                engagement_manual_id, vf_name, reviewer, peer_reviewer,
                checklist_name)

        # @UndefinedVariable
        return check_sts(checklist, request_data_mgr.get_user(),
                         CheckListState.peer_review.name, additional_comment)

    elif checklist.state == CheckListState.peer_review.name:
        logger.debug('set_state: peer review to approval')
        set_state_to_approval()
        admins = IceUserProfile.objects.filter(role__name=Roles.admin.name)
        slack_client.\
            send_notification_to_admins_when_the_peer_review_completes(
                engagement_manual_id,
                vf_name, reviewer, peer_reviewer, admins,
                checklist_name)

        # @UndefinedVariable
        return check_sts(checklist, request_data_mgr.get_user(),
                         CheckListState.approval.name, additional_comment)

    elif checklist.state == CheckListState.approval.name:
        logger.debug('set_state: approval to handoff')
        set_state_to_handoff()
        slack_client.send_notification_to_reviewer_when_approved(
            engagement_manual_id, vf_name, reviewer, checklist_name)

        # @UndefinedVariable
        return check_sts(checklist, request_data_mgr.get_user(),
                         CheckListState.handoff.name, additional_comment)

    elif checklist.state == CheckListState.handoff.name:
        logger.debug('set_state: handoff to closed')
        set_state_to_closed()
        admins = IceUserProfile.objects.filter(role__name=Roles.admin.name)
        slack_client.send_notifications_when_closed(
            engagement_manual_id, vf_name, reviewer, peer_reviewer,
            admins, checklist_name)

        # @UndefinedVariable
        return check_sts(checklist, request_data_mgr.get_user(),
                         CheckListState.closed.name, additional_comment)


def duplicate_checklist_and_its_auditlogs(checklist, isMoveToAutomation):
    ''' Create the basic duplicated checklist
    object based on the original one '''

    newState = CheckListState.pending.name  # @UndefinedVariable
    checklistDupObject = Checklist.objects.create(
        name=checklist.name,
        validation_cycle=checklist.validation_cycle + 1,
        associated_files=checklist.associated_files,
        engagement=checklist.engagement,
        template=checklist.template,
        creator=checklist.creator,
        owner=checklist.creator,
        state=newState)

    ''' Fetch all original cl audit logs and attach it to the \
    duplicated one '''
    audits = ChecklistAuditLog.objects.filter(checklist=checklist)
    for item in audits:
        audit = addAuditLogToChecklist(
            checklistDupObject, item.description, item.creator)

        if not audit:
            logger.error(
                "duplicate_checklist_and_its_auditlogs: Failed to \
                create a duplicated audit log in the DB")
            msg = "checklist state wasn't change"
            raise Exception(msg)

    ''' Fetch all original line items and attach it to the duplicated one '''
    line_items_list = ChecklistLineItem.objects.filter(
        template=checklist.template)
    for lineitem in line_items_list:
        old_decisions = ChecklistDecision.objects.filter(
            lineitem=lineitem, checklist=checklist,
            template=checklist.template)
        if len(old_decisions) == 0:
            new_decision = ChecklistDecision.objects.create(
                checklist=checklistDupObject,
                template=checklistDupObject.template, lineitem=lineitem)
        else:
            for decision in old_decisions:
                new_decision = ChecklistDecision.objects.create(
                    checklist=checklistDupObject,
                    template=checklist.template, lineitem=lineitem)
                old_decision_auditlogs = ChecklistAuditLog.objects.filter(
                    decision=decision)
                for audit in old_decision_auditlogs:
                    audit = ChecklistAuditLog.objects.create(
                        decision=new_decision, description=audit.description,
                        category='', creator=audit.creator)
    # This is a scenario in which we send to VM
    # cl_from_pending_to_automation_event
    if isMoveToAutomation:
        logger.debug("Cloned Checklist is triggered as to automation")
        try:
            set_state_to_automation(checklistDupObject)
        except KeyError:
            # delete new checklist since
            # we don't want duplicate checklist while
            # the other one is still not archived
            checklistDupObject.delete()

    return checklistDupObject


def check_sts(checklist, user, next_state, additional_comment):
    description = description_creator(
        checklist, next_state, additional_comment=additional_comment)
    if not description:
        msg = "failed to set the state to the next one due to \
        invalid parameters."
        raise ValueError(msg)
    addAuditLogToChecklist(checklist, description, user)
    return checklist


def check_decision_meet_criterias(checkListObj, review_type):
    if not type:
        return True

    if review_type == 'review_value':
        invalid_decisions = ChecklistDecision.objects.filter(
            Q(checklist=checkListObj) &
            (
                Q(review_value=CheckListDecisionValue.na.name)
                | Q(review_value=CheckListDecisionValue.denied.name)
            )).count()  # @UndefinedVariable
    elif review_type == 'peer_review_value':
        invalid_decisions = ChecklistDecision.objects.filter(
            Q(checklist=checkListObj) &
            (
                Q(peer_review_value=CheckListDecisionValue.na.name) |
                Q(peer_review_value=CheckListDecisionValue.denied.name)
            )).count()  # @UndefinedVariable
    else:
        return True

    if invalid_decisions:
        msg = "checklist state wasn't change, \
        not all decisions are approved / na"
        raise MethodNotAllowed(msg)


def retrieve_checklist_and_its_decisions(cluuid, review_type):
    checkListObj = retrieve_checklist_object(cluuid)
    if not checkListObj:
        msg = "checklist state wasn't change"
        raise KeyError(msg)
    check_decision_meet_criterias(checkListObj, review_type)
    return checkListObj


def retrieve_checklist_object(cluuid):
    checklist = Checklist.objects.get(uuid=cluuid)
    return checklist


"""
This method is called when an EL / Peer Reviewer declines a CL or \
creates a Next step for them after declining a specific line item in the CL.
"""


@auth(Permissions.set_checklist_decision, is_internal=True)
def set_state_to_archive(isMoveToAutomation=True, description=None):
    checkListObj = retrieve_checklist_and_its_decisions(
        request_data_mgr.get_cl_uuid(), '')

    rejection_description = description_creator(
        checkListObj, CheckListState.archive.name, description)
    addAuditLogToChecklist(
        checkListObj, rejection_description, request_data_mgr.get_user())
    checklistDupObject = duplicate_checklist_and_its_auditlogs(
        checkListObj, isMoveToAutomation)
    checkListObj.state = CheckListState.archive.name
    checkListObj.owner = checkListObj.creator
    checkListObj.update_time = timezone.now()

    checkListObj.save()

    return checklistDupObject


def set_state_to_automation(checkListObj=None):
    if checkListObj is None:
        checkListObj = retrieve_checklist_object(
            request_data_mgr.get_cl_uuid())

    if checkListObj.associated_files == [] or not \
            checkListObj.associated_files:
        logger.error(
            "set_state_to_automation failed: no files were \
            found in the checkListObj.associated_file")
        msg = "checklist state wasn't change, please add files \
        to the checklist in order to start Automation state"
        raise KeyError(msg)
    originalState = checkListObj.state
    checkListObj.state = CheckListState.automation.name
    checkListObj.update_time = timezone.now()

    checkListObj.save()

    if originalState == CheckListState.pending.name:
        send_cl_from_pending_to_automation_event(checkListObj)


def set_state_to_review(checkListObj):
    checkListObj.state = CheckListState.review.name
    checkListObj.update_time = timezone.now()
    # set the owner to reviewer and update_or_insert_to_recent_engagements(...)

    checkListObj.save()


@auth(Permissions.el_review_checklist, is_internal=True)
def set_state_to_peer_review():
    """
    This method is called when EL approves a review
    and moves a CL to peer_review
    """
    checkListObj = retrieve_checklist_and_its_decisions(
        request_data_mgr.get_cl_uuid(), 'review_value')
    checkListObj.state = CheckListState.peer_review.name
    checkListObj.owner = checkListObj.engagement.peer_reviewer

    insert_to_recent_engagements(
        owner=checkListObj.owner,
        action=RecentEngagementActionType.GOT_OWNERSHIP_OVER_ENGAGEMENT.name)

    checkListObj.update_time = timezone.now()

    checkListObj.save()


@auth(Permissions.peer_review_checklist, is_internal=True)
def set_state_to_approval():
    """
    This method is called when Peer Reviewer approves a
    review and moves a CL to approval state
    """
    checkListObj = retrieve_checklist_and_its_decisions(
        request_data_mgr.get_cl_uuid(), 'peer_review_value')
    checkListObj.state = CheckListState.approval.name
    admin_role = Role.objects.get(name=Roles.admin.name)

    admin_list = IceUserProfile.objects.all().filter(
        role=admin_role)
    if admin_list.count() < 1:
        logger.error("Failed to save the new state \
        of the Checklist to the DB")
        msg = "checklist state wasn't change due to server error"
        raise Exception(msg)

    rand_admin = admin_list[random.randint(0, admin_list.count() - 1)]
    admin = IceUserProfile.objects.get(uuid=rand_admin.uuid)

    checkListObj.update_time = timezone.now()
    checkListObj.owner = admin
    insert_to_recent_engagements(
        owner=checkListObj.owner,
        action=RecentEngagementActionType.GOT_OWNERSHIP_OVER_ENGAGEMENT.name)

    checkListObj.save()


@auth(Permissions.admin_approve_checklist)
def set_state_to_handoff():
    """
    This method is called when an admin approves
    a CL and moves it to a handoff state
    """
    checkListObj = retrieve_checklist_and_its_decisions(
        request_data_mgr.get_cl_uuid(), '')
    checkListObj.state = CheckListState.handoff.name
    checkListObj.owner = checkListObj.creator

    insert_to_recent_engagements(
        owner=checkListObj.owner,
        action=RecentEngagementActionType.GOT_OWNERSHIP_OVER_ENGAGEMENT.name)

    checkListObj.update_time = timezone.now()

    checkListObj.save()


@auth(Permissions.handoff_checklist)
def set_state_to_closed():
    """
    This method is called when an EL approves the handoff
    and moves the CL to closed state
    """
    checkListObj = retrieve_checklist_and_its_decisions(
        request_data_mgr.get_cl_uuid(), '')
    checkListObj.state = CheckListState.closed.name
    checkListObj.owner = checkListObj.creator
    checkListObj.update_time = timezone.now()
    update_eng_validation_details(checkListObj)
    checkListObj.save()
