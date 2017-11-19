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
from uuid import uuid4
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.template.loader import render_to_string
import requests
from engagementmanager.decorator.retry import retry_connection
from engagementmanager.models import Engagement, IceUserProfile, \
    Role, Checklist,\
    ChecklistDecision, ChecklistLineItem, CheckListState, \
    ChecklistTemplate, VF
from engagementmanager.serializers import VFModelSerializerForSignal
from engagementmanager.utils.constants import Roles, EngagementStage, \
    CheckListLineType, JenkinsBuildParametersNames, RGWApermission, CheckListCategory
from engagementmanager.utils.cryptography import CryptographyText
from engagementmanager.utils.validator import logEncoding
from mocks.gitlab_mock.rest.gitlab_files_respons_rest import \
    GitlabFilesResultsREST
from mocks.jenkins_mock.rest.jenkins_tests_validation_rest import \
    JenkinsTestsResultsREST

from rgwa_mock.services.rgwa_keys_service import RGWAKeysService
from validationmanager.rados.rgwa_client_factory import RGWAClientFactory
from validationmanager.utils.clients import get_jenkins_client, \
    get_gitlab_client
from validationmanager.tasks import request_scan
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()
config_xml_content = None
jenkins_mock_object = JenkinsTestsResultsREST()


def jenkins_job_and_gitlab_repo_exists_callback(vf):
    if not settings.IS_SIGNAL_ENABLED:
        return True
    logger.debug(
        "Engagement Manager has signaled to check if repo exists")
    if not get_jenkins_client().job_exists(vf.jenkins_job_name()):
        logger.debug("Jenkins job %s doesnt exists...", vf.jenkins_job_name())
        return False

    gitlab = get_gitlab_client()
    # ensure group git gitlab was created
    existing_group = gitlab.search_group_by_name(
        vf.engagement.engagement_manual_id)
    if not existing_group:
        logger.debug(
            "Group %s doesnt exists in gitlab...",
            vf.engagement.engagement_manual_id)
        return False

    """Return the id for Gitlab project, creating it if it does not exist."""
    project = gitlab.search_project_in_group(vf.name, existing_group['id'])
    if not project:
        logger.debug("Project %s doesnt exists...", vf.name)
        return False

    return True


def cl_from_pending_to_automation_callback(vf, checklist):
    if not settings.IS_SIGNAL_ENABLED:
        jenkins_mock_object.post(vf.git_repo_url, checklist.uuid)
    else:
        logger.debug(
            "Engagement Manager has signaled that a checklist state was " +
            "changed from pending to automation")
        if checklist.template and checklist.template.category == CheckListCategory.glance.name:
            logger.debug("Triggering image scan")
            request_scan(vf, checklist)
        elif checklist.template and checklist.template.category == CheckListCategory.heat.name:
            logger.debug("Triggering heat template validation")
            get_jenkins_client().build_job(
                vf.jenkins_job_name(), {
                    'checklist_uuid': checklist.uuid,
                    'git_repo_url': vf.git_repo_url,
                })


def provision_new_vf_callback(vf):
    """Given a new vf, provision Gitlab and Jenkins for it.

    Note: despite its name, this signal is not used only for new vfs,
    but to update existing gitlab and jenkins provisioning when a vf
    changes e.g. when team members are added or removed.

    This function will either succeed (and return None), or throw
    an exception.
    """
    logger.debug(
        "Engagement Manager has signaled that a new VF has been created")
    if not settings.IS_SIGNAL_ENABLED:
        ensure_checklists(vf)
    else:
        if not vf:
            raise ValueError("vf %r not found" % vf)

        ensure_git_entities(vf)
        ensure_jenkins_job(vf)
        ensure_checklists(vf)
        ensure_rgwa_entities(vf)


def get_list_of_repo_files_callback(vf):
    """Given a vf, return its file list.
    This function will either succeed (and return a list),
    or throw an exception.
    """
    logger.debug(
        "Engagement Manager has signaled that there is a need " +
        "to fetch the VF associated files")
    if not settings.IS_SIGNAL_ENABLED:
        files = GitlabFilesResultsREST().get(vf)
        return files
    else:
        gitlab = get_gitlab_client()
        project = get_project_by_vf(vf, gitlab)
        project_id = project['id']
        logger.debug(
            "Project_id for fetched associated files is %s", project_id)
        files = gitlab.get_repository_files(project_id)
        logger.debug("gitlab.get_repository_files returned %r", files)
        return files


