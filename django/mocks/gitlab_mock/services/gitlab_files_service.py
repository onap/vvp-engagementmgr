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
import random


class GitlabFilesResultsSvc(object):

    num_of_required_files = 3

    def retrieve_files_for_vf_repo(self):
        list_of_files = list()
        for index in range(GitlabFilesResultsSvc.num_of_required_files):
            current_file_dict = dict()
            current_file_dict['id'] = ''.join(random.choice(
                '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(16))
            current_file_dict['name'] = 'file%d' % index
            current_file_dict['type'] = 'blob'
            current_file_dict['mode'] = '100644'
            list_of_files.append(current_file_dict)
        return list_of_files
