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
from django.conf.urls import url

from engagementmanager.rest import checklist_audit_log
from engagementmanager.rest import user, activation, activity, vf,\
    invite, feedback, nextsteps, engagement, \
    login, signup, notification, checklist, deployment_target_site,\
    vendor, data_loader, checklist_decision, \
    vfc, checklist_set_state, deployment_target, ecomp, validation_details
from engagementmanager.rest.cms.pages import Pages, PageById, PageSearch
from engagementmanager.rest.cms.posts import Posts
from engagementmanager.rest.engagement import EngagementProgressBar,\
    ChangeTargetLabEntryDate, EngagementOps, \
    EngagementReviewer, EngagementPeerReviewer,\
    ArchiveEngagement, SwitchEngagementReviewers
from engagementmanager.rest.user import User
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


# Our UUIDs are always uuid4; a 36-character string of lowercase hexadecimal
# and '-' characters.
re_uuid = r'[a-f0-9-]{36}'
# UUIDs in tokens are the same as above without '-', so 32 lowercase
# hexadecimal characters.
re_token = r'[a-f0-9]{32}'
# Parameters like 'stage' correspond to Enums, so have the same rules as Python
# identifiers: upper and lower case, numbers, and underscore.
re_enum = r'[a-zA-Z0-9_\.-]+'

re_token_reset_password = r'[a-zA-Z0-9-\._]+'


