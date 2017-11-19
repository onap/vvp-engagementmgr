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
import requests
from engagementmanager.utils.validator import logEncoding
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class GitlabClient(object):
    """
    Class for performing various operations with gitlab
    like create project using Gitlab API.

    Gitlab API docs can be referred at:-
    http://doc.gitlab.com/ce/api/README.html
    """

    BASE_CTX = "/api/v3/"
    GROUPS_SUFFIX = BASE_CTX + "groups"
    PROJECTS_SUFFIX = BASE_CTX + "projects"
    PROJECT_TO_GROUP_SUFFIX = BASE_CTX + "groups/:id/projects/:project_id"
    USERS_SUFFIX = BASE_CTX + "users"
    KEYS_SUFFIX = BASE_CTX + "user/keys"
    EMAILS_SUFFIX = BASE_CTX + "user/emails"
    USER_PROJECT_PERMISSION_LEVEL = 40

    # TODO
#     url should be in wsetting.xml as gitlab_url

    def __init__(self, url, private_token):
        self.url = url
        self.groups_url = "%s%s" % (url, self.GROUPS_SUFFIX)
        self.projects_url = "%s%s" % (url, self.PROJECTS_SUFFIX)
        self.projects_to_group_url = "%s%s" % (
            url, self.PROJECT_TO_GROUP_SUFFIX)
        self.users_url = "%s%s" % (url, self.USERS_SUFFIX)
        self.keys_url = "%s%s" % (url, self.KEYS_SUFFIX)
        self.emails_url = "%s%s" % (url, self.EMAILS_SUFFIX)
        self.headers = {'PRIVATE-TOKEN': private_token}

    def create_group(self, params_dict):
        """
        Function creates a new group with specified parameters

        params_dict is a dict containing properties of group,
        """

        # assert that params_dict is a dict
        assert(isinstance(params_dict, dict))

        # assert that params_dict contains the value for cumpulsory field name
        # name field is used for assigning name to the project to be created
        assert('name' in params_dict)
        assert('path' in params_dict)
        created_group = False
        resp = requests.post(
            self.groups_url, data=params_dict, headers=self.headers)

        if not resp.json():
            logger.debug("couldnt create_group. response : %s", resp.content)
        else:
            created_group = resp.json()

