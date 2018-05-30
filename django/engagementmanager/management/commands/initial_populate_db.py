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
""" intial_populate_db
Will create initial content to use this system.

This command is creating users, templates, companies,
deployment targets, sites and much more.
Will run at the state of a clean system so it won't cause data collisions.

WARNING: Do not run while there is data at the system.
"""
import inspect
import random
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from engagementmanager.models import Role, Vendor, \
    IceUserProfile, DeploymentTarget, \
    DeploymentTargetSite, Checklist, ChecklistDecision, ChecklistLineItem, \
    ChecklistTemplate, ChecklistSection, ECOMPRelease, Engagement, \
    CustomUser
from engagementmanager.models import VF
from engagementmanager.serializers import ThinVFModelSerializer
from engagementmanager.utils.constants import Roles, Constants
from engagementmanager.utils.validator import logEncoding
from engagementmanager.views_helper import createUserTemplate
from validationmanager.models import ValidationTest
from uuid import uuid4
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class Command(BaseCommand):

    def handle(self, *args, **options):
        if (settings.ENVIRONMENT == "local" or
                settings.ENVIRONMENT == "development"):
            execute_bootstrap_actions()


companies = [
    'Test Company 1',
    'Test Company 2'
]

companies_not_public = [
    'Private Company 1',
    'Private Company 2'
]

admin_dummy_users = [['admin bogus user',
                      Constants.service_provider_admin_mail,
                      '+1-23-456-78901']]

admin_ro_dummy_users = [
    ['ro admin bogus user', Constants.service_provider_admin_ro_mail,
     '+1-23-456-78901']]

dummy_users = [
    ['Bugs Bunny', 'bb@' + Constants.service_provider_mail_domain[0],
     '+1-555-555-5555'],
    ['CI Standard 1', 'ci_standard_1@' +
        Constants.service_provider_mail_domain[0], '+1-555-555-5555'],
]

el_dummy_users = [
    ['Donald Duck', 'dd1122@' +
        Constants.service_provider_mail_domain[0], '+1-555-555-5555'],
    ['Homer Simpson', 'hs0007@' +
        Constants.service_provider_mail_domain[0], '+1-555-555-5555']
]

