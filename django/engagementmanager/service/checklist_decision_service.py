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
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import MethodNotAllowed
from engagementmanager.models import ChecklistDecision
from engagementmanager.serializers import ThinChecklistDecisionModelSerializer
from engagementmanager.utils.constants import CheckListState, \
    CheckListDecisionValue, Roles
from engagementmanager.utils.validator import logEncoding
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def setDecision(decisionUuid, user, value):
    logger.debug("attempting setDecision(user=%r, value=%r)...", user, value)

    if not decisionUuid or not user or value not in \
            CheckListDecisionValue.__members__:
        msg = "decisionUuid or value are empty or invalid / user == None"
        logger.error(msg)
        msg = "decision wasn't change due to bad parameters"
        raise KeyError(msg)

    decision = ChecklistDecision.objects.get(uuid=decisionUuid)
    checklist = decision.checklist

    if (checklist.owner.email == user.email and
            user.role.name == Roles.el.name) or \
            (user.role.name == Roles.admin.name):
        if checklist.state == CheckListState.review.name:
            if decision.review_value != value:
                decision.review_value = value
                decision.save()
                msg = "review_value was successfully " +\
                    "changed for decision: " + \
                    decision.uuid + " , value: " + value
            else:
                msg = "review_value was already the same: " + \
                    decision.uuid + " , value: " + value
            logger.debug(msg)
        elif checklist.state == CheckListState.peer_review.name:
            if decision.peer_review_value != value:
                decision.peer_review_value = value
                decision.save()
                msg = "peer_review_value was successfully " +\
                    "changed for decision: " + decision.uuid +\
                    " , value: " + value
            else:
                msg = "review_value was already the same: " + \
                    decision.uuid + " , value: " + value
            logger.debug(msg)
        elif checklist.state == CheckListState.automation.name:
            if decision.review_value != value:
                decision.peer_review_value = value
                decision.save()
                msg = "peer_review_value was successfully " +\
                    "changed for decision: " + decision.uuid +\
                    " , value: " + value
            else:
                msg = "review_value was already the same: " + \
                    decision.uuid + " , value: " + value

            if decision.review_value != value:
                decision.review_value = value
                decision.save()
                msg = "review_value was successfully " +\
                    "changed for decision: " + \
                    decision.uuid + " , value: " + value
            else:
                msg = "review_value was already the same: " + \
                    decision.uuid + " , value: " + value
            logger.debug(msg)
        else:
            msg = "checklist's state is an invalid state for the decision " +\
                "change and should be different"
            logger.error(msg)
            msg = "decision wasn't change, " +\
                "Checklist's state is not allowed to change the decision"
            raise MethodNotAllowed(msg)
        return msg
    else:
        msg = "user isn't an EL / The User (" + user.full_name + \
            ") tried to change the decision while the current owner is " \
            + checklist.owner.full_name
        logger.error(logEncoding(msg))
        msg = "Action is forbidden"
        raise PermissionDenied(msg)


def getDecision(decisionUuid, user):
    data = dict()
    # @UndefinedVariable
    if decisionUuid == '' or (not user and user.role.name == Roles.el.name):
        msg = "decisionUuid or (user == None / user.role != EL)"
        logger.error(msg)
        msg = "decision wasn't retrieved due to bad parameters / " +\
            "you are not authorized"
        raise KeyError(msg)

    decision = ChecklistDecision.objects.get(uuid=decisionUuid)
    data['decision'] = ThinChecklistDecisionModelSerializer(
        decision, many=False).data
    decisionData = json.dumps(data, ensure_ascii=False)
    return decisionData
