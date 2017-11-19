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
import bleach

from engagementmanager.models import VFC, IceUserProfile, VF, Vendor
from engagementmanager.service.base_service import BaseSvc


class VFCSvc(BaseSvc):

    def create_vfc(self, data):
        msg = "OK"
        vf = None
        vfc = None
        user = None
        company = None
        duplicateNames = []
        duplicate = False
        many = True
        dict = {}
        # Iterate through all the VFCs that are received from the user,
        # if there's duplication -> check the VF,
        # if it is the same ->duplicate = True
        # If there's a duplication and the other
        # VFCs trying to be created are not
        # duplicated -> Many = True -> they would be successfully created any
        # way
        for i in range(len(data['vfcs'])):
            dict.update(data['vfcs'][i])
            # check if the VFC already exist (filter by name)
            try:
                vfc = VFC.objects.filter(
                    name=dict['name'], external_ref_id=dict['external_ref_id'])
                # if found VFC with same name and ref id
                if (vfc.count() > 0):
                    for item in vfc:
                        if (item.vf.uuid == data['vf_uuid']):
                            if (not duplicate):
                                duplicate = True
                            duplicateNames.append(dict['name'])
                    # if found a similar VFC with name and ref_id,\
                    # but VF is different (
                    # cannot use else, and raise,
                    # since the for has to check all vfcs that
                    # match - for example, 2 VFs with same vfc)
                    if not duplicate:
                        raise VFC.DoesNotExist
                # didn't find any vfc with same name and ref_id
                else:
                    raise VFC.DoesNotExist
            # If the VFC Does not exist, then continue as usual and create it.
            except VFC.DoesNotExist:
                many = True
                # not used, unless there's a duplicate as well, just a helper

                user = IceUserProfile.objects.get(
                    email=data['creator']['email'])
                vf = VF.objects.get(uuid=data['vf_uuid'])
                # Check if the company that the user entered already exist.
                try:
                    company = Vendor.objects.get(name=dict['company'])
                except Vendor.DoesNotExist:
                    company = Vendor.objects.create(
                        name=dict['company'], public=False)
                    company.save()
                # create the VFC
                vfc = VFC.objects.create(
                    name=dict['name'],
                    company=company,
                    vf=vf,
                    creator=user,
                    external_ref_id=dict['external_ref_id'])
                if 'ice_mandated' in dict:
                    vfc.ice_mandated = dict['ice_mandated']
                vfc.save()

            dict = {}
        if duplicate and many:
            num = 1
            for vfc_name in duplicateNames:
                msg = msg + str(num) + ". The VFC " + vfc_name + \
                    " already exist, the VF that it is related to is: "\
                    + item.vf.name + "\n"
                num += 1
            msg = msg + "\nThe other VFCs were created succesfully\n"
            self.logger.error(msg)
            msg = bleach.clean(msg, tags=['a', 'b'])
        return msg

    def delete_vfc(self, vfc_uuid):
        VFC.objects.get(uuid=vfc_uuid).delete()