#         logger.debug("create_group response : %s", resp.content)

        return created_group

    def create_project(self, name, **kwargs):
        """
        Function creates a new project with specified parameters.
        The following parameters are understood:

        name:           The name of the new project
        path:           Custom repository name for new project.
                        default: based on name
        namespace_id:   Namespace for the new project.
                        default: current user's namespace
        description
        issues_enabled
        merge_requests_enabled
        builds_enabled
        wiki_enabled
        snippets_enabled
        container_registry_enabled
        shared_runners_enabled
        public
        visibility_level
        import_url
        public_builds
        only_allow_merge_if_build_succeeds
        only_allow_merge_if_all_discussions_are_resolved
        lfs_enabled
        request_access_enabled

        https://docs.gitlab.com/ce/api/projects.html#create-project
        """

        # filter kwargs to known parameters and non-optional args
        parameters = dict({k: kwargs[k] for k in kwargs if k in [
            'path', 'namespace_id', 'description',
            'issues_enabled', 'merge_requests_enabled',
            'builds_enabled', 'wiki_enabled',
            'snippets_enabled', 'container_registry_enabled',
            'shared_runners_enabled', 'public',
            'visibility_level', 'import_url',
            'public_builds', 'only_allow_merge_if_build_succeeds',
            'only_allow_merge_if_all_discussions_are_resolved', 'lfs_enabled',
            'request_access_enabled',
        ]},
            name=name,
        )

        r = requests.post(
            self.projects_url, json=parameters, headers=self.headers)
        logger.debug("create_project. response : %s", r.json())
        r.raise_for_status()
        return r.json()

    def transfer_project_to_group(self, params_dict):
        """
        Function creates a new project with specified parameters

        params_dict is a dict containing properties of project like name,
        description, issues_enabled, public, wiki_enabled etc
        """

        # assert that params_dict is a dict
        assert(isinstance(params_dict, dict))

        # assert that params_dict contains the value for cumpulsory field name
        # name field is used for assigning name to the project to be created
        assert('name' in params_dict)

        resp = requests.post(
            self.projects_to_group_url, json=params_dict, headers=self.headers)
        logger.debug("transfer_project_to_group. response : %s", resp.content)

        return resp

    def remove_project(self, proj_id):
        """
        Function removes a project from gitlab server with given project id
        """
        url = "%s/%d" % (self.projects_url, int(proj_id))
        return requests.delete(url, headers=self.headers)

    def search_group_by_name(self, group_name):
        assert(group_name)
        group_found = None

        url = "%s/%s" % (self.groups_url, group_name)
        resp = requests.get(url, headers=self.headers)

        logger.debug("search_group response : %s", resp.content)

        if resp.status_code == 404 or not resp.json():
            logger.info("didnt find gitlab group : %s", resp.content)
        else:
            decoded_response = resp.json()
            if group_name == decoded_response['name']:
                group_found = decoded_response

        return group_found

    def search_project_in_group(self, project_name, group_id):
        assert(project_name)
        assert(group_id)

        url = "%s/search/%s" % (self.projects_url, project_name)
        resp = requests.get(url, headers=self.headers)
        project_found = False

        if not resp.json():
            logger.info("didnt find project: %s", logEncoding(resp.content))
        else:
            for project in resp.json():
                if (project_name == project['name'] and
                        group_id == project['namespace']['id']):
                    project_found = project
                    break

        return project_found

    def get_user_by_email(self, email):
        assert(email)
        user_found = False
        username = email.replace('@', "_at_")
        email = email.lower()
        url = "%s?username=%s" % (self.users_url, str(username))
        resp = requests.get(url, headers=self.headers)
        # logger.debug("get_user_by_email response: %s" % resp.content+".
        # Response code: %s" % resp.status_code)
        if not resp.json():
            logger.info("didnt find user: %s", logEncoding(resp.content))
        else:
            for user in resp.json():
                if email == user['email']:
                    user_found = user
                    break

        return user_found

    def add_user_to_project(self, gitlab_user_id, project_id):
        assert(gitlab_user_id)
        assert(project_id)

        params_dict = dict()
        params_dict['id'] = project_id
        params_dict['user_id'] = gitlab_user_id
        params_dict['access_level'] = self.USER_PROJECT_PERMISSION_LEVEL

        url = "%s/%s/members" % (self.projects_url, int(project_id))
        resp = requests.post(url, json=params_dict, headers=self.headers)
        user_added = False

        if not resp.json():
            logger.error(
                "couldn't add user to project: %s", logEncoding(resp.content))
        else:
            user_added = resp.json()

        return user_added

    def add_user_to_group(self, gitlab_user_id, group_id):
        assert(gitlab_user_id)
        assert(group_id)

        params_dict = dict()
        params_dict['id'] = group_id
        params_dict['user_id'] = gitlab_user_id
        params_dict['access_level'] = 50

        url = "%s/%s/members" % (self.groups_url, int(group_id))
        resp = requests.post(url, json=params_dict, headers=self.headers)
        user_added = False

        if not resp.json():
            logger.error(
                "couldnt add user to group: %s", logEncoding(resp.content))
        else:
            user_added = resp.json()

        return user_added

    def create_user(self, params_dict):
        """
        Function creates a new user on gitlab server,

        ** This operation needs admin rights for this **

        username, password and email must be specicifed in params_dict
        """

        # assert that params_dict is a dict
        assert(isinstance(params_dict, dict))

        # assert that params_dict contains the value for cumpulsory fields:-
        # name, password and email.
        assert('name' in params_dict)
        assert('username' in params_dict)
        assert('password' in params_dict)
        assert('email' in params_dict)
        user_created = False

        resp = requests.post(
            self.users_url, json=params_dict, headers=self.headers)

        if not resp.json():
            logger.error("couldnt create_user : %s", logEncoding(resp.content))
        else:
            user_created = resp.json()