def ssh_key_created_or_updated_callback(user):
    if not settings.IS_SIGNAL_ENABLED:
        return None
    logger.debug("Engagement Manager has signaled that a user has " +
                 "created or updated an ssh key")
    user_dict = model_to_dict(user)
    gitlab = get_gitlab_client()
    gitlab_user = gitlab.get_user_by_email(user.email)
    if not gitlab_user:
        gitlab_user = create_user_in_gitlab(user_dict, gitlab)
        logger.debug("created user in gitlab=%s", user.email)

    if 'id' not in gitlab_user:
        err_msg = "coudln't get gitlab user %s " % user.uuid
        raise ValueError(err_msg)
    update_user_ssh_keys(user_dict, gitlab, gitlab_user)
    logger.debug(
        "Successfuly created/updated user in the git in " +
        "key_created_or_updated signal")


@retry_connection
def ensure_checklists(vf):
    '''
    Ensure there is at least one entry of all checklists template for a
    given vf
    '''
    engagement = vf.engagement
    reviewer = engagement.reviewer

    existing_checklists = Checklist.objects.filter(engagement=engagement)
    existing_checklists_templates = set([c.template.category
                                         for c in existing_checklists])

    cts = ChecklistTemplate.objects.all()
    for ct in cts:
        if ct.category in existing_checklists_templates:
            continue

        # grab all the line items to determine the state to create the line
        line_items_list = ChecklistLineItem.objects.filter(template=ct)
        line_items_manual = [li.line_type == CheckListLineType.manual.name
                             for li in line_items_list]

        # set the checklist state
        checklist_state = CheckListState.pending.name
        if all(line_items_manual):
            checklist_state = CheckListState.review.name

        checklist = Checklist.objects.create(
            name=ct.name,
            validation_cycle=1,
            associated_files=[],
            state=checklist_state,
            engagement=engagement,
            template=ct,
            creator=reviewer,
            owner=reviewer)

        for line_item in line_items_list:
            ChecklistDecision.objects.create(
                checklist=checklist,
                template=ct,
                lineitem=line_item)


@retry_connection
def ensure_jenkins_job(vf):
    """Given a vf, ensure that its jenkins/TestEngine jobs exist.

    This function will either succeed (and return None), or throw an exception.

    """
    # we cache the configuration in a module-level variable.
    global config_xml_content
    if config_xml_content is None:
        config_xml_content = get_jenkins_job_config()

    jenkins = get_jenkins_client()
    job_name = vf.jenkins_job_name()

    for namesuffix, xml in config_xml_content.items():
        name = job_name + namesuffix

        # FIXME test-then-set can cause a race condition, so maybe better
        # to attempt to create and ignore "already exists" error.
        if jenkins.job_exists(name):
            logger.debug(
                "TestEngine job %s for VF %s already provisioned, skipping.",
                name, vf.name)
            continue

        logger.debug("creating TestEngine job %s for VF %s", name, vf.name)
        jenkins.create_job(name, xml)


@retry_connection
def get_jenkins_build_log(vf, checklistUuid):
    """Given a vf, retrieve its jenkins build log.

    This function will either succeed (and return the build log).

    """
    if not settings.IS_SIGNAL_ENABLED:
        return jenkins_mock_object.get(
            vf.engagement.engagement_manual_id, vf.name)
    logger.debug("Retrieving VF's(%s) last Jenkins build log " % (vf.name))
    jenkins = get_jenkins_client()
    job_name = vf.jenkins_job_name()
    vf_builds = jenkins.server.get_job_info(
        job_name, depth=1, fetch_all_builds=True)
    build_num = -1
    logs = ''
    for build in vf_builds['builds']:
        for parameter in build['actions'][0]['parameters']:
            if parameter['name'] == \
                    JenkinsBuildParametersNames.CHECKLIST_UUID:
                if parameter['value'] == checklistUuid:
                    logger.debug(
                        "I have succeeded to match the given checklist uuid \
                        to one of the VF's builds' checklist_uuid")
                    build_num = build['number']
    if build_num < 0:
        logger.error(
            "Failed to match the given checklist uuid to one of the VF's \
            builds' checklist_uuid")
    else:
        logs = jenkins.server.get_build_console_output(job_name, build_num)
    return logs


