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
    A webhook endpoint for Gitlab.

    FIXME currently this supports only Push Hook notification. It could
    be extended to support any type of webhook that Gitlab issues.

    This is based on the documentation here:
    https://docs.gitlab.com/ce/web_hooks/web_hooks.html

    Upon receiving a push from Gitlab, we authenticate the request,
    parse the json payload, and send appropriate signals so other
    applications can take action.

    Reference: https://docs.gitlab.com/ce/web_hooks/web_hooks.html

'''
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from validationmanager.em_integration import em_client
import validationmanager.rest.http_response_custom as exc
from validationmanager.utils.constants import KNOWN_GITLAB_EVENTS
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class GitWebhookEndpoint(APIView):
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

        # There are multiple types of Gitlab webhook, specified in the
        # X-Gitlab-Event header.
        gitlab_event = request.META.get('HTTP_X_GITLAB_EVENT')
        if gitlab_event is None:
            raise exc.InvalidGitlabEventException()

        if gitlab_event not in KNOWN_GITLAB_EVENTS:
            raise exc.InvalidGitlabEventException()

        # FIXME a properly abstract webhook endpoint would dispatch to
        # handlers for each type of gitlab event. For now, we only support
        # the Push Hook event.
        if gitlab_event != 'Push Hook':
            raise exc.InvalidGitlabEventException()

        # Parse
        try:
            payload = request.data
        except ValueError:
            raise exc.InvalidPayloadException()

        # A loose sanity-check to be sure data is in expected format.
        if not all(k in payload for k in ['object_kind', 'ref',
                                          'project', 'commits']):
            raise exc.InvalidPayloadException()

        # Remove deprecated keys for safety
        payload.pop('repository', None)  # now 'project'
        payload['project'].pop('ssh_url', None)  # now 'git_ssh_url'
        payload['project'].pop('http_url', None)  # now 'git_http_url'

        # Send the signal with the payload
        logger.debug('validationmanager.rest.git_webhook_endpoint sending %r',
                     payload)
        em_client.git_push(gitlab_data=payload)

        # Gitlab ignores the HTTP status code returned, but a valid HTTP
        # response should always be sent lest it try to send the webhook again.
        return Response('Webhook received functions notified')
