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
from engagementmanager.models import ChecklistDecision, ChecklistAuditLog, Checklist
from engagementmanager.serializers import ThinChecklistAuditLogModelSerializer
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def addAuditLogToDecision(decision, description, user, category=''):
    """
    expected: decisionUuid(string), description(string), user(object), category is optional(string)
    result: new auditlog object would be create and attached to a decision object.
    """
    audit = ChecklistAuditLog.objects.create(decision=decision,
                                             description=description, category=category, creator=user)
    auditData = ThinChecklistAuditLogModelSerializer(audit).data
    return auditData


def getAuditLogsWithDecision(decisionUuid, user):
    """
    expected: decisionUuid(string), user(object)
    result: all audit logs objects that attached to a decision would be returned in a json.
    """
    data = dict()
    if checklistUuid == '' or not user:  # @UndefinedVariable
        msg = "checklistUuid or user == None"
        logger.error(msg)
        msg = "AuditLogs were not retrieved due to bad parameters"
        raise KeyError(msg)

    decision = ChecklistDecision.objects.get(uuid=decisionUuid)
    audits = ChecklistAuditLog.objects.filter(decision=decision)
    data['audits'] = ThinChecklistAuditLogModelSerializer(audits, many=True).data
    auditsData = json.dumps(data, ensure_ascii=False)
    return auditsData


def addAuditLogToChecklist(checklist, description, user, category=''):
    """
    expected: checklistUuid(string), description(string), user(object), category is optional(string)
    result: new auditlog object would be create and attached to a checklist object.
    """
    audit = ChecklistAuditLog.objects.create(checklist=checklist,
                                             description=description, category=category, creator=user)
    auditData = ThinChecklistAuditLogModelSerializer(audit).data
    logger.debug("audit log was successfully updated")
    return auditData


def getAuditLogsWithChecklist(checklistUuid, user):
    """
    expected: checklistUuid(string), user(object)
    result: all audit logs objects that attached to a checklist would be returned in a json.
    """
    data = dict()
    if checklistUuid == '' or not user:  # @UndefinedVariable
        msg = "checklistUuid or user == None"
        logger.error(msg)
        msg = "AuditLogs were not retrieved due to bad parameters"
        raise KeyError(msg)

    checklist = Checklist.objects.get(uuid=checklistUuid)
    audits = ChecklistAuditLog.objects.filter(checklist=checklist)
    data['audits'] = ThinChecklistAuditLogModelSerializer(audits, many=True).data
    auditsData = json.dumps(data, ensure_ascii=False)
    return auditsData