def get_jenkins_job_config():
    """Return the XML configurations for the Jenkins/TestEngine build job and
    the Jenkins/Imagescanner results processing job.

    The configurations are templated, and the context provided will include the
    appropriate webhook endpoint for its notification callbacks. It is not
    cached; do that from a higher level caller.

    """
    # replacing auth in the view name 'jenkins-notification-endpoint'
    # (url.py) and appending it to the url from settings
    context = {
        'notification_endpoint': "http://%s%s" % (
            settings.API_DOMAIN,
            reverse(
                'jenkins-notification-endpoint',
                kwargs={'auth_token': settings.WEBHOOK_TOKEN}))}
    return {
        '': render_to_string('jenkins_job_config.xml', context),
        '_scanner': render_to_string('imagescanner_job_config.xml', context),
    }


@retry_connection
def ensure_git_webhook(gitlab, project_id):
    """Given a gitlab client and project id, set its webhook
    notification endpoint appropriately and exclusively.

    Any other existing webhooks will be removed.

    This function will either succeed (and return None),
    or throw an exception.
    """
    webhook_endpoint = "http://%s%s" % (settings.API_DOMAIN, reverse(
        'git-push-endpoint', kwargs={'auth_token': settings.WEBHOOK_TOKEN}))
    logger.debug("setting gitlab project %r webhook_endpoint to %s",
                 project_id, webhook_endpoint)

    exists = False
    for hook in gitlab.list_project_hooks(project_id):
        if (hook['url'] == webhook_endpoint and
                hook['push_events'] and
                hook['enable_ssl_verification']):
            logger.debug(
                "webhook to %r already set correctly in project %r",
                hook['url'], project_id)
            exists = True
            continue

        logger.debug(
            "deleting old webhook to %r in project %r",
            hook['url'], project_id)
        gitlab.delete_project_hook(project_id, hook['id'])

    if not exists:
        logger.debug(
            "installing new webhook to %r in project %r",
            webhook_endpoint, project_id)
        gitlab.edit_project_hook(
            project_id, webhook_endpoint, push_events=True,
            enable_ssl_verification=True)


@retry_connection
def add_users_to_git_project(gitlab, formated_vf, project_id):
    # add users to project
    # hold array of all members added to project in order to exclude them in
    # further queries.
    el_role = Role.objects.get(name=Roles.el.name)  # @UndefinedVariable
    admin_role = Role.objects.get(name=Roles.admin.name)  # @UndefinedVariable
    user_added = None
    engagement_team_list = []
    for user in formated_vf['engagement']['engagement_team']:
        engagement_team_list.append(user['uuid'])
        # @UndefinedVariable
        engagement_stage = formated_vf['engagement']['engagement_stage']
        if (engagement_stage == EngagementStage.Active.name or
                user['role']['name'] in (admin_role.name, el_role.name)):
            user_added = send_user_data_to_gitlab_and_to_project(
                user, project_id, gitlab)
            if not user_added:
                err_msg = "Failed: Engagement team user with uuid " + \
                    user['uuid'] + " was not added to project"
                logger.error(err_msg)
                raise Exception(err_msg)

    # In case a project has been created add all EL & Admins that not already
    # part of the git project
    el_admin_list = IceUserProfile.objects.all().filter(Q(role=el_role) | Q(
        role=admin_role)).exclude(uuid__in=engagement_team_list).values()
    for user in el_admin_list:
        user_added = send_user_data_to_gitlab_and_to_project(
            user, project_id, gitlab)
        if not user_added:
            err_msg = "el/admin user  with uuid " + \
                user['uuid'] + " was not added to project " + project_id
            logger.error(logEncoding(err_msg))
            raise Exception(err_msg)


def ensure_git_entities(vf):
    """Given a vf, ensure that its Gitlab group/project are
    created, with webhook and users.

    This function will either succeed (and return None),
    or throw an exception.
    """
    gitlab = get_gitlab_client()
    # Target project name is of the form {ENG_MANUAL_ID}/{VF_NAME}
    # Populate data to be entered/compared in gitlab
    formated_vf = VFModelSerializerForSignal(vf).data

    group_id = get_or_create_git_group(
        vf.engagement.engagement_manual_id, gitlab)

    project_id = get_or_create_git_project(vf, gitlab, group_id)

    ensure_git_webhook(gitlab, project_id)
    engagement_stage = formated_vf['engagement']['engagement_stage']
    if (engagement_stage == EngagementStage.Validated.name or
            engagement_stage == EngagementStage.Completed.name
            or engagement_stage == EngagementStage.Archived.name):
        remove_all_standard_users_from_project(gitlab, project_id, formated_vf)
    else:
        add_users_to_git_project(gitlab, formated_vf, project_id)

    logger.debug(
        "ensure_git_entities: Successfully added all " +
        "VF engagement team to project %s", project_id)


