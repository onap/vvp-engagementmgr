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
'''
A webhook endpoint for Jenkins

This acts as the endpoint for the Jenkins Notification Plugin:
https://wiki.jenkins-ci.org/display/JENKINS/Notification+Plugin

It must be configured for JSON format and HTTP mode.

We parse the data delivered from Jenkins, and build a structure in
this format:

{
    "checklist": {
        "checklist_uuid": "dsda-2312-dsxcvd-213",
        "decisions": [
            {
                "line_item_id": "123-223442-12312-21312",
                "value": "approved",
                "audit_log_text": "audiot text blah blaj",
                },
            {
                "line_item_id": "123-223442-12312-21312",
                "value": "approved",
                "audit_log_text": "audiot text blah blaj",
                },
            ],
        "error": "..." # optional; only exists when there's an error.
        }
    }

The Notification Plugin provides no mechanism for an authentication
token, so if desired, we set this endpoint at a difficult-to-guess
URL, by default:

    hook/test-complete/<webhook token>/

where <jenkins token> is django.settings.WEBHOOK_TOKEN.

'''
from collections import namedtuple
import re

from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from tap.parser import Parser as TapParser

from engagementmanager.models import Checklist, ChecklistLineItem
from engagementmanager.utils.constants import CheckListDecisionValue
from validationmanager.em_integration import em_client
import validationmanager.rest.http_response_custom as exc
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


# A simple class to hold abstracted test result data.
# Intentionally similar to tap.Line of category
# 'test', but it is possible that not all of our test results
# will be in TAP format in the future.
TestResult = namedtuple('TestResult', ['name', 'ok', 'skip', 'description'])


def null_testresult(name):
    """Return a fake TestResult object representing a missing
    test with the given name.

    This is the "Null Object Pattern," called whenever build_decision
    looks for a test that has not run.
    """
    return TestResult(
        name=name,
        ok=False,
        skip=False,
        description='(Required validator "%s" did not run.)' % name)


def build_decisions(test_results, test_names, line_items):
    """Generates a decision dict for each line item, given
    a dict of test names to TestResults.

    Decision dicts take the form:
        {
            "line_item_id": "...",
            "value": (a CheckListDecisionValue),
            "audit_log_text": "...",
        }

    """
    parsed_results = {}
    for test_name in test_names:
        parsed_results[test_name] = {
            "ok": [],
            "skip": [],
            "skip_or_ok": [],
        }

    for test_result in test_results:
        test_name = test_result.name
        parsed_results[test_name]["ok"].append(test_result.ok)
        parsed_results[test_name]["skip"].append(test_result.skip)
        parsed_results[test_name]["skip_or_ok"].append(test_result.ok or
                                                       test_result.skip)

    for line_item in line_items:
        validation_tests = line_item.validationtest_set.all()
        required_test_names = sorted([t.name
                                      for t in validation_tests])

        # no associated tests: no decision for this line item.
        if not required_test_names:
            continue

        for r in required_test_names:
            if r not in parsed_results:
                parsed_results[r] = {"ok": [], "skip": [], "skip_or_ok": []}

        # - A test is passing if at least one of the tests passes
        # and the rest are skipped.
        # - If all tests for a line item are skipped, mark test as na
        # - If at least one test fail, the entire line item is failing
        # - Required tests that are not in 'result' default to no decision
        audit_logs = "All required tests "
        if all(result
               for t in required_test_names
               for result in parsed_results[t]["ok"]):
            value = CheckListDecisionValue.approved
            audit_logs += "passed."
        elif all(result
                 for t in required_test_names
                 for result in parsed_results[t]["skip_or_ok"]):
            value = CheckListDecisionValue.approved
            audit_logs += "either passed or skipped."
        elif all(result
                 for t in required_test_names
                 for result in parsed_results[t]["skip"]):
            value = CheckListDecisionValue.na
            audit_logs += "were skipped."
        else:
            value = CheckListDecisionValue.denied
            audit_logs = "At least one of the required tests\
                          failed. The tests that ran were:\n\n"

        # Complete the audit_logs
        audit_logs += (" (" + ", ".join(required_test_names) + ")")

        yield {
            "line_item_id": line_item.uuid,
            "value": value.name,
            "audit_log_text": audit_logs,
        }


def parse_tap_logs(test_output):
    """Given text in TAP format, generate TestResult objects.

    NOTE: This ignores lines of TAP output of type plan,
    diagnostic (comment), bail, and unknown.
    """
    for line in TapParser().parse_text(test_output):
        if line.category != 'test':
            continue
        if line.todo:
            continue

        # get the test name
        pattern = re.compile(r'- (.+?)\[(.+?)\]')
        m = pattern.match(line.description)
        if not m:
            continue
        if len(m.groups()) < 2:
            continue
        test_name = m.group(1)

        yield TestResult(
            name=test_name,
            ok=line.ok,
            skip=line.skip,
            description=line.description,
        )


class JenkinsWebhookEndpoint(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None, **kwargs):
        # Authenticate
        #
        # NOTE: we'd like to employ the built-in facilities in Django
        # REST Framework for authentication, but we have no easy way to control
        # the headers that the Jenkins notification plugin sends during
        # its POST request. So we homebrew our own URL-based mechanism.
        correct_token = settings.WEBHOOK_TOKEN
        if correct_token and correct_token != kwargs.get('auth_token'):
            raise exc.InvalidAuthTokenException()

        # sanity check
        try:
            data = request.data
            if data['build']['phase'] != u'FINALIZED':
                raise exc.InvalidJenkinsPhaseException()
        except KeyError:
            raise exc.InvalidJenkinsPhaseException()

        # Using data model, map the output logs to line item sucess/fail.

        # look up the Checklist
        # NOTE this logic relies upon there being a single, unique UUID per
        # checklist per git hash.
        # If someone pushes new data into the repo, a new Checklist
        # should be created that we will validate.
        checklist_uuid = data['build']['parameters']['checklist_uuid']
        checklist = Checklist.objects.get(uuid=checklist_uuid)

        # Get the ChecklistLineItems associated with Checklist.
        line_items = ChecklistLineItem.objects.filter(
            template=checklist.template)

        # parse all result data to an iterable of TestResults
        test_results = list(parse_tap_logs(data['build']['log']))

        # get all the test names from the test results
        test_names = set([test_result.name
                          for test_result in test_results])

        # Build payload object
        payload = {
            "checklist": {
                "checklist_uuid": checklist_uuid,
                "decisions": list(build_decisions(test_results,
                                                  test_names,
                                                  line_items)),
            }}
        logger.debug('sending test_finished with payload %s', payload)

        # The Validation Engine suite will always include a successful
        # result with the description.
        # "test_this_sentinel_always_succeeds'. If it is not present,
        # we assume something has gone
        # wrong with the Validation Engine itself.
        # if 'test_this_sentinel_always_succeeds' not in test_results:
        #    logger.error('Validation Engine failed to include sentinel.
        # Assuming it failed. Full log: %s',
        #                 logEncoding(request.data['build']['log']))
        #    payload['checklist']['error'] = 'The Validation Engine \
        # encountered an error.'
        #     If possible, identify what specifically went wrong and
        # provide a message to return to the user.
        #    if 'fatal: Could not read from remote repository'
        #     in request.data['build']['log']:
        #         payload['checklist']['error'] += " There was a problem \
        # cloning a git repository."
        # Send Signal
        em_client.test_finished(checklist_test_results=payload['checklist'])

        # Respond to webhook
        return Response('Webhook received functions notified')