checklist_templates = [
    {
        'name': 'Heat Templates',
        'category': 'heat',
        'version': 1,
        'sections': [
            {
                'name': 'Basic Heat Format and Syntax',
                'weight': 1,
                'description': 'section description',
                'validation_instructions': 'validation instructions',
                'line_items': [
                    {
                        'name': 'Filenames',
                        'weight': 1,
                        'description': 'description',
                        'validation_instructions': 'Here are some \
                        useful tips for how to validate this item in \
                        the most awesome way:<br><br><ul><li>Here is \
                        my awesome tip 1</li><li>Here is my awesome tip \
                        2</li><li>Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Valid YAML and HEAT',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    }
                ]
            },
            {
                'name': 'Parameter And Resource Specification',
                'weight': 1,
                'description': 'section description',
                'validation_instructions': 'validation instructions',
                'line_items': [
                    {
                        'name': 'Parameters',
                        'weight': 1,
                        'description': 'description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Resources',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Unique Names for Resources',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Outputs',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    }
                ]

            },
            {
                'name': 'Naming Conventions',
                'weight': 1,
                'description': 'section description',
                'validation_instructions': 'validation instructions',
                'line_items': [
                    {
                        'name': 'Name, Flavor, and Image Assignments',
                        'weight': 1,
                        'description': 'description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Availability Zones',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Required Metadata',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Optional Metadata',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Volumes',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Keys and Keypairs',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Networks',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Subnet',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Fixed IPs',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome tip 1\
                        </li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Allowed Address Pairs',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Ports',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    }
                ]

            },
            {
                'name': 'General Guidelines',
                'weight': 1,
                'description': 'section description',
                'validation_instructions': 'validation instructions',
                'line_items': [
                    {
                        'name': 'HEAT Files Support (get_file)',
                        'weight': 1,
                        'description': 'description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'HTTP-based references',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Anti-Affinity and Affinity Rules',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Resource Data Synchronization',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    }
                ]

            }
        ]
    },
    {
        'name': 'Image Validation',
        'category': 'glance',
        'version': 1,
        'sections': [
            {
                'name': 'Prerequisites',
                'weight': 1,
                'description': 'section description',
                'validation_instructions': 'validation instructions',
                'line_items': [
                    {
                        'name': 'Image Source',
                        'weight': 1,
                        'description': 'description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Vendor Provided Image',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    }
                ]
            },
            {
                'name': 'Image Scan',
                'weight': 1,
                'description': 'section description',
                'validation_instructions': 'validation instructions',
                'line_items': [
                    {
                        'name': 'Clam AV Scan',
                        'weight': 1,
                        'description': 'description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                ]
            },
        ]
    },
    {
        'name': 'OpenStack Instantiation',
        'category': 'instantiation',
        'version': 1,
        'sections': [
            {
                'name': 'Prerequisites',
                'weight': 1,
                'description': 'section description',
                'validation_instructions': 'validation instructions',
                'line_items': [
                    {
                        'name': 'Validated Heat Template(s)',
                        'weight': 1,
                        'description': 'description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Validated Glance Image(s)',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    }
                ]
            },
            {
                'name': 'Manual Instantiation in OpenStack',
                'weight': 1,
                'description': 'section description',
                'validation_instructions': 'validation instructions',
                'line_items': [
                    {
                        'name': 'Create the HEAT Stack',
                        'weight': 1,
                        'description': 'description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Delete the HEAT Stack',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    }
                ]
            }
        ]
    },
    {
        'name': 'SDC Onboarding',
        'category': 'sdc',
        'version': 1,
        'sections': [
            {
                'name': 'Prerequisites',
                'weight': 1,
                'description': 'section description',
                'validation_instructions': 'validation instructions',
                'line_items': [
                    {
                        'name': 'Validated Heat Template(s)',
                        'weight': 1,
                        'description': 'description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Validated Glance Image(s)',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome tip\
                         1</li><li>Here is my awesome tip 2</li><li>\
                         Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                    {
                        'name': 'Successful Manual Instantiation',
                        'weight': 1,
                        'description': 'Description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    }
                ]
            },
            {
                'name': 'Onboard The VNF To The Target SDC Environment',
                'weight': 1,
                'description': 'section description',
                'validation_instructions': 'validation instructions',
                'line_items': [
                    {
                        'name': 'Create the VNF',
                        'weight': 1,
                        'description': 'description',
                        'validation_instructions': 'Here are some useful \
                        tips for how to validate this item in the most \
                        awesome way:<br><br><ul><li>Here is my awesome \
                        tip 1</li><li>Here is my awesome tip 2</li><li>\
                        Here is my awesome tip 3</li></ul>',
                        'line_type': 'manual',
                    },
                ]
            },
        ]
    }
]

# Map all the validation tests to the right line items
#
#   Get the validation test mappings like this from a reference deployment:
#   from validationmanager.models import ValidationTest
#   vts = sorted(ValidationTest.objects.all(), key=lambda vt: vt.name)
#   for vt in vts:
#       for li in vt.line_items.all():
#           print("['" + vt.name + "', '" + li.name + "'],")
heat_validation_tests = [
    ['test_all_nested_templates_provided', 'Filenames'],
    ['test_all_referenced_resources_exists', 'Resources'],
    ['test_allowed_address_pairs_format', 'Allowed Address Pairs'],
    ['test_allowed_address_pairs_format', 'Ports'],
    ['test_allowed_address_pairs_include_vm_type_network_role', 'Ports'],
    ['test_allowed_address_pairs_include_vm_type_network_role', 'Ports'],
    ['test_alphanumeric_resource_ids_only', 'Resources'],
    ['test_availability_zone_naming', 'Availability Zones'],
    ['test_availability_zone_naming_use_get_param', 'Availability Zones'],
    ['test_base_template_names', 'Filenames'],
    ['test_base_template_outputs_consumed', 'Outputs'],
    ['test_default_values', 'Parameters'],
    ['test_env_and_yaml_same_name', 'Filenames'],
    ['test_env_files_provided', 'Filenames'],
    ['test_environment_file_contains_required_sections',
     'Valid YAML and HEAT'],
    ['test_environment_file_extension', 'Filenames'],
    ['test_environment_file_sections_have_the_right_format',
     'Valid YAML and HEAT'],
    ['test_environment_structure', 'Valid YAML and HEAT'],
    ['test_fixed_ips_format', 'Fixed IPs'],
    ['test_fixed_ips_format', 'Ports'],
    ['test_fixed_ips_format_use_get_parm', 'Fixed IPs'],
    ['test_fixed_ips_format_use_get_parm', 'Ports'],
    ['test_fixed_ips_include_vm_type_network_role', 'Ports'],
    ['test_fixed_ips_include_vm_type_network_role', 'Ports'],
    ['test_get_file_only_reference_local_files',
        'HEAT Files Support (get_file)'],
    ['test_heat_pairs_provided', 'Filenames'],
    ['test_heat_template_file_extension', 'Filenames'],
    ['test_heat_template_parameters_contain_required_fields',
     'Valid YAML and HEAT'],
    ['test_heat_template_structure', 'Valid YAML and HEAT'],
    ['test_heat_template_structure_contains_required_sections',
     'Valid YAML and HEAT'],
    ['test_heat_template_structure_sections_have_the_right_format',
     'Valid YAML and HEAT'],
    ['test_heat_templates_provided', 'Filenames'],
    ['test_network_format', 'Networks'],
    ['test_network_format', 'Ports'],
    ['test_network_format_use_get_param_or_get_resource', 'Networks'],
    ['test_network_format_use_get_param_or_get_resource', 'Ports'],
    ['test_no_unused_parameters_between_env_and_templates', 'Parameters'],
    ['test_nova_servers_correct_parameter_types',
        'Name, Flavor, and Image Assignments'],
    ['test_nova_servers_valid_resource_ids', 'Resources'],
    ['test_numeric_parameter', 'Parameters'],
    ['test_parameter_valid_keys', 'Valid YAML and HEAT'],
    ['test_parameter_valid_keys', 'Parameters'],
    ['test_parse_yaml', 'Valid YAML and HEAT'],
    ['test_port_resource_ids', 'Resources'],
    ['test_port_resource_ids', 'Ports'],
    ['test_referenced_and_defined_parameters_match', 'Parameters'],
    ['test_required_parameters_no_constraints', 'Required Metadata'],
    ['test_required_parameters_provided_in_env_file', 'Required Metadata'],
    ['test_required_parameters_provided_in_heat_template',
     'Required Metadata'],
    ['test_required_parameters_provided_in_heat_template',
     'Required Metadata'],
    ['test_servers_have_optional_metadata', 'Optional Metadata'],
    ['test_servers_have_required_metadata', 'Required Metadata'],
    ['test_servers_metadata_use_get_param', 'Required Metadata'],
    ['test_subnet_format', 'Subnet'],
    ['test_subnet_format', 'Ports'],
    ['test_subnet_format_use_get_param_or_get_resource', 'Subnet'],
    ['test_subnet_format_use_get_param_or_get_resource', 'Ports'],
    ['test_unique_name_resources', 'Unique Names for Resources'],
    ['test_unique_name_str_replace_use_req_params',
     'Unique Names for Resources'],
    ['test_unique_name_str_replace_use_req_params_in_tmpl',
        'Unique Names for Resources'],
    ['test_unique_resources_across_all_yaml_files', 'Resources'],
    ['test_unique_resources_across_yaml_file', 'Unique Names for Resources'],
    ['test_unique_resources_across_yaml_file', 'Resources'],
    ['test_valid_nesting', 'Filenames'],
    ['test_vm_type_assignments_on_nova_servers_only_use_get_param',
        'Name, Flavor, and Image Assignments'],
    ['test_vm_type_consistent_on_nova_servers',
        'Name, Flavor, and Image Assignments'],
    ['test_volume_format_outputs', 'Volumes'],
    ['test_volume_outputs_consumed', 'Volumes'],
    ['test_volume_resource_ids', 'Resources'],
    ['test_volume_resource_ids', 'Volumes'],
    ['test_volume_templates_contains_outputs', 'Volumes'],
    ['test_volume_templates_only_contains_cinder', 'Volumes'],
    ['test_volume_templates_outputs_match_resources', 'Volumes'],
]

glance_validation_tests = [
    ['test_image_scan_complete', 'Clam AV Scan'],
]

deployment_targets = [
    ['OpenStack', 'Kilo'],
    ['OpenStack', 'Liberty'],
    ['OpenStack', 'Mitaka'],
    ['OpenStack', 'Newton'],
    ['Other', 'No version available']
]

ecomps = [
    ['Unknown']
]

deployment_targets_sites = [
    "Site 1",
    "Site 2",
    "Site 3",
    "Site 4"
]


def execute_bootstrap_actions():
    create_roles()
    create_companies()
    create_deployment_targets()
    create_ecomp()
    create_deployment_targets_sites()

    # Non-default data:
    create_standard_users()
    create_el_users()
    create_admin_users()
    create_admin_ro_users()
    create_templates()
    create_validation_tests()


# TODO maybe enter this into migration scripts
def patch_migration_missing_fields():
    logger.info('Patching migration default fields')
    vf_ids = VF.objects.filter()
    if (vf_ids):
        vf_list = ThinVFModelSerializer(vf_ids, many=True).data
        for vf_data in vf_list:
                    # TODO remove into migration script
            if vf_data['ecomp_release'] is None:
                default_ecomp = ECOMPRelease.objects.get(name="Unknown")
                vfObj = VF.objects.get(uuid=vf_data['uuid'])
                vfObj.ecomp_release = default_ecomp
                vfObj.save()
            if vf_data['engagement']['reviewer'] is None:
                # @UndefinedVariable
                elRole = Role.objects.get(name=Roles.el.name)
                ids_list = []
                for user in vf_data['engagement']['engagement_team']:
                    ids_list.append(user['uuid'])
                # Fetch another random el Reviewer
                qs = IceUserProfile.objects.all().filter(role=elRole).filter(
                    uuid__in=ids_list)  # @UndefinedVariable
                if qs.count() > 0:
                    elUser = IceUserProfile.objects.get(uuid=qs[0].uuid)
                    engagementObj = Engagement.objects.get(
                        uuid=vf_data['engagement']['uuid'])
                    engagementObj.reviewer = elUser
                    engagementObj.save()

            # TODO remove into migration script
            if vf_data['engagement']['peer_reviewer'] is None:
                # @UndefinedVariable
                elRole = Role.objects.get(name=Roles.el.name)
                ids_list = []
                for user in vf_data['engagement']['engagement_team']:
                    ids_list.append(user['uuid'])
                # Fetch another random el to be a Peer Reviewer
                qs = IceUserProfile.objects.all().filter(role=elRole).exclude(
                    uuid__in=ids_list)  # @UndefinedVariable
                if qs.count() > 0:
                    randUser = qs[random.randint(0, qs.count() - 1)]
                    prUser = IceUserProfile.objects.get(uuid=randUser.uuid)
                    engagementObj = Engagement.objects.get(
                        uuid=vf_data['engagement']['uuid'])
                    engagementObj.peer_reviewer = prUser
                    engagementObj.save()


# TODO remove after check engine is connected
def populate_checklist_automation_value():
    logger.info('Populating existing checklist with decisions value')

    outerframes = inspect.getouterframes(inspect.currentframe())
    for outerframe in outerframes:
        if ('unittest' in str(outerframe)):
            logger.error(
                "Avoiding setting checklists in automation to be \
                review since this is a test run: " + logEncoding(outerframe))
            return

    checklists = Checklist.objects.filter(state='automation')
    first = True
    for checklist in checklists:
        checklist = Checklist.objects.get(uuid=checklist.uuid)
        if (first):
            checklist.state = 'review'
        else:
            checklist.state = 'peer_review'
        checklist.save()
    #    first = False
        decisions = ChecklistDecision.objects.filter(checklist=checklist)
        for decision in decisions:
            decision = ChecklistDecision.objects.get(uuid=decision.uuid)
            line_item = ChecklistLineItem.objects.get(
                uuid=decision.line_item_id)
            if line_item.line_type == 'auto':
                rand_decision_value = bool(random.getrandbits(1))
                if rand_decision_value:
                    decision.review_value = 'approved'
                else:
                    decision.review_value = 'denied'
            decision.save()


def create_templates():
    logger.info('Creating Checklist templates')
    for template in checklist_templates:
        created_template, created = ChecklistTemplate.objects.get_or_create(
            name=template['name'],
            defaults={
                'category': template['category'],
                'version': template['version'],
                'create_time': timezone.now()
            })
        for section in template['sections']:
            created_section = ChecklistSection.objects.get_or_create(
                name=section['name'],
                template_id=created_template.uuid,
                defaults={
                    'weight': section['weight'],
                    'description': section['description'],
                    'validation_instructions':
                    section['validation_instructions']

                })
            created_section = ChecklistSection.objects.get(
                name=section['name'], template_id=created_template.uuid)
            for line_item in section['line_items']:
                ChecklistLineItem.objects.get_or_create(
                    name=line_item['name'],
                    section_id=created_section.uuid,
                    template_id=created_template.uuid,
                    defaults={
                        'weight': line_item['weight'],
                        'description': line_item['description'],
                        'validation_instructions':
                        line_item['validation_instructions'],
                        'line_type': line_item['line_type'],
                        'section_id': created_section.uuid,
                    })


def create_validation_tests():
    logger.info('Creating Validation Tests')
    validation_tests = {
        'heat': heat_validation_tests,
        'glance': glance_validation_tests,
    }
    for category in validation_tests:
        template = ChecklistTemplate.objects.get(category=category)
        for test_name, line_item_name in validation_tests[category]:
            line_item = ChecklistLineItem.objects.get(
                name=line_item_name, template=template)
            if line_item:
                validation_test, status = ValidationTest.objects.get_or_create(
                    name=test_name)
                validation_test.line_items.add(line_item)


def create_roles():
    role_standard_user, created = Role.objects.get_or_create(
        name=Roles.standard_user.name)  # @UndefinedVariable
    Constants.role_standard_user = role_standard_user
    logger.info(
        'user role found or created : ' + logEncoding(role_standard_user))

    role_el, created = Role.objects.get_or_create(
        name=Roles.el.name)  # @UndefinedVariable
    Constants.role_el = role_el
    logger.info('user role found or created : ' + logEncoding(role_el))

    role_admin, created = Role.objects.get_or_create(
        name=Roles.admin.name)  # @UndefinedVariable
    Constants.role_admin = role_admin
    logger.info('user role found or created : ' + logEncoding(role_admin))

    role_admin_ro, created = Role.objects.get_or_create(
        name=Roles.admin_ro.name)  # @UndefinedVariable
    Constants.role_admin_ro = role_admin_ro
    logger.info('user role found or created : ' + logEncoding(role_admin_ro))


def create_companies():
    service_provider_company = None
    created = None
    try:
        service_provider_company, created = Vendor.objects.get_or_create(
            name=Constants.service_provider_company_name, public=True)
        Constants.service_provider_company = service_provider_company
        logger.info('The company was found or created : ' +
                    str(service_provider_company))
    except Exception as e:
        logger.error("bootstrap_actions - create_companies error:")
        logger.error(e)
        logger.error('The company could not be found or created : ' +
                     Constants.service_provider_company_name)

    for company in companies_not_public:
        try:
            company, created = Vendor.objects.get_or_create(
                name=company, public=False)  # @UndefinedVariable
            logger.info('The company was found or created : ' + str(company))
        except Exception as e:
            logger.error("bootstrap_actions - create_companies error:")
            logger.error(e)
            logger.error(
                'The company could not be found or created.' + str(company))

    for company in companies:
        try:
            company, created = Vendor.objects.get_or_create(
                name=company, public=True)  # @UndefinedVariable
            logger.info('The company was found or created : ' + str(company))
        except Exception as e:
            logger.error("bootstrap_actions - create_companies error:")
            logger.error(e)
            logger.error(
                'The company could not be found or created.' + str(company))

    try:
        company_other, created = Vendor.objects.get_or_create(
            name='Other', public=True, defaults={'public': True})
        logger.info('The company was found or created : ' + str(company_other))
    except Exception as e:
        logger.error("bootstrap_actions - create_deployment_targets error:")
        logger.error(e)
        logger.error('The company could not be found or created : Other')


"""expected: nothing , result: IceUserProfiles with el role creation"""


def create_standard_users():
    service_provider_company = Vendor.objects.get(
        name=Constants.service_provider_company_name)
    user_role = Role.objects.get(name="standard_user")
    user_list = dummy_users

    for user in user_list:
        try:
            user_object, created = CustomUser.objects.get_or_create(
                username=user[1], defaults={
                    'is_active': True, 'email': user[1],
                    'activation_token': uuid4(),
                    'activation_token_create_time': timezone.now()})
            user_object.set_password('iceusers')
            user_object.save()
            data = createUserTemplate(
                service_provider_company, user[0],
                user_role, user[2], True, None,
                True, user_object)
            standard_user, profile_created = \
                IceUserProfile.objects.update_or_create(
                    email=user_object.email, defaults=data)
            logger.info(
                'The Standard user was found or created: ' +
                str(standard_user.full_name))
        except Exception as e:
            logger.error("bootstrap_actions - create_el_users error:")
            logger.error(e)
            logger.error('The EL User could not be found or created.')


def create_el_users():
    service_provider_company = Vendor.objects.get(
        name=Constants.service_provider_company_name)
    el_role = Role.objects.get(name="el")
    el_list = el_dummy_users

    for user in el_list:
        try:
            user_object, created = CustomUser.objects.get_or_create(
                username=user[1], defaults={
                    'is_active': True, 'email': user[1],
                    'activation_token': uuid4(),
                    'activation_token_create_time': timezone.now()})
            user_object.set_password('iceusers')
            user_object.save()
            data = createUserTemplate(
                service_provider_company, user[0], el_role,
                user[2], True, None, True, user_object)
            el_user, profile_created = IceUserProfile.objects.update_or_create(
                email=user_object.email, defaults=data)
            logger.info(
                'The EL user was found or created: ' + str(el_user.full_name))
        except Exception as e:
            logger.error("bootstrap_actions - create_el_users error:")
            logger.error(e)
            logger.error('The EL User could not be found or created.')


def create_admin_users():
    service_provider_company = Vendor.objects.get(
        name=Constants.service_provider_company_name)
    admin_role = Role.objects.get(name=Roles.admin.name)  # @UndefinedVariable

    admin_list = admin_dummy_users

    for user in admin_list:
        try:
            user_object, created = CustomUser.objects.get_or_create(
                username=user[1], defaults={'is_active': True, 'email': user[
                    1], 'password': "iceusers", 'activation_token': uuid4(),
                    'activation_token_create_time': timezone.now()})
            user_object.set_password('iceusers')
            user_object.save()
            data = createUserTemplate(
                service_provider_company, user[0], admin_role, user[2],
                True, None, True, user_object)
            admin_user, profile_created = \
                IceUserProfile.objects.update_or_create(
                    email=user_object.email, defaults=data)
            logger.info(
                'The admin user was found or created: ' +
                str(admin_user.full_name))
        except Exception as e:
            logger.error("bootstrap_actions - create_admin_users error:")
            logger.error(e)
            logger.error('The admin user could not be found or created.')


def create_admin_ro_users():
    service_provider_company = Vendor.objects.get(
        name=Constants.service_provider_company_name)
    admin_ro_role = Role.objects.get(
        name=Roles.admin_ro.name)  # @UndefinedVariable

    admin_ro_list = admin_ro_dummy_users

    for user in admin_ro_list:
        try:
            user_object, created = CustomUser.objects.get_or_create(
                username=user[1],
                defaults={'is_active': True, 'email': user[
                    1], 'password': "iceusers", 'activation_token': uuid4(),
                    'activation_token_create_time': timezone.now()})
            user_object.set_password('iceusers')
            user_object.save()
            data = createUserTemplate(
                service_provider_company, user[0], admin_ro_role, user[2],
                True, None, True, user_object)
            admin_ro_user, profile_created = \
                IceUserProfile.objects.update_or_create(
                    email=user_object.email, defaults=data)
            logger.info(
                'The admin_ro user was found or created: ' +
                str(admin_ro_user.full_name))
        except Exception as e:
            logger.error("bootstrap_actions - create_admin_ro_users error:")
            logger.error(e)
            logger.error('The admin_ro user could not be found or created.')


"""expected: nothing , result: Deployment Target objects creation"""


def create_deployment_targets():
    for dt in deployment_targets:
        try:
            deployment_target, created = \
                DeploymentTarget.objects.get_or_create(
                    name=dt[0], version=dt[1], defaults={'version': dt[1]})
            logger.info(
                'Deployment Target found or created: ' +
                str(deployment_target))
        except Exception as e:
            logger.error(
                "bootstrap_actions - create_deployment_targets error:")
            logger.error(e)
            logger.error(
                'Deployment Target could not be found or created : ' + str(dt))


"""expected: nothing , result: ECOMP objects creation"""


def create_ecomp():
    for dt in ecomps:
        try:
            ecomp, created = ECOMPRelease.objects.get_or_create(
                name=dt[0])
            logger.info('ECOMP Release found or created: ' + str(ecomp))
        except Exception as e:
            logger.error("bootstrap_actions - create_ecomp error:")
            logger.error(e)
            logger.error(
                'ECOMP Release could not be found or created : ' + str(dt))


"""expected: nothing , result: creation of Deployment Target Sites objects"""


def create_deployment_targets_sites():
    for dt in deployment_targets_sites:
        try:
            deployment_target_site, created = \
                DeploymentTargetSite.objects.get_or_create(
                    name=dt)
            logger.info(
                'Deployment Target found or created: ' +
                str(deployment_target_site.name))
        except Exception as e:
            logger.error(
                "bootstrap_actions - create_deployment_targets_sites error:")
            logger.error(e)
            logger.error(
                'Deployment Target could not be found or created : ' + str(dt))