@retry_connection
def get_or_create_git_group(name, client):
    """Return the id for Gitlab group 'name', creating it if
    it does not exist."""
    existing_group = client.search_group_by_name(name)
    if existing_group:
        logger.debug("Group %s exists...", name)
        return existing_group['id']
    else:
        logger.debug("Group %s doesn't exists, creating it...", name)
        result = client.create_group({'name': name, 'path': name})
        logger.debug("create_group response: %r", result)
        return result['id']


@retry_connection
def get_or_create_git_project(vf, gitlab, group_id):
    """Return the id for Gitlab project, creating it if it does not exist."""
    project = gitlab.search_project_in_group(vf.name, group_id)
    if project:
        logger.debug("Project %s exists...", vf.name)
    elif not vf.git_repo_url or vf.git_repo_url == '-1':
        logger.debug("Project %s doesn't exists, creating it...", vf.name)
        """Given a vf object, create a git project for it and return its gitlab id.
        A pre-existing project of the same group and name is an error.
        """
        project = gitlab.create_project(
            name=vf.name, path=vf.name.replace(' ', '_'),
            namespace_id=group_id)
        logger.debug(
            "get_or_create_git_project: project created " +
            "with id=%s", project['id'])
    else:
        raise ValueError("Couldn't find GitLab project " +
                         "but gitlab url exists. %s: %s" % (
                             vf.name, vf.git_repo_url))

    if vf.git_repo_url != project['ssh_url_to_repo']:
        # Make sure repo url in DB is updated"
        vf = VF.objects.get(uuid=vf.uuid)
        vf.git_repo_url = project['ssh_url_to_repo']
        vf.save()
        logger.debug(
            "get_or_create_git_project: git_repo_url=%s, " +
            "was updated", vf.git_repo_url)

    return project['id']


def get_project_by_vf(vf, gitlab):
    project_id = "%s/%s" % (vf.engagement.engagement_manual_id,
                            vf.name.replace(' ', '_'))
    try:
        return gitlab.get_project(project_id)
    except requests.exceptions.HTTPError as exc:
        msg = "Couldn't find GitLab project %s: %s" % (
            project_id, exc.response.content)
        if exc.response.status_code == 404:
            logger.error(msg)
        raise ValueError(msg)


def send_user_data_to_gitlab_and_to_project(user, project_id, gitlab):
    logger.debug(
        "send_user_data_to_gitlab_and_to_project %r %r",
        user['email'], project_id)
    gitlab_user_id = None
    existing_gitlab_user = gitlab.get_user_by_email(user['email'])

    if not existing_gitlab_user or 'id' not in existing_gitlab_user:
        logger.debug(
            "User with email %s doesn't exists in gitlab, " +
            "trying to add him", user['email'])

        created_gitlab_user = create_user_in_gitlab(user, gitlab)
        logger.debug("Created user %s in gitlab", user['email'])

        gitlab_user_id = created_gitlab_user['id']

        update_user_ssh_keys(user, gitlab, created_gitlab_user)
        logger.debug("Updated user %s ssh keys in gitlab", user['email'])
    else:
        gitlab_user_id = existing_gitlab_user['id']
        update_user_ssh_keys(user, gitlab, existing_gitlab_user)

    user_added = gitlab.add_user_to_project(gitlab_user_id, project_id)

    if not user_added:
        err_msg = "GitLab User with gitlab user uuid " + \
            gitlab_user_id + " not added to git project " + project_id
        logger.error(logEncoding(err_msg))
        raise Exception(err_msg)

    return user_added