#         logger.debug("create_user response: %s" % resp.content + ",
#         Response code: %s" % resp.status_code)

        return user_created

    def current_user(self):
        """
        Function gets information for currently authenticated user
        """
        url = "%s/api/v3/user" % self.url
        return requests.get(url, headers=self.headers)

    def delete_user(self, uid):
        """
        Function deletes a user from gitlab server with a given user id
        """
        url = "%s/%d" % (self.users_url, int(uid))
        return requests.delete(url, headers=self.headers)

    def remove_user_from_gitlab_project(self, project_id, uid):
        """
        Function removes a user from a gitlab project, using a given user id
        """
        url = self.projects_url + '/' + \
            str(project_id) + '/members/' + str(int(uid))
        return requests.delete(url, headers=self.headers)

    def list_users(self):
        """
        Function get list of all the gitlab user.

        ** This operation needs admin rights for this **
        """
        return requests.get(self.users_url, headers=self.headers)

    def list_usernames(self):
        """
        Function get list of all the gitlab usernames.

        ** This operation needs admin rights for this **
        """
        resp = requests.get(self.users_url, headers=self.headers)
#         logger.debug("list_usernames Response: "+resp.content)
        if resp.status_code == 200:
            return [u["username"] for u in resp.json()]
        return []

    def list_projects(self):
        """
        Function get list of all the projects
        """
        resp = requests.get(self.projects_url, headers=self.headers)
