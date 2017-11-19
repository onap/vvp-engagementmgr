from celery import Celery
from django.conf import settings
from engagementmanager.models import CheckListState

celery_app = Celery(
    broker='redis://redis',
    backend='redis://redis',
    )

# Celery signatures allow us to invoke the imagescanner celery task without
# importing or depending upon imagescanner's code here. (Because doing so would
# make all of imagescanner's dependencies get added to this Django project.)
#
# FIXME for some reason, requests submitted in this way do not show their
# arguments in the simple frontend's "Executing" and "Pending" lists. It
# appears only as "()"
_request_scan = celery_app.signature(
    'imagescanner.tasks.request_scan',
    queue='scans',
    ignore_result=True)


def request_scan(vf, checklist):
    """Issue a request (using Celery and Redis) for the imagescanner to run.

    This function issues the request asynchronously and returns quickly.

    vf:
        the VF corresponding to the image to be scanned. we use this to
        determine the radosgw bucket name to search for images and the jenkins
        job name to trigger with the image scan results.

    checklist:
        the checklist to be updated with the results of the scan.
    """
    # we can't necessarily look this up from the vf because there might be two
    # available at the time this method runs (the new one, and the old one
    # which will get changed to archive state)

    return _request_scan.delay(
        source="https://%s/%s_%s/" % (
            settings.AWS_S3_HOST, vf.engagement.engagement_manual_id, vf.name),
        path='',
        recipients=[],
        # this suffix should match the one in
        # validationmanager.em_integration.vm_api.get_jenkins_job_config
        jenkins_job_name=vf.jenkins_job_name() + '_scanner',
        checklist_uuid=checklist.uuid,
        )