def add_user_to_gitlab_and_to_project(user, project_id, gitlab):
    logger.debug("add_user_to_gitlab_and_to_project %r %r",
                 user['email'], project_id)
    gitlab_user_id = None

    existing_gitlab_user = gitlab.get_user_by_email(user['email'])

    if not existing_gitlab_user or 'id' not in existing_gitlab_user:
        logger.debug(
            "User with email %s doesn't exists in gitlab, " +
            "trying to add him", user['email'])

        created_gitlab_user = create_user_in_gitlab(user, gitlab)
        logger.debug("Created user %s in gitlab", user['email'])

        gitlab_user_id = created_gitlab_user['id']

        update_user_ssh_keys(user, gitlab, created_gitlab_user)
        logger.debug("Updated user %s ssh keys in gitlab", user['email'])
    else:
        gitlab_user_id = existing_gitlab_user['id']
        update_user_ssh_keys(user, gitlab, existing_gitlab_user)

    user_added = gitlab.add_user_to_project(gitlab_user_id, project_id)

    if not user_added:
        err_msg = "GitLab User with gitlab user uuid " + \
            gitlab_user_id + " not added to git project " + project_id
        logger.error(logEncoding(err_msg))
        raise Exception(err_msg)

    return user_added


# Remove user from project, if their is not related to any project - delete
# user from gitlab.
def remove_all_standard_users_from_project(gitlab, project_id, formatted_vf):
    if not settings.IS_SIGNAL_ENABLED:
        return None
    el_role = Role.objects.get(name=Roles.el.name)  # @UndefinedVariable
    admin_role = Role.objects.get(name=Roles.admin.name)  # @UndefinedVariable
    for user in formatted_vf['engagement']['engagement_team']:
        if user['role']['name'] in (el_role.name, admin_role.name):
            continue
        # call signal that checks how many eng teams is the user involved in
        else:
            existing_gitlab_user = gitlab.get_user_by_email(user['email'])
            remove_user_from_project(existing_gitlab_user, project_id, gitlab)
            payload = {"email": user['email']}
            logger.debug('sending test_finished with payload %s', payload)
            num_of_eng_teams = Engagement.objects.filter(
                engagement_team__email=user['email'],
                engagement_stage=EngagementStage.Active.name).count()
            if num_of_eng_teams == 0:
                remove_user_from_gitlab(existing_gitlab_user, gitlab)
    return None


def create_user_in_gitlab(user, gitlab):
    logger.debug("create_user_in_gitlab %s", user['email'])
    user_dict = {
        'name': user['full_name'],
        'username': user['email'].replace('@', "_at_"),
        'password': str(uuid4()),
        'email': user['email'].lower(),
    }
    gitlab_user = gitlab.create_user(user_dict)
    update_user_ssh_keys(user, gitlab, gitlab_user)

    return gitlab_user


def remove_user_from_gitlab(user, gitlab):
    logger.debug("remove_user_from_gitlab %s", user['email'])
    return gitlab.delete_user(user['id'])


def remove_user_from_project(user, project_id, gitlab):
    logger.debug("remove_user_from_project %s", user['email'])
    return gitlab.remove_user_from_gitlab_project(project_id, user['id'])


@retry_connection
def update_user_ssh_keys(user_dict, gitlab, gitlab_user):
    """Update Gitlab with the user's ssh key, and delete all others.

    If the user has no ssh key, this will be reflected in Gitlab:
    any ssh keys there will be deleted.

    user_dict: dictionary of IceUserProfile model data, e.g.
    from django.forms.models.model_to_dict()
        gitlab: gitlab client object
        gitlab_user: dictionary of gitlab user data

    This function will either succeed (and return None), or throw an exception.
    """
    ssh_key = user_dict['ssh_public_key']
    gitlab_user_id = gitlab_user['id']
    logger.debug("update_user_ssh_keys for %s", user_dict['email'])

    # remove all old ssh keys
    for old_ssh_key in gitlab.list_ssh_keys_for_user(gitlab_user_id):
        gitlab.remove_ssh_key_for_user(gitlab_user_id, old_ssh_key['id'])

    if not ssh_key:
        return None

    try:
        gitlab.add_ssh_key_for_user(
            gitlab_user_id, 'ssh key added by system', ssh_key)
    except requests.exceptions.HTTPError as exc:
        if exc.response.status_code == 400:
            # This typically occurs when a user uploads a key in use
            # by a different user. It is accepted by engagementmanager
            # but rejected by Gitlab.
            # FIXME: how do we, when running in a background thread,
            # communicate this failure to the user?
            logger.error(exc.response.content)
        raise


