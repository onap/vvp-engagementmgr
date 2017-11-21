import logging

from django.core.exceptions import ObjectDoesNotExist

from engagementmanager.bus.handlers.service_bus_base_handler \
    import ServiceBusBaseHandler
from engagementmanager.slack_client.api import SlackClient
from engagementmanager.models import VF, Checklist, IceUserProfile
from engagementmanager.utils.constants import CheckListState
from validationmanager.rados.rgwa_client_factory import RGWAClientFactory
from datetime import datetime, timedelta
from engagementmanager.service.checklist_state_service import set_state
from engagementmanager.utils.request_data_mgr import request_data_mgr

logger = logging.getLogger('ice.logger')


class ImagePushedHandler(ServiceBusBaseHandler):
    def handle_message(self, bus_message):
        logger.debug("New hourly scheduled message arrived,"
                     " Will check if there are new images and trigger the "
                     "checklist scan in accordance.")

        rgwa = RGWAClientFactory.admin()
        start_date = datetime.today() - timedelta(hours=1)
        last_hour_uasge = rgwa.get_usage(show_entries=True,
                                         start=start_date
                                         .strftime('%Y-%m-%d %H:%M:%S'))

        if last_hour_uasge is not None and 'entries' in last_hour_uasge:
            for entry in last_hour_uasge['entries']:
                for bucket in entry['buckets']:
                    if "_" not in bucket["bucket"]:
                        # we must skip "cms-media", "cms-static", "em-media",
                        # and "em-static", as well as any bucket not created
                        # for images, for now this is sufficient but FIXME
                        # could be more robust.
                        continue
                    if any(category['category'] == 'put_obj' for category
                           in bucket['categories']):
                        logger.debug("Found image which updated at the last "
                                     "hour -> will run checklist scan"
                                     "for validation.")
                        bucket_name_combinations = str(bucket['bucket'])\
                            .split('_')
                        eng_manual_id = bucket_name_combinations[0]
                        vf_name = bucket_name_combinations[1]

                        vf = VF.objects.get(
                            name=vf_name,
                            engagement__engagement_manual_id=eng_manual_id)
                        self.validate_vf_exists(vf)
                        self.notify_slack_users(vf, bucket['bucket'])
                        self.set_checklist_states(vf)

    def validate_vf_exists(self, vf):
        if vf is None:
            msg = "Couldn't fetch any VF"
            logger.error(msg)
            raise ObjectDoesNotExist(msg)

    def notify_slack_users(self, vf, bucket_name):
        slack_client = SlackClient()
        slack_client.send_notifications_bucket_image_update(
            vf.engagement.engagement_manual_id, vf.name,
            vf.engagement.reviewer, vf.engagement.peer_reviewer, bucket_name)

    def set_checklist_states(self, vf):
        checklists = (Checklist.objects
                      .filter(engagement=vf.engagement)
                      .exclude(state=CheckListState.archive.name)
                      .exclude(state=CheckListState.closed.name))

        for checklist in checklists:
            # FIXME Even though there is probably no associated request for
            # this periodically-triggered task, set_state will crash if the
            # request_data_mgr.get_user() returns None. So fake it.
            request_data_mgr.set_user(
                IceUserProfile.objects.filter(role__name='admin').first())
            data = set_state(decline=True,
                             checklist_uuid=checklist.uuid,
                             isMoveToAutomation=True,
                             description="This change was triggered by an "
                                         "update to the engagement rgwa bucket"
                                         ".")

            logger.debug("set_state returned (%r)" % data)
