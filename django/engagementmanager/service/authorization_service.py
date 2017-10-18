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
from enum import Enum
import rest_framework
from engagementmanager.models import Role, Engagement, Checklist, NextStep, VFC, \
    VF, ChecklistDecision, Notification
from engagementmanager.utils.constants import Roles
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class Permissions(Enum):
    """
    This ENUM holds all the actions that require permissions on the ICE portal
    """
    update_user = 1,  # TODO Any user can update their own account
    add_vendor = 2,  # only el or admin
    add_nextstep = 3,  # only el or admin
    complete_nextstep = 4,  # any eng member
    delete_nextstep = 5,  # only el or admin
    approve_nextstep = 6,  # only el or admin
    deny_nextstep = 7,  # only el or admin
    reset_nextstep = 8  # any eng member
    add_checklist = 9,  # only el of a given engagement
    set_checklist_decision = 10,  # TODO only el defined as owner of cl
    add_checklist_audit_log = 11,  # TODO only el defined as owner of cl
    delete_checklist_audit_log = 12,  # Do we have this capability ??
    el_review_checklist = 13,  # only checklist owner can set state.
    # only el defined as peer_viewer of given engagement and is cl owner
    peer_review_checklist = 14,
    # TODO only admin which is defined as cl owner
    admin_approve_checklist = 15,
    # TODO only el of a given engagement and is the cl owner
    handoff_checklist = 16,
    add_vf = 17,  # only standard_user
    add_vfc = 18,  # only standard_user ??
    delete_vfc = 19,  # only standard_user
    add_checklist_nextstep = 20,  # only el
    is_el_of_eng = 21,  # only el of engagement
    update_personal_next_step = 22,
    create_checklist_audit_log = 23,
    create_checklist_decision = 24,
    update_checklist_decision = 25,
    update_checklist_state = 26,
    create_deployment_target_site = 27,
    star_an_engagement = 28,
    invite = 29,
    update_account = 30,
    set_ssh = 31,
    update_password = 32,
    get_engagement_status = 34,
    put_engagement_status = 35,
    eng_membership = 36,
    delete_engagement = 37,
    view_checklist = 38,  # only non-standard-user
    get_vfc = 39,
    pull_activities = 40,
    get_deployment_target_site = 41,
    add_deployment_target_site = 42,
    delete_deployment_target_site = 43,
    export_engagments = 44,
    archive_engagement = 45,
    get_el_list = 46,
    update_engagement = 47,
    view_checklist_template = 48,
    edit_checklist_template = 49,
    delete_notification = 50,
    remove_from_engagement_team = 51,
    update_engagement_reviewers = 52,
    edit_nextstep = 54,
    order_nextstep = 60,
    set_nextstep = 56,
    edit_stage = 57,
    edit_progress_bar = 58,
    get_progress_bar = 59,
    change_lab_entry = 62,
    update_vf = 61,  # only non-standard-user
    add_feedback = 63,