def ensure_rgwa_entities(vf):
    """Given a vf, ensure that its RGWA BUCKET are
    created.
    """
    formated_vf = VFModelSerializerForSignal(vf).data
    engagement_stage = formated_vf['engagement']['engagement_stage']
    bucket_name = vf.engagement.engagement_manual_id + "_" + vf.name.lower()
    if engagement_stage == EngagementStage.Active.name:
        bucket = get_or_create_bucket(bucket_name)
        add_bucket_users(bucket, vf)
    elif engagement_stage == EngagementStage.Validated.name or\
            engagement_stage == EngagementStage.Completed.name or\
            engagement_stage == EngagementStage.Archived.name:
        bucket = get_or_create_bucket(bucket_name)
        remove_bucket_users_grants(bucket, vf)


def create_user_rgwa(user):
    if settings.IS_SIGNAL_ENABLED:
        logger.debug("Engagement Manager has signaled that a user has " +
                     "created an rgwa")
        rgwa = RGWAClientFactory.admin()
        rgwa_user = rgwa.get_user(user.uuid)
        if rgwa_user is None:
            logger.debug(
                user.full_name + "User does not exist, a new one is created!")
            try:
                rgwa_user = rgwa.create_user(
                    uid=user.uuid,
                    display_name=user.full_name,
                    # admin will create and own the buckets users use. note:
                    # radosgw treats 0 as "unlimited", -1 as "none"
                    max_buckets=-1,
                )
                user = IceUserProfile.objects.get(uuid=user.uuid)
                access_key = rgwa_user['keys'][0]['access_key']
                secret_key = CryptographyText.encrypt(
                    rgwa_user['keys'][0]['secret_key'])
                user.rgwa_access_key = access_key
                user.rgwa_secret_key = secret_key
                user.save()
                logger.debug(
                    "Successfuly created user in the rgwa in " +
                    "create_user_rgwa signal" +
                    str(rgwa_user))
            except Exception as e:
                logger.error(str(e))
                err_msg = "coudln't get rgwa user %s " % user.uuid
                raise ValueError(err_msg)
    else:
        rgwa_user = RGWAKeysService().mock_create_user(
            uid=user.uuid, display_name=user.full_name)
        user = IceUserProfile.objects.get(uuid=user.uuid)
        user.rgwa_access_key = rgwa_user['access_key']
        user.rgwa_secret_key = CryptographyText.encrypt(
            rgwa_user['secret_key'])
        user.save()


def validate_rgwa_user(uuid):
    rgwa = RGWAClientFactory.admin()
    rgwa_user = rgwa.get_user(uuid)
    if rgwa_user is None:
        create_user_rgwa(IceUserProfile.objects.get(uuid=uuid))


@retry_connection
def add_bucket_users(bucket, vf):
    for user in vf.engagement.engagement_team.all():
        add_bucket_user(user, bucket)


def add_bucket_user(user, bucket):
    try:
        validate_rgwa_user(user.uuid)
        bucket_acl = bucket.get_acl()
        grants = set((grant.id, grant.permission)
                     for grant in bucket_acl.acl.grants)
        for permission in [RGWApermission.READ, RGWApermission.WRITE]:
            if (user.uuid, permission) in grants:
                continue
            bucket_acl.acl.add_user_grant(permission, user.uuid)
        bucket.set_acl(bucket_acl)
    except Exception as e:
        err_msg = "Failed: Engagement team user with uuid " + \
            user.uuid + " was not added to bucket"
        logger.error(err_msg)
        raise e


@retry_connection
def get_or_create_bucket(name):
    """Return the Bucket, creating it if
    it does not exist."""
    boto_conn = RGWAClientFactory.standard()

    try:
        bucket = boto_conn.lookup(name)
        if bucket is None:
            bucket = boto_conn.create_bucket(name)
        return bucket
    except Exception as e:
        logger.error("Problem get or create Rados GW bucket", e)
        raise e


def remove_bucket_users_grants(bucket, vf):
    for user in vf.engagement.engagement_team.all():
        remove_bucket_user_grants(bucket, user)


def remove_bucket_user_grants(bucket, user):
    bucket_acl = bucket.get_acl()
    bucket_acl.acl.grants = [
        grant for grant in bucket_acl.acl.grants if not grant.id ==
        user.uuid]
    bucket.set_acl(bucket_acl)
