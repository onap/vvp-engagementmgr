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
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.aggregates import Max
from engagementmanager.apps import bus_service
from engagementmanager.bus.messages.activity_event_message import \
    ActivityEventMessage
from engagementmanager.git.git_manager import GitManager
from engagementmanager.models import ChecklistTemplate, \
    Checklist, Engagement, \
    ChecklistAuditLog, ChecklistDecision, ChecklistLineItem, \
    IceUserProfile, VF, \
    ChecklistSection, Role
from engagementmanager.serializers import ThinChecklistModelSerializer, \
    ThinChecklistAuditLogModelSerializer, \
    ThinChecklistDecisionModelSerializer, \
    ThinPostChecklistResponseModelSerializer, \
    ChecklistTemplateModelSerializer, \
    ChecklistSectionModelSerializer, ChecklistLineItemModelSerializer
from engagementmanager.service.checklist_audit_log_service import \
    addAuditLogToDecision, addAuditLogToChecklist
from engagementmanager.service.checklist_decision_service import setDecision
from engagementmanager.service.checklist_state_service import set_state
from engagementmanager.service.base_service import BaseSvc
from engagementmanager.utils.constants import Roles, CheckListState, \
    CheckListLineType
from engagementmanager.utils.activities_data import TestFinishedActivityData
from engagementmanager.utils.vvp_exceptions import VvpObjectNotAvailable
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.utils.validator import logEncoding
from engagementmanager.vm_integration.vm_client import \
    send_jenkins_job_and_gitlab_repo_exists, executor