urlpatterns = [
    url(r'^users/engagementleads/?$', user.EngagementLeads.as_view()),
    url(r'^users/ssh/?$', user.SetSsh.as_view()),
    url(r'^users/account/?$', user.User.as_view()),
    url(r'^users/account/rgwa/?$', user.RGWAAccessKey.as_view()),
    url(r'^users/pwd/reset-instructions/?$',
        user.SendResetPasswordInstructionMail.as_view()),
    url(r'^users/pwd/?$', user.UpdatePassword.as_view()),
    url(r'^users/?$', User.as_view()),

    # User Activation
    url(r'^users/activation-mail/(?P<user_uuid>%s)$' % re_uuid,
        activation.ResendActivationMail.as_view()),
    url(r'^users/activate/(?P<uu_id>%s)/(?P<token>%s)$' %
        (re_uuid, re_token), activation.ActivateUser.as_view()),

    # Engagements API
    url(r'^single-engagement/(?P<eng_uuid>%s)/stage/(?P<stage>%s)$' %
        (re_uuid, re_enum), engagement.SingleEngByUser.as_view()),
    url(r'^single-engagement/(?P<eng_uuid>%s)$' %
        re_uuid, engagement.SingleEngByUser.as_view()),
    url(r'^engagements/user/nextsteps/?$', nextsteps.UserNextSteps.as_view()),
    url(r'^engagements/starred_eng/?$',
        engagement.StarredEngagements.as_view()),
    url(r'^engagements/recent_eng/?$',
        engagement.GetRecentEngagements.as_view()),
    url(r'^engagements/engagement-team/?$',
        engagement.EngagementTeamUsers.as_view()),
    url(r'^engagements/(?P<eng_uuid>%s)/status/?$' %
        re_uuid, engagement.Status.as_view()),
    url(r'^engagements/(?P<eng_uuid>%s)/nextsteps/?$' %
        re_uuid, nextsteps.NextSteps.as_view()),
    url(r'^engagements/(?P<eng_uuid>%s)/nextsteps/order_next_steps$' %
        re_uuid, nextsteps.OrderNextSteps.as_view()),
    url(r'^engagements/(?P<eng_uuid>%s)/' % re_uuid +\
        'nextsteps/(?P<eng_stage>%s)/?$' % re_enum,
        nextsteps.NextSteps.as_view()),  # Set Next Step State
    # Set Progress bar for Engagement
    url(r'^engagements/(?P<eng_uuid>%s)/progress/?$' %
        re_uuid, EngagementProgressBar.as_view()),
    url(r'^engagements/(?P<eng_uuid>%s)/target_date/?$' %
        re_uuid, EngagementProgressBar.as_view()),  # Set Target Date
    # Set Target Lab Entry Date
    url(r'^engagements/(?P<eng_uuid>%s)/target_lab_date/?$' %
        re_uuid, ChangeTargetLabEntryDate.as_view()),
    url(r'^engagements/(?P<eng_uuid>%s)/archive/?$' %
        re_uuid, ArchiveEngagement.as_view()),
    url(r'^engagements/(?P<eng_uuid>%s)/reviewer/?$' %
        re_uuid, EngagementReviewer.as_view()),
    url(r'^engagements/(?P<eng_uuid>%s)/peerreviewer/?$' %
        re_uuid, EngagementPeerReviewer.as_view()),
    url(r'^engagements/(?P<eng_uuid>%s)/switch-reviewers/?$' %
        re_uuid, SwitchEngagementReviewers.as_view()),
    url(r'^engagements/(?P<eng_uuid>%s)/$' %
        re_uuid, EngagementOps.as_view()),  # Used by delete engagement
    url(r'^engagement/expanded/?$', engagement.ExpandedEngByUser.as_view()),
    url(r'^engagement/export/', engagement.ExportEngagements.as_view()),
    url(r'^engagement/?$', engagement.GetEngByUser.as_view()),
    # Activities - pull top X objects
    url(r'^engagement/(?P<eng_uuid>%s)/activities/?$' %
        re_uuid, activity.PullActivities.as_view()),

    # DeploymentTarget(version)
    url(r'^engagement/(?P<engagement_uuid>%s)' % re_uuid +\
        '/deployment-targets/(?P<dt_uuid>%s)$' % (re_uuid),
        deployment_target.DeploymentTargetRESTMethods.as_view()),
    url(r'^deployment-targets/?$',
        deployment_target.DeploymentTargetRESTMethods.as_view()),

    # ECOMP
    url(r'^engagement/(?P<engagement_uuid>%s)' % re_uuid +\
        '/ecomp-releases/(?P<ecomp_uuid>%s)$' % (re_uuid),
        ecomp.ECOMPReleaseRESTMethods.as_view()),
    url(r'^ecomp-releases/?$', ecomp.ECOMPReleaseRESTMethods.as_view()),
    # VFVERSION
    url(r'^vf/(?P<vf_uuid>%s)/vf-version/$' % re_uuid, vf.VF.as_view()),
    # DeploymentTargetSite%s
    url(r'^vf/(?P<vf_uuid>%s)/validation-details/$' % re_uuid,
        validation_details.UpdateValidationDetails.as_view()),
    url(r'^vf/(?P<vf_uuid>%s)/dtsites/$' %
        re_uuid, deployment_target_site.DTSites.as_view()),
    url(r'^vf/(?P<vf_uuid>%s)/dtsites/(?P<dts_uuid>%s)$' %
        (re_uuid, re_uuid), deployment_target_site.DTSites.as_view()),
    url(r'^dtsites/?$', deployment_target_site.DTSites.as_view()),

    # Vendor
    url(r'^vendors/?$', vendor.VendorREST.as_view()),
    url(r'^vendors/(?P<uuid>%s)$' % re_uuid, vendor.VendorREST.as_view()),

    url(r'^vfcs/?$', vfc.VFCRest.as_view()),
    url(r'^vf/(?P<vf_uuid>%s)/vfcs/$' % re_uuid, vfc.VFCRest.as_view()),
    url(r'^vf/(?P<vf_uuid>%s)/vfcs/(?P<vfc_uuid>%s)?$' %
        (re_uuid, re_uuid), vfc.VFCRest.as_view()),

    # Next Steps
    url(r'^nextsteps/(?P<ns_uuid>%s)/' % re_uuid +\
        'engagement/(?P<eng_uuid>%s)?$' % re_uuid,
        nextsteps.EditNextSteps.as_view()),  # Set State for a next step
    url(r'^nextsteps/(?P<ns_uuid>%s)/(?P<attr>state)/?$' %
        re_uuid, nextsteps.NextSteps.as_view()),  # Set State for a next step
    url(r'^nextsteps/(?P<ns_uuid>%s)$' %
        re_uuid, nextsteps.EditNextSteps.as_view()),

    # Login + Signup:
    url(r'^login(?P<param>%s)?$' %
        re_token_reset_password, login.Login.as_view()),
    url(r'^signup/?$', signup.SignUp.as_view()),

    # User Actions
    url(r'^vf/?$', vf.VF.as_view()),
    url(r'^add-contact/?$', invite.InviteContact.as_view()),
    url(r'^invite-team-members/?$', invite.InviteTeamMember.as_view()),
    url(r'^add-feedback/?$', feedback.Feedback.as_view()),

    # Notifications - set notifications for specific user to is_read = True
    url(r'^notifications/reset/?$', notification.NotificationOps.as_view()),
    url(r'^notifications/num/?$', notification.PullNotifCount4User.as_view()),

    # Notifications - pull unread objects
    url(r'^notifications/(?P<user_uuid>%s)/(?P<offset>\d+)/(?P<limit>\d+)$' %
        re_uuid, notification.NotificationOps.as_view()),
    # Notifications - delete specific notification for a user
    url(r'^notifications/(?P<notif_uuid>%s)$' %
        re_uuid, notification.NotificationOps.as_view()),

    # Initialize the engagement leads
    url(r'^load-engagement-leads/?$',
        data_loader.EngLeadsDataLoader.as_view()),
    # Initialize companies
    url(r'^load-companies/?$', data_loader.CompaniesDataLoader.as_view()),

    # get/add CLAuditLogs
    url(r'^checklist/decision/(?P<decision_uuid>%s)/auditlog/$' %
        re_uuid, checklist_audit_log.DecisionAuditLog.as_view()),
    url(r'^checklist/(?P<checklistUuid>%s)/auditlog/$' %
        re_uuid, checklist_audit_log.ChecklistAuditLog.as_view()),

    # get/set CLDecision
    url(r'^checklist/decision/(?P<decision_uuid>%s)$' %
        re_uuid, checklist_decision.ClDecision.as_view()),
    # get/set CLDecision
    url(r'^checklist/(?P<checklistUuid>%s)/state/$' %
        re_uuid, checklist_set_state.ChecklistState.as_view()),

    url(r'^checklist/template/$', checklist.CheckListTemplates.as_view()),
    url(r'^checklist/templates/$', checklist.CheckListTemplates.as_view()),
    url(r'^checklist/template/(?P<templateUuid>%s)$' %
        re_uuid, checklist.CheckListTemplates.as_view()),

    # get Checklist (returns files and all templates)
    url(
        r'^engagement/(?P<eng_uuid>%s)/checklist/' % re_uuid +\
        '(?P<checklistUuid>%s)/nextstep/$' % re_uuid,\
        nextsteps.ChecklistNextStep.as_view()),
    url(r'^engagement/(?P<eng_uuid>%s)/checklist/new/$' %
        re_uuid, checklist.NewCheckList.as_view()),
    url(r'^checklist/(?P<checklistUuid>%s)$' %
        re_uuid, checklist.ExistingCheckList.as_view()),
    url(r'^checklist/$', checklist.ExistingCheckList.as_view()),

    url(r'^cms/posts/$', Posts.as_view()),
    url(r'^cms/pages/$', Pages.as_view()),
    url(r'^cms/pages/search/?$', PageSearch.as_view()),
    url(r'^cms/pages/(?P<id>\d+)/$', PageById.as_view()),
]