class AuthorizationService:
    """
    The Authorization Service detemines whether a given action is authorized for a specific user.
    The method: is_user_able_to performs the authorization check given a user and an action (from Permissions ENUM)
    """
    role_standard_user = None
    role_el = None
    role_admin = None
    role_admin_ro = None

    def __get_role_checks(self, user, action):
        """
        Returns the list of auth checks that should be performed per user action.
        Returns None if the action is not listed in the authorized actions of the given user.
        """
        result = None

        # EL #
        if (user.role == self.role_el) and (action in self.el_permissions):
            result = self.el_permissions[action]
        # ADMIN #
        elif user.role == self.role_admin and action in self.admin_permissions:
            result = self.admin_permissions[action]
        # ADMIN Read only #
        elif user.role == self.role_admin_ro and action in self.admin_ro_permissions:
            result = self.admin_ro_permissions[action]
        # STANDRARD_USER #
        if user.role == self.role_standard_user and action in self.standard_user_permissions:
            result = self.standard_user_permissions[action]

        return result

    def __require_eng_membership(self, user, action, **kwargs):
        """
        Determines whether a given user is part of engagement team by the eng uuid
        user = IceUser
        eng = UUID as a string

        :param user: user for auth check
        :param action: action for auth check
        :param kwargs: eng_uuid, checklist_uuid, ...
        :return: Boolean, Message -> True/False if auth check succeeds/fails and a message describing auth failure
        """
        eng = kwargs['eng']

        try:
            # @UndefinedVariable
            if (user.email == eng.reviewer.email or user.email == eng.peer_reviewer.email or user.role.name == Roles.admin.name):
                return True, 'OK'
            else:
                # validate if user in Team
                if user in eng.engagement_team.all():
                    return True, 'OK'
                else:
                    return False, ""
        except Engagement.DoesNotExist:
            msg = 'User ' + user.email + ' is not a member of engagement: ' + eng.uuid + \
                ' / User is a not peer reviewer / admin of the engagement / Engagement wasnt found while fetching from DB'
            logger.info(msg)
            return False, msg
        except Exception as e:
            print(e)
            msg = 'A general error occurred while trying to validate that User ' + \
                user.email + ' is a member of engagement '
            logger.info(msg + " Error: " + str(e))
            return False, msg

    def __require_peer_review_ownership(self, user, action, **kwargs):
        """
        Determines whether the given user is the peer reviewer of the checklist
        """

        cl = kwargs['cl']
        eng = kwargs['eng']
        if cl and eng:
            # @UndefinedVariable
            if (eng.peer_reviewer == user and cl.owner == user) or (user.role.name == Roles.admin.name):
                return True, 'OK'
            else:
                return False, 'User is either not the owner of the checklist or not a peer reviewer of the checklist'
        else:
            logger.error(
                'Internal Error - Checklist/Engagement not found while trying to check permissions for user ' + user.email)
            return False, 'Internal Error - Checklist not found'

    def __require_cl_ownership(self, user, action, **kwargs):
        """
        Determines whether the given user is the owner of the checklist
        """

        cl = kwargs['cl']
        if cl:
            # @UndefinedVariable
            if cl.owner == user or user.role.name == Roles.admin.name:
                return True, 'OK'
            else:
                return False, 'User is not the owner of the checklist'
        else:
            logger.error(
                'Internal Error - Checklist not found while trying to check permissions for user ' + user.email)
            return False, 'Internal Error - Checklist not found'

    def __require_el_of_engagement(self, user, action, **kwargs):
        """
        Determines whether the given user is the el of the engagement
        """
        eng = kwargs['eng']

        if eng:
            if (user.role.name == Roles.admin.name):  # @UndefinedVariable
                return True, 'OK'
            if (user.uuid == eng.reviewer.uuid):  # @UndefinedVariable
                return True, 'OK'

            return False, 'Role Not authorized'
        else:
            logger.error(
                'Internal Error - Engagement not found while trying to check permissions for user ' + user.email)
            return False, 'Internal Error - Checklist not found'

    def __noop(self, user, action, **kwargs):
        """
        Do nothing, just authorize the action for the given user
        """
        return True, 'OK'

    def __prevent(self, user, action, **kwargs):
        """
        Do nothing, just prevent the action for the given user
        """
        return False, 'Role Not authorized'

    def __is_notification_owner(self, user, action, **kwargs):
        msg = 'Role Not authorized'
        authorized = False

        notification_uuid = request_data_mgr.get_notification_uuid()
        if notification_uuid:
            if Notification.objects.get(uuid=notification_uuid).user == user:
                authorized = True
                msg = 'OK'

        return authorized, msg

    ######################
    # EL Permissions     #
    ######################
    """
    Each Permission Map is composed of the following key-val pairs:
    Key='Action (Permission ENUM)' --> Value='Set of Checks to perform on this action.'
    """
    el_permissions = {
        Permissions.add_vf: {__noop},
        Permissions.add_feedback: {__noop},
        Permissions.update_user: {__noop},
        Permissions.add_vendor: {__noop},
        Permissions.update_vf: {__require_eng_membership},
        Permissions.add_nextstep: {__require_eng_membership},
        Permissions.complete_nextstep: {__require_eng_membership},
        Permissions.delete_nextstep: {__require_eng_membership},
        Permissions.order_nextstep: {__require_eng_membership},
        Permissions.set_nextstep: {__require_eng_membership},
        Permissions.edit_stage: {__require_eng_membership},
        Permissions.edit_progress_bar: {__require_eng_membership},
        Permissions.get_progress_bar: {__require_eng_membership},
        Permissions.change_lab_entry: {__require_eng_membership},
        Permissions.approve_nextstep: {__require_eng_membership},
        Permissions.deny_nextstep: {__require_eng_membership},
        Permissions.add_checklist: {__require_eng_membership},
        Permissions.set_checklist_decision: {__require_cl_ownership},
        Permissions.add_checklist_audit_log: {__require_cl_ownership},
        Permissions.delete_checklist_audit_log: {__require_cl_ownership},
        Permissions.el_review_checklist: {__require_cl_ownership, __require_eng_membership},
        Permissions.peer_review_checklist: {__require_peer_review_ownership},
        Permissions.handoff_checklist: {__require_cl_ownership, __require_eng_membership},
        Permissions.add_checklist_nextstep: {__require_cl_ownership, __require_eng_membership},
        Permissions.edit_nextstep: {__require_eng_membership},
        Permissions.is_el_of_eng: {__require_el_of_engagement},
        Permissions.update_personal_next_step: {__noop},
        Permissions.create_checklist_audit_log: {__require_eng_membership},
        Permissions.create_checklist_decision: {__require_eng_membership},
        Permissions.update_checklist_state: {__require_cl_ownership, __require_eng_membership},
        Permissions.create_deployment_target_site: {__require_eng_membership},
        Permissions.star_an_engagement: {__noop},
        Permissions.invite: {__require_eng_membership},
        Permissions.update_account: {__require_eng_membership},
        Permissions.set_ssh: {__require_eng_membership},
        Permissions.update_password: {},
        Permissions.delete_vfc: {__require_eng_membership},
        Permissions.get_engagement_status: {__require_eng_membership},
        Permissions.put_engagement_status: {__require_eng_membership},
        Permissions.eng_membership: {__noop},
        Permissions.delete_engagement: {__require_eng_membership},
        Permissions.view_checklist: {__require_eng_membership},
        Permissions.pull_activities: {__require_eng_membership},
        Permissions.get_deployment_target_site: {__noop},
        Permissions.add_deployment_target_site: {__noop},
        Permissions.delete_deployment_target_site: {__noop},
        Permissions.export_engagments: {__noop},
        Permissions.update_checklist_decision: {__noop},
        Permissions.get_vfc: {__noop},
        Permissions.add_vfc: {__noop},
        Permissions.delete_notification: {__is_notification_owner},
        Permissions.update_engagement: {__noop},
        Permissions.remove_from_engagement_team: {__require_eng_membership},
    }

    #################################
    # STANDARD_USER Permissions     #
    #################################
    standard_user_permissions = {
        Permissions.update_user: {__noop},
        Permissions.add_vf: {__noop},
        Permissions.add_feedback: {__noop},
        Permissions.add_vfc: {__noop},
        Permissions.get_vfc: {__require_eng_membership},
        Permissions.delete_vfc: {__require_eng_membership},
        Permissions.complete_nextstep: {__require_eng_membership},
        Permissions.update_vf: {__require_eng_membership},
        Permissions.reset_nextstep: {__require_eng_membership},
        Permissions.update_personal_next_step: {__noop},
        Permissions.update_checklist_state: {__require_cl_ownership, __require_eng_membership},
        Permissions.create_deployment_target_site: {__require_eng_membership},
        Permissions.star_an_engagement: {__noop},
        Permissions.invite: {__require_eng_membership},
        Permissions.update_account: {__require_eng_membership},
        Permissions.set_ssh: {__require_eng_membership},
        Permissions.update_password: {__require_eng_membership},
        Permissions.delete_vfc: {__require_eng_membership},
        Permissions.get_engagement_status: {__require_eng_membership},
        Permissions.eng_membership: {__noop},
        Permissions.pull_activities: {__require_eng_membership},
        Permissions.export_engagments: {__noop},
        Permissions.update_checklist_decision: {__noop},
        Permissions.remove_from_engagement_team: {__require_eng_membership},
        Permissions.delete_notification: {__is_notification_owner},
        Permissions.change_lab_entry: {__require_eng_membership},
    }

    ######################
    # ADMIN Permissions  #
    ######################
    ######################################################
    # TODO: We need to decide exactly what are the ADMIN
    # TODO: permissions. Currently it matches EL +
    # TODO: admin_approve_checklist
    ######################################################
    admin_permissions = dict(el_permissions)  # Duplicate permissions of EL
    admin_permissions.update(  # Add Extra permissions to admin
        {
            Permissions.admin_approve_checklist: {__require_cl_ownership},
            Permissions.remove_from_engagement_team: {__require_eng_membership},
            Permissions.view_checklist_template: {__noop},
            Permissions.edit_checklist_template: {__noop},
            Permissions.archive_engagement: {__noop},
            Permissions.get_el_list: {__noop},
            Permissions.update_engagement_reviewers: {__noop},
            Permissions.edit_nextstep: {__noop},
            Permissions.delete_nextstep: {__noop},
            Permissions.order_nextstep: {__noop},
            Permissions.set_nextstep: {__noop},
            Permissions.edit_stage: {__noop},
            Permissions.edit_progress_bar: {__noop},
            Permissions.get_progress_bar: {__noop},
            Permissions.change_lab_entry: {__noop},
        }
    )

    ######################
    # ADMIN Read only Permissions  #
    ######################
    admin_ro_permissions = dict()
    admin_ro_permissions.update(  # Add Extra permissions to admin_ro
        {
            Permissions.add_vf: {__prevent},
            Permissions.add_feedback: {__noop},
            Permissions.get_vfc: {__noop},
            Permissions.get_engagement_status: {__noop},
            Permissions.eng_membership: {__noop},
            Permissions.pull_activities: {__noop},
            Permissions.star_an_engagement: {__noop},
            Permissions.export_engagments: {__noop},
        }
    )

    def __init__(self):
        self.role_standard_user = self.role_el = self.role_admin = self.role_admin_ro = None
        self.__load_roles_from_db()

    def check_permissions(self, user, action, eng_uuid, role, eng, cl):
        # Retrieve the permission checks that should be performed on this user
        # role and action
        perm_checks = self.__get_role_checks(user, action)
        if not perm_checks:
            # Permission Checks were not found, it means that the action is not listed in the permitted
            # actions for the role of the user
            ret = False, 'Role ' + str(role.name) + ' is not permitted to ' + \
                str(action.name) + '/ Engagement: ' + \
                str(eng_uuid) + " isn't valid"
        else:
            # Start invoking permissions checks one by one.
            for check in perm_checks:
                ret = result, message = check(
                    self, user, action, eng=eng, cl=cl)
                if result:
                    # Permission check succeeded
                    continue
                else:
                    break  # Permission check failed

        return ret

    """
    Determines whether a user is able to perform some action.
    """

    def is_user_able_to(self, user, action, eng_uuid, checklist_uuid):
        role = user.role
        ret = True, 'OK'

        checklist_uuid = request_data_mgr.get_cl_uuid()

        # Retrieve Engagement and Checklist if their UUIDs were supplied
        eng, cl = self.__get_objects_from_db(eng_uuid, checklist_uuid)
        if eng and not eng_uuid:
            eng_uuid = eng.uuid

        ret = self.check_permissions(user, action, eng_uuid, role, eng, cl)

        return ret

    def __get_objects_from_db(self, eng_uuid, cl_uuid):
        eng = cl = None

        try:
            if eng_uuid:
                eng = Engagement.objects.get(uuid=eng_uuid)
        except Engagement.DoesNotExist:
            logger.error(
                'ENG was not found while checking permissions... returning 500')
            return None, None

        try:
            if cl_uuid:
                cl = Checklist.objects.get(uuid=cl_uuid)
                if not eng:
                    eng = cl.engagement
        except Checklist.DoesNotExist:
            logger.error('CL was not found while checking permissions')
            cl = None

        return eng, cl

    def __load_roles_from_db(self):
        self.role_standard_user, created = Role.objects.get_or_create(
            name=Roles.standard_user.name)  # @UndefinedVariable
        self.role_el, created = Role.objects.get_or_create(
            name=Roles.el.name)  # @UndefinedVariable
        self.role_admin, created = Role.objects.get_or_create(
            name=Roles.admin.name)  # @UndefinedVariable
        self.role_admin_ro, created = Role.objects.get_or_create(
            name=Roles.admin_ro.name)  # @UndefinedVariable

    def prepare_data_for_auth(self, *args, **kwargs):
        eng_uuid = None
        # Extract ENG_UUID #
        if 'eng_uuid' in kwargs:
            eng_uuid = kwargs['eng_uuid']
        elif 'engagement_uuid' in kwargs:
            eng_uuid = kwargs['engagement_uuid']
        else:
            # Extract eng_uuid from request body
            for arg in args:
                if eng_uuid != None:
                    break
                if isinstance(arg, rest_framework.request.Request):
                    try:
                        if arg.body:
                            data = json.loads(arg.body)
                            try:
                                iter(data)
                                for item in data:
                                    if 'eng_uuid' in item and item['eng_uuid']:
                                        eng_uuid = item['eng_uuid']
                                        break
                                    elif 'eng_uuid' in item and item.eng_uuid:
                                        eng_uuid = item.eng_uuid
                                        break
                                    elif item == 'eng_uuid':
                                        eng_uuid = item
                                        break
                            except TypeError:
                                if 'eng_uuid' in data and data['eng_uuid']:
                                    eng_uuid = data['eng_uuid']

                                elif 'engagement_uuid' in data and data['engagement_uuid']:
                                    eng_uuid = data['engagement_uuid']
                    except Exception as e:
                        print(e)
                        pass

        request_data_mgr.set_eng_uuid(eng_uuid)

        # Extract CHECKLIST_UUID #
        if 'checklistUuid' in kwargs:
            request_data_mgr.set_cl_uuid(kwargs['checklistUuid'])
            if (eng_uuid == None):
                try:
                    eng_uuid = Checklist.objects.get(
                        uuid=request_data_mgr.get_cl_uuid()).engagement.uuid
                    request_data_mgr.set_eng_uuid(eng_uuid)
                except Checklist.DoesNotExist:
                    raise Exception("auth service couldn't fetch Checklist by checklist uuid=" +
                                    request_data_mgr.get_cl_uuid())
                except Exception as e:
                    raise Exception(
                        "Failed fetching engagement uuid from checklist " + request_data_mgr.get_cl_uuid())

        # Extract engagement by NEXTSTEP_UUID #
        if 'ns_uuid' in kwargs:
            request_data_mgr.set_ns_uuid(kwargs['ns_uuid'])
            if (eng_uuid == None):
                next_step = None
                try:
                    next_step = NextStep.objects.get(
                        uuid=request_data_mgr.get_ns_uuid())
                except NextStep.DoesNotExist:
                    raise Exception("auth service couldn't fetch NextStep by nextstep uuid=" +
                                    request_data_mgr.get_ns_uuid())

                try:
                    eng_uuid = next_step.engagement.uuid
                    request_data_mgr.set_eng_uuid(eng_uuid)
                except:
                    # If we've gotten here it means that the next_step doesn't have attached
                    # engagement (e.g personal next_step)
                    pass

        # Extract engagement by VFC
        if ('uuid' in kwargs):
            from engagementmanager.rest.vfc import VFCRest
            if (isinstance(args[0], VFCRest) == True):
                try:
                    vfc = VFC.objects.get(uuid=kwargs['uuid'])
                    if (eng_uuid == None):
                        eng_uuid = vfc.vf.engagement.uuid
                        request_data_mgr.set_eng_uuid(eng_uuid)
                except VFC.DoesNotExist:
                    raise Exception(
                        "auth service couldn't fetch vfc by vfc uuid=" + kwargs['uuid'])

        # Extract engagement by VF (unfortunately the url exposed by the server
        # get uuid as a parameter and serve both vf and vfc APIs) #
        if 'vf_uuid' in kwargs and eng_uuid == None:
            try:
                eng_uuid = VF.objects.get(
                    uuid=kwargs['vf_uuid']).engagement.uuid
                request_data_mgr.set_eng_uuid(eng_uuid)
            except VF.DoesNotExist:
                logger.error(
                    "Prepare_data_for_auth: Couldn't fetch engagement object from VF, trying to fetch from VFC...")
                vfc = None
                try:
                    vfc = VFC.objects.get(uuid=kwargs['vf_uuid'])
                    if (vfc != None):
                        eng_uuid = vfc.vf.engagement.uuid
                        request_data_mgr.set_eng_uuid(eng_uuid)
                except VFC.DoesNotExist:
                    logger.error(
                        "Prepare_data_for_auth: Couldn't fetch engagement object from VFC")

        # Extract engagement by ChecklistDecision
        if 'decision_uuid' in kwargs and eng_uuid == None:
            try:
                eng_uuid = ChecklistDecision.objects.get(
                    uuid=kwargs['decision_uuid']).checklist.engagement.uuid
                request_data_mgr.set_eng_uuid(eng_uuid)
            except ChecklistDecision.DoesNotExist:
                logger.error(
                    "Prepare_data_for_auth: Couldn't fetch engagement object from ChecklistDecision")

        # Extract notification uuid for permission check
        if 'notif_uuid' in kwargs:
            request_data_mgr.set_notification_uuid(kwargs['notif_uuid'])

        return eng_uuid