#         logger.debug("list_projects response: "+resp.content)
        return resp

    def list_ssh_keys_for_user(self, gitlab_user_id):
        """
        Function lists ssh keys for given user id

        ** This operation needs admin rights for this **
        """

        url = "%s/%s/keys" % (self.users_url, int(gitlab_user_id))
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def add_ssh_key(self, title, key):
        """
        Function adds SSH key to gitlab user account

        Needs a title for the SSH key and the SSH key

        """
        # composing params dict for POST
        data = {"title": title, "key": key}

        r = requests.post(self.keys_url, json=data, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def add_ssh_key_for_user(self, id, title, key):
        """
        Function adds SSH key to gitlab user account

        Needs a user id, title for the SSH key and the SSH key

        ** This operation needs admin rights for this **

        """
        # composing params dict for POST
        data = {"id": id, "title": title, "key": key}
        # composing url for adding key for given user id
        url = "%s/api/v3/users/%d/keys" % (self.url, int(id))
        r = requests.post(url, json=data, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def remove_ssh_key(self, id):
        """
        Function remove a SSH key for an authenticated user with given id
        """
        url = "%s/%d" % (self.keys_url, int(id))
        return requests.delete(url, headers=self.headers)

    def remove_ssh_key_for_user(self, uid, kid):
        """
        Function remove a SSH key for an given user id and with given key id

        ** This operation needs admin rights for this **
        """
        url = "%s/%d/keys/%d" % (self.users_url, int(uid), int(kid))
        return requests.delete(url, headers=self.headers)

    def list_ssh_keys(self):
        """
        Function list SSH keys of an authenticated user on gitlab server
        """
        return requests.get(self.keys_url, headers=self.headers)

    def create_project_for_user(self, id, proj_name):
        """
        Function creates a new project owned by the specified user.

        ** This operation needs admin rights for this **
        """
        url = "%s/user/%d" % (self.projects_url, int(id))

        # composing params dict for POST
        data = {"user_id": id, "name": proj_name}

        return requests.post(url, json=data, headers=self.headers)

    def add_email(self, email):
        """
        Function adds given email to given user id
        """
        url = "%s/api/v3/user/emails" % self.url

        # composing params dict for POST
        data = {"email": email}
        return requests.post(url, json=data, headers=self.headers)

    def add_email_for_user(self, id, email):
        """
        Function adds given email to given user id

        ** This operation needs admin rights for this **
        """
        url = "%s/api/v3/users/%d/emails" % (self.url, int(id))

        # composing params dict for POST
        data = {"id": id, "email": email}

        return requests.post(url, json=data, headers=self.headers)

    def list_emails(self):
        """
        Function lists emails for current authenticated user
        """
        return requests.get(self.emails_url, headers=self.headers)

    def list_emails_for_user(self, id):
        """
        Function lists emails for current authenticated user
        """
        url = "%s/api/v3/users/%d/emails" % (self.url, int(id))
        return requests.get(url, headers=self.headers)

    def get_repository_files(self, project_id):
        """
        Function retrieves all files for a given repository by project id
        (In VVP projectId is 1:1 with repo_id)
        GET /projects/:id/repository/tree
        Doc: https://docs.gitlab.com/ce/api/repositories.html
        """
#         endpoint = self.url+self.BASE_CTX+"projects/"+str(project_id)+
#         "/repository/tree"
        endpoint = "%s%sprojects/%s/repository/tree" % (
            self.url, self.BASE_CTX, str(project_id))
        logger.debug("get_repository_files endpoint=" + endpoint)
        resp = requests.get(endpoint, headers=self.headers)

        if resp.status_code == 404 and resp.json()['message'] == \
                '404 Tree Not Found':
            # When no initial commit has been created and there are
            # no files in the repo, the response is not an empty list
            # but "404 Tree Not Found." Intercept this and return
            # empty list instead.
            logger.info("get_repository_files: Looks like there are" +
                        "no associated file to project %s." +
                        "Response : %s, status = %s", logEncoding(
                            project_id), logEncoding(resp.content), 404)
            return []

        return resp.json()

    def get_project(self, project_id):
        """
        project_id: The ID of the project or NAMESPACE/PROJECT_NAME

        https://docs.gitlab.com/ce/api/projects.html
        """
        project_id = requests.utils.quote(str(project_id), safe='')
        endpoint = "%s/api/v3/projects/%s" % (self.url, project_id)
        r = requests.get(endpoint, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def list_project_hooks(self, project_id):
        """
        project_id: The ID of the project or NAMESPACE/PROJECT_NAME

        https://docs.gitlab.com/ce/api/projects.html
        """
        project_id = requests.utils.quote(str(project_id), safe='')
        endpoint = "%s/api/v3/projects/%s/hooks" % (self.url, project_id)
        return requests.get(endpoint, headers=self.headers).json()

    def edit_project_hook(self, project_id, url, hook_id=None, **kwargs):
        """
        project_id: The ID of the project or NAMESPACE/PROJECT_NAME
        url: the hook URL
        hook_id: the ID of the project hook, or None to create new

        The following boolean kwargs describe when to trigger the hook:
            push_events
            issues_events
            merge_requests_events
            tag_push_events
            note_events
            build_events
            pipeline_events
            wiki_events
        To do SSL verification when triggering the hook:
            enable_ssl_verification
        Secret token:
            token

        https://docs.gitlab.com/ce/api/projects.html
        """
        parameters = dict({k: kwargs[k] for k in kwargs if k in [
            'push_events', 'issues_events', 'merge_requests_events',
            'tag_push_events', 'note_events', 'build_events',
            'pipeline_events', 'wiki_events',
            'enable_ssl_verification', 'token']},
            id=project_id,
            url=url,
        )

        if hook_id is None:
            # New hook
            endpoint = "%s/api/v3/projects/%s/hooks" % (self.url, project_id)
            return requests.post(endpoint, json=parameters,
                                 headers=self.headers)
        else:
            # Update existing hook
            parameters['hook_id'] = hook_id
            endpoint = "%s/api/v3/projects/%s/hooks/%s" % (
                self.url, project_id, hook_id)
            return requests.put(endpoint, json=parameters,
                                headers=self.headers)

    def delete_project_hook(self, project_id, hook_id):
        endpoint = "%s/api/v3/projects/%s/hooks/%s" % (
            self.url, project_id, hook_id)
        return requests.delete(endpoint, headers=self.headers)