from validationmanager.em_integration.vm_api import get_jenkins_build_log
import json
import time
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class CheckListSvc(BaseSvc):

    def retreive_cl_files_for_engagment(self, eng_uuid):
        vf_associated_files_list = []

        checklists_of_eng = Checklist.objects.filter(
            engagement__uuid=eng_uuid).exclude(
            state=CheckListState.archive.name).exclude(
            state=CheckListState.closed.name)

        for checklistObj in checklists_of_eng:
            associated_files = json.loads(checklistObj.associated_files)
            vf_associated_files_list = \
                vf_associated_files_list + associated_files
        return vf_associated_files_list

    def getDataForCreateNewChecklist(self, user, eng_uuid):
        engagement = Engagement.objects.get(uuid=eng_uuid)
        vf = engagement.vf

        if not send_jenkins_job_and_gitlab_repo_exists(vf):
            msg = "Jenkins job or gitlab repo is still missing"
            logger.error(msg)
            return False

        # Get all templates
        data = self.getChecklistTemplates()

        data['checkListAssociatedFiles'] = \
            self.gitManager.getRepoAssociatedFilesForUser(
            eng_uuid)
        return data

    def getChecklistTemplates(self, templateUuid=None):
        """Return  checklist template with
        nested sections and their nested line items"""
        data = dict()
        if not templateUuid:
            checkListTemplates = ChecklistTemplate.objects.all()
            if (checkListTemplates):
                data['checkListTemplates'] = ChecklistTemplateModelSerializer(
                    checkListTemplates, many=True).data
            return data
        cl_template = ChecklistTemplate.objects.get(uuid=templateUuid)
        if (cl_template is not None):
            data = ChecklistTemplateModelSerializer(
                cl_template, many=False).data
            sections = ChecklistSection.objects.filter(template=cl_template)
            if (sections is not None):
                section_list = []
                for sec in sections:
                    section_data = dict()
                    section_data = ChecklistSectionModelSerializer(
                        sec, many=False).data

                    lineItems = ChecklistLineItem.objects.filter(section=sec)
                    section_data['lineItems'] = \
                        ChecklistLineItemModelSerializer(
                        lineItems, many=True).data
                    section_list.append(section_data)

            data['sections'] = section_list

        return data

    def createNewSection(self, section, templateObj):
        """Create new section for a given template """
        logger.debug(
            "Creating a new section. Section name = " + section['name'])

        weight = int(
            ChecklistSection.objects.filter(
                template=templateObj).aggregate(
                max_weight=Max('weight'))['max_weight'] or 0) + 1

        newSection = ChecklistSection.objects.create(
            name=section.get('name', None),
            description=section.get('description', None),
            validation_instructions=section.get(
                'validation_instructions', None),
            template=templateObj,
            weight=weight)

        return newSection

    def createNewLineItemForSection(
            self, newSectionObj, listItem, templateObj):
        """Create new line item for a given section and template """

        weight = int(
            ChecklistLineItem.objects.filter(
                section=newSectionObj).aggregate(
                max_weight=Max('weight'))['max_weight'] or 0) + 1

        ChecklistLineItem.objects.create(
            name=listItem['name'],
            description=listItem.get('description', None),
            # @UndefinedVariable
            line_type=listItem.get('line_type', CheckListLineType.auto.name),
            validation_instructions=listItem.get(
                'validation_instructions', None),
            section=newSectionObj,
            template=templateObj,
            weight=weight)

    def delete(self, dict_structure, query_set, entity, isDirty):
        """Generically find the xor result of the user input and the
        db data. Assumption: If entities exits in DB but not in
        user input they'll be deleted"""
        uuid_client = [dictio['uuid'] for dictio in dict_structure]
        uuid_db = [record.uuid for record in query_set]
        uuids_to_delete = set(uuid_db) - set(uuid_client)
        for u_uid in uuids_to_delete:
            entity.objects.filter(uuid=u_uid).delete()
            # Note: No need to delete ChecklistLineItem
            # corresponding to this section
            # since there is a CASCADE operation on delete section
            isDirty[0] = True

    def editIfChanged(self, entity, uidict, fieldList):
        """Generic function to check that set of fields
        are modified on a certain entity"""
        isChanged = False
        for field in fieldList:
            if (field in uidict):
                if (not isChanged and entity.__dict__[
                        field] == uidict[field]):
                    isChanged = False
                else:
                    entity.__dict__[field] = uidict[field]
                    isChanged = True
        return isChanged

    def updateTemplateFields(self, clTemplate, checklistTemplate, isDirty):
        if (self.editIfChanged(clTemplate, checklistTemplate, ['name'])):
            clTemplate.save()
            isDirty[0] = True

    def updateSectionFields(self, section, sec, isDirty):
        if (self.editIfChanged(section, sec, ['name'])):
            section.save()
            isDirty[0] = True

    def updateLineItemFields(self, lineitem, li, isDirty):
        if (self.editIfChanged(lineitem, li, [
                'name', 'description',
                'validation_instructions', 'line_type'])):
            lineitem.save()
            isDirty[0] = True

    def editChecklistTemplate(self, checklistTemplate):
        """edit the template+section+line-item of user input"""
        # this is an indication on top of the provided json to create the
        # entity
        NEW_ENTITY = "newEntity"
        templateObj = None
        isDirty = [False]
        if ('uuid' in checklistTemplate):
            templateUuid = checklistTemplate['uuid']
            templateObj = ChecklistTemplate.objects.get(uuid=templateUuid)
            self.updateTemplateFields(templateObj, checklistTemplate, isDirty)
            # SECTIONS
            if ('sections' in checklistTemplate):
                sections = checklistTemplate['sections']
                query_set = templateObj.checklistsection_set.all()
                self.delete(sections, query_set, ChecklistSection, isDirty)
                sectionObj = None
                for sec in sections:
                    if (sec['uuid'] == NEW_ENTITY):
                        sectionObj = self.createNewSection(sec, templateObj)
                        isDirty[0] = True
                    else:  # section was only updated
                        sectionObj = ChecklistSection.objects.get(
                            uuid=sec['uuid'])
                        self.updateSectionFields(sectionObj, sec, isDirty)
                    # LINE-ITEMS
                    if ('lineItems' in sec):
                        lineItems = sec['lineItems']
                        query_set = sectionObj.checklistlineitem_set.all()
                        self.delete(lineItems, query_set,
                                    ChecklistLineItem, isDirty)
                        for li in lineItems:
                            if (li['uuid'] == NEW_ENTITY):
                                self.createNewLineItemForSection(
                                    sectionObj, li, templateObj)
                                isDirty[0] = True
                            else:  # line-item was only updated
                                lineitem = ChecklistLineItem.objects.get(
                                    uuid=li['uuid'])
                                self.updateLineItemFields(
                                    lineitem, li, isDirty)

        executor.submit(self.decline_all_template_checklists,
                        isDirty[0], templateObj, request_data_mgr.get_user())

    def decline_all_template_checklists(self, isDirty, templateObj, user):
        request_data_mgr.set_user(user)
        checklists = None

        start = time.clock()
        try:
            if (isDirty):
                states_to_exclude = [
                    CheckListState.archive.name,
                    CheckListState.closed.name,
                    CheckListState.pending.name]  # @UndefinedVariable
                checklists = Checklist.objects.filter(
                    template=templateObj).exclude(state__in=states_to_exclude)
                logger.debug("Number of checklists=" +
                             str(len(checklists)))
                for checklist in checklists:
                    request_data_mgr.set_cl_uuid(checklist.uuid)
                    request_data_mgr.set_eng_uuid(checklist.engagement.uuid)
                    set_state(
                        # means that the checklist will be declined and a
                        # cloned one is created in PENDING status
                        True,
                        checklist.uuid,
                        isMoveToAutomation=True,
                        description="""Checklist {name} was rejected """ +\
                        """since its template ({template}) was """ +\
                        """edited/deleted""".format(
                            name=checklist.name, template=templateObj.name),
                        # means the checklist will be triggered into automation
                        # cycle
                    )
        except Exception as e:
            msg = """Something went wrong while trying to reject """ +\
                """check-lists which its template was changed. """ +\
                """template={template}. Error:""".format(
                    template=templateObj.name)
            logger.error(msg + " " + str(e))
            raise e  # Don't remove try-except, it supports async invocation
        end = time.clock()
        logger.debug("TIME:" + str(end - start))

    def getChecklist(self, user, checklistUuid):

        data = dict()
        checklist = None

        if user.role.name == Roles.admin.name or \
                user.role.name == Roles.admin_ro.name:
            checklist = Checklist.objects.get(uuid=checklistUuid)
        else:
            checklist = Checklist.objects.get(
                Q(uuid=checklistUuid), Q(creator=user) | Q(owner=user))

        # CheckList
        if checklist.state == CheckListState.archive.name:
            msg = "got a request for a checklist which is an archived one, " +\
                "might have been due to an admin edit of a checklist template."
            logger.error(msg)
            msg = "Requested checklist is archived, reloading checklists list"
            raise VvpObjectNotAvailable(msg)
        data['checklist'] = ThinChecklistModelSerializer(
            checklist, many=False).data
        vf = VF.objects.get(engagement=checklist.engagement)
        data['checklist']['associated_files'] = json.loads(
            data['checklist']['associated_files'])
        data['checklist']['jenkins_log'] = get_jenkins_build_log(
            vf, checklistUuid)
        data['checklist']['repo_associated_files'] = GitManager(
        ).getRepoAssociatedFilesForUser(checklist.engagement.uuid)
        # CheckList Audit Logs
        # here all fetched records should have decision==null
        checklistAuditLogs = ChecklistAuditLog.objects.filter(
            checklist__uuid=checklistUuid)
        serializedAuditLogsData = ThinChecklistAuditLogModelSerializer(
            checklistAuditLogs, many=True).data
        data['checklistAuditLogs'] = serializedAuditLogsData

        # CheckList Decisions + LineItems + Sections (The data is nested thanks
        # to the serializer)
        checklistDecisions = ChecklistDecision.objects.filter(
            checklist__uuid=checklistUuid)
        serializedDecisionsData = ThinChecklistDecisionModelSerializer(
            checklistDecisions, many=True).data
        checklistLineItems = {}
        for checklistDecision in serializedDecisionsData:
            section_uuid = checklistDecision['lineitem']['section']['uuid']
            section_weight = checklistDecision['lineitem']['section']['weight']
            section_key = str(section_weight) + "_" + section_uuid
            if section_key not in checklistLineItems:
                checklistLineItems[section_key] = {}
                checklistLineItems[section_key]['section'] = \
                    checklistDecision['lineitem']['section']
                checklistLineItems[section_key]['decisions'] = {}
                checklistLineItems[section_key]['weight'] = section_weight

            decision_uuid = checklistDecision['uuid']
            line_item_weight = checklistDecision['lineitem']['weight']
            decision_key = str(line_item_weight) + "_" + decision_uuid
            checklistLineItems[section_key]['decisions'][decision_key] = \
                checklistDecision
            checklistLineItems[section_key]['decisions'][
                decision_key]['weight'] = line_item_weight

        data['checklistDecisions'] = checklistLineItems

        # Decision Audit Logs
        data['decisionAuditLogs'] = {}
        for checklistDecision in checklistDecisions:
            # here all fetched records should have checklist==null
            decisionAuditLogs = ChecklistAuditLog.objects.filter(
                decision=checklistDecision)
            if decisionAuditLogs.count() > 0:
                serializedAuditLogsData = ThinChecklistAuditLogModelSerializer(
                    decisionAuditLogs, many=True).data
                data['decisionAuditLogs'][
                    checklistDecision.uuid] = serializedAuditLogsData

        logger.debug("get existing checklist has " +
                     "succeeded for checklist.uuid=" +
                     str(checklist.uuid) +
                     ", user.uuid=" +
                     str(user.uuid) +
                     ", checklist.uuid=" +
                     str(checklistUuid))

        return data

    def getEngagementFiles(self, eng_uuid):
        repo_files = self.gitManager.getRepoAssociatedFilesForUser(eng_uuid)
        return repo_files

    def createOrUpdateChecklist(
            self,
            checkListName,
            checkListTemplateUuid,
            checkListAssociatedFiles,
            checklistUuid=None):
        template = None
        checklist = None
        user = request_data_mgr.get_user()
        eng_uuid = request_data_mgr.get_eng_uuid()

        vf = VF.objects.get(engagement__uuid=eng_uuid)

        # associated_files may be delivered in this format
        #   [{"File": "bar"}, {"File": "baz"},
        # {"File": "foo"}, {"File": "quux"}]
        # but we want to store it in this format
        #   ["bar", "baz", "foo", "quux"]

        repo_files = self.gitManager.getRepoAssociatedFilesForUser(eng_uuid)
        if not send_jenkins_job_and_gitlab_repo_exists(vf):
            msg = "Jenkins job or gitlab repo is still missing"
            logger.error(msg)
            msg = "Create or update checklist is not ready yet"
            raise Exception(msg)
        checklist_files_list = []
        for file in checkListAssociatedFiles:
            if isinstance(file, dict):
                checklist_files_list.append(file['File'])
            else:
                checklist_files_list.append(file)
        for added_name in checklist_files_list:
            if added_name not in repo_files:
                logger.error("Update checklist has failed. " +
                             added_name + " doesnt exist in repo")
                msg = "Failed to create checklist, please select valid file"
                raise ValueError(msg)

        associated_files = json.dumps(checklist_files_list, ensure_ascii=False)

        engagement = Engagement.objects.get(uuid=eng_uuid)
        template = ChecklistTemplate.objects.get(uuid=checkListTemplateUuid)

        if (checklistUuid is not None):  # Update Checklist
            checklist = Checklist.objects.get(uuid=checklistUuid)
            checklist.name = checkListName
            checklist.associated_files = associated_files
            checklist.template = template
            checklist.save()
            if (associated_files and len(checklist_files_list) > 0):
                set_state(
                    decline=True,
                    description="Checklist: " + checklist.name +
                    "in Pending state will transition to \
                    Automation because it has associated files",
                    isMoveToAutomation=True,
                    # means the checklist will be triggered into automation
                    # cycle
                    checklist_uuid=checklist.uuid
                )
        else:  # create ChcekList
            if (user.role.name == Roles.admin.name):  # @UndefinedVariable
                incharge_personal = engagement.reviewer
            else:
                incharge_personal = user
            vf = None
            vf = VF.objects.get(engagement=engagement)

            if (vf.git_repo_url is None):
                msg = "Can't create checklist since the attached VF (" + \
                    vf.name + ") doesn't contain git_repo_url"
                logger.error(
                    "Update checklist has failed. " + logEncoding(msg))
                raise ObjectDoesNotExist(msg)

            checklist = Checklist(
                name=checkListName,
                validation_cycle=1,
                associated_files=associated_files,
                state=CheckListState.pending.name,
                engagement=engagement,
                template=template,
                creator=user,
                owner=incharge_personal)  # @UndefinedVariable
            line_items_list = ChecklistLineItem.objects.filter(
                template=template)
            checklist.save()
            for lineitem in line_items_list:
                new_decision = ChecklistDecision(
                    checklist=checklist, template=template, lineitem=lineitem)
                new_decision.save()

            # When Checklist is created with files move it it automation
            if (associated_files and len(checklist_files_list) > 0):
                set_state(
                    decline=False,
                    checklist_uuid=checklist.uuid,
                    description="Checklist: " + checklist.name +
                    "in Pending state will transition to \
                    Automation because it has associated files",
                    isMoveToAutomation=True
                    # means the checklist will be triggered into automation
                    # cycle
                )

        logger.debug(
            "Create/Update checklist has succeeded for checklist.uuid="
            + str(checklist.uuid))

        return ThinPostChecklistResponseModelSerializer(checklist).data

    def deleteChecklist(self, checklist_uuid):
        checklist = Checklist.objects.get(uuid=checklist_uuid)
        checklist.delete()

        logger.debug(
            "Delete checklist has succeeded for checklist.uuid=" +
            str(checklist_uuid))

    def setChecklistDecisionsFromValMgr(
            self,
            user,
            checklist_uuid,
            decisions,
            checklist_results_from_jenkins):
        checklist = Checklist.objects.get(
            uuid=checklist_uuid,
            owner=user,
            state=CheckListState.automation.name)

        logger.debug(
            "setChecklistDecisionsFromValMgr() " +
            "checklist_uuid=%r, len(decisions)=%d",
            checklist_uuid,
            len(decisions),
        )

        if ('error' in checklist_results_from_jenkins):
            el_role = Role.objects.get(name=Roles.el.name)
            admin_role = Role.objects.get(name=Roles.admin.name)
            el_admin_list = IceUserProfile.objects.all().filter(
                Q(role=el_role) | Q(role=admin_role))

            activity_data = TestFinishedActivityData(
                el_admin_list, checklist.engagement,
                checklist_results_from_jenkins['error'])
            bus_service.send_message(ActivityEventMessage(activity_data))

            msg = "test_finished signal from Jenkins has arrived with " +\
                "error: {}".format(checklist_results_from_jenkins['error'])
            logger.error(msg)
            set_state(True, checklist_uuid, isMoveToAutomation=False,
                      description=checklist_results_from_jenkins['error'])
            raise Exception(msg)

        ChecklistLineItem.objects.filter(template=checklist.template).update(
            line_type=CheckListLineType.manual.name)

        for decision in decisions:
            lineitem_obj = ChecklistLineItem.objects.get(
                uuid=decision['line_item_id'])
            lineitem_obj.line_type = CheckListLineType.auto.name
            lineitem_obj.save()

            decision_obj = ChecklistDecision.objects.get(
                checklist=checklist, lineitem=lineitem_obj)
            setDecision(decisionUuid=decision_obj.uuid,
                        user=user, value=decision['value'])

            if (decision['audit_log_text'] !=
                    '' and decision['audit_log_text'] is not None):
                addAuditLogToDecision(
                    decision=decision_obj,
                    description=decision['audit_log_text'],
                    user=user,
                    category='')

        desc = "The {} validation test suite has completed. The decisions " +\
               "based on the test results \
               have successfully been set in the " +\
               "checklist.".format(checklist.template.category)
        addAuditLogToChecklist(checklist=checklist, description=desc,
                               user=user, category='')
        checklistData = ThinChecklistModelSerializer(
            checklist, many=False).data
        set_state(False, checklist.uuid,
                  isMoveToAutomation=True, description="")

        return checklistData
