#!/usr/bin/env python3

import logging
from apscheduler.schedulers.base import STATE_STOPPED, JobLookupError

import jobs.handlers as handlers
from jobs.utils import (get_service_state_str, get_job_state_str, job2raw_dict, is_failed_job)
from jobs.scheduler import uses_scheduler, ScheduleJobError, Scheduler

logger = logging.getLogger(__name__)


@uses_scheduler
def get_service_state(scheduler):
    return {"state": get_service_state_str(scheduler)}, 200


@uses_scheduler
def put_service_state(scheduler, state):
    if scheduler.state == STATE_STOPPED:
        scheduler.start(paused=(state == 'paused'))

    if state == 'paused':
        scheduler.pause()
    elif state == 'running':
        scheduler.resume()
    else:
        return {"error": "Unknown status provided: '%s'" % state}, 400

    return {"state": get_service_state_str(scheduler)}, 200


@uses_scheduler
def delete_jobs(scheduler, job_id):
    try:
        scheduler.remove_job(job_id)
    except JobLookupError:
        return {"error": "No such job with id '%s'" % job_id}, 410
    return {'removed': [job_id]}, 200


@uses_scheduler
def delete_clean_failed(scheduler):
    ret = []
    for job in scheduler.get_jobs():
        if is_failed_job(job):
            ret.append(job.id)
            job.remove()
    return {'removed': ret}, 200


@uses_scheduler
def put_jobs(scheduler, job_id, state):
    try:
        if state == "paused":
            job = scheduler.pause_job(job_id)
        elif state == "running":
            job = scheduler.resume_job(job_id)
        else:
            return {"error": "Unknown state '%s'" % state}, 400
    except JobLookupError:
        return {"error": "No such job with id '%s'" % job_id}, 404

    return {"job_id": job.id, "state": get_job_state_str(job)}, 200


@uses_scheduler
def get_jobs(scheduler, job_type=None):
    jobs = scheduler.get_jobs()

    job_types = ('all', 'failed', 'user', None)
    if job_type not in job_types:
        return {"error": "Unknown job type filtering supplied: '%s', should be one of %s" %
                (job_type, job_types)}, 400

    job_list = []
    job_type = job_type or 'all'
    for job in jobs:
        if job_type == 'failed' and is_failed_job(job):
                job_list.append(job2raw_dict(job))
        if job_type == 'user' and not is_failed_job(job):
            job_list.append(job2raw_dict(job))
        if job_type == 'all':
            job_list.append(job2raw_dict(job))

    return {"jobs": job_list, "jobs_count": len(job_list)}, 200


def get_readiness():
    return {}, 200


@uses_scheduler
def get_liveness(scheduler):
    # Ensure the scheduler is alive
    logger.warning("Liveness probe - trying retrieve stored jobs from database using scheduler")
    # Ensure that we are able to publish messages
    logger.warning("Liveness probe - trying to schedule the livenessFlow")
    handlers.FlowScheduling(job_id=None).execute('livenessFlow', flow_arguments=[None])
    logger.warning("Liveness probe - finished")
    return {}, 200


def post_schedule_job(scheduler, handler_name, **kwargs):
    # No need to add @requires_auth for this one, assuming handler specific
    # POST endpoints take care of it
    try:
        # Translate 'kwargs' in POST to handler key-value arguments passing, if needed
        kwargs.update(kwargs.pop('kwargs', {}))
        job = Scheduler.schedule_job(scheduler, handler_name, **kwargs)
        return {"job": job2raw_dict(job)}, 201
    except ScheduleJobError as exc:
        return {"error": str(exc)}, 400


@uses_scheduler
def post_flow_scheduling(scheduler, **kwargs):
    return post_schedule_job(scheduler, handlers.FlowScheduling.__name__, **kwargs)


@uses_scheduler
def post_selective_flow_scheduling(scheduler, **kwargs):
    return post_schedule_job(scheduler, handlers.SelectiveFlowScheduling.__name__, **kwargs)

#@requires_auth
#def post_show_select_query(filter_definition):
#    try:
#        query = BaseHandler(job_id=None).construct_select_query(filter_definition.pop(
#            BaseHandler.DEFAULT_FILTER_KEY))
#    except Exception as exc:
#        logger.exception(str(exc))
#        return {"error": str(exc), "traceback": traceback.format_exc()}, 400
#    return {"query": query}, 200
#
#
#@requires_auth
#def post_expand_filter_query(filter_definition):
#    try:
#        matched = BaseHandler(job_id=None).expand_filter_query(filter_definition)
#    except Exception as exc:
#        logger.exception(str(exc))
#        return {"error": str(exc), "traceback": traceback.format_exc()}, 400
#    return {"matched": matched}, 200
#
#
#@requires_auth
#def get_analyses_report(ecosystem, from_date=None, to_date=None):
#    if from_date:
#        try:
#            from_date = parse_datetime(from_date)
#        except Exception as exc:
#            return {"error": "Cannot parse string format for 'from_date': %s" % str(exc)}, 400
#
#    if to_date:
#        try:
#            to_date = parse_datetime(to_date)
#        except Exception as exc:
#            return {"error": "Cannot parse string format for 'to_date': %s" % str(exc)}, 400
#
#    return construct_analyses_report(ecosystem, from_date, to_date), 200
#
#
#@requires_auth
#def get_queue_attributes():
#    try:
#        report = construct_queue_attributes()
#    except Exception as exc:
#        logger.exception("Failed to get queue attributes")
#        return {"error": str(exc)}, 500
#    return report, 200
#
#
#@requires_auth
#def get_gh_tokens_rate_limits():
#    response = {'tokens': []}
#    for token in configuration.GITHUB_ACCESS_TOKENS:
#        r = requests.get('https://api.github.com/rate_limit', params={'access_token': token})
#        limits = r.json()
#        limits['token'] = '{prefix}...'.format(prefix=token[:4])
#        response['tokens'].append(limits)
#
#    return response, 200
#
##
## Handler specific POST requests
##
#
#
#
#
#@requires_auth
#
#
#@requires_auth
#@uses_scheduler
#def post_analyses(scheduler, **kwargs):
#    try:
#        handlers.base.AnalysesBaseHandler.check_arguments(**kwargs)
#    except Exception as exc:
#        return {"error": str(exc)}, 400
#
#    handler_name = handlers.base.AnalysesBaseHandler.ecosystem2handler_name(kwargs['ecosystem'])
#    return post_schedule_job(scheduler, handler_name, **kwargs)
#
#
#@requires_auth
#@uses_scheduler
#def github_most_starred(scheduler, **kwargs):
#    try:
#        handlers.base.AnalysesBaseHandler.check_arguments(**kwargs)
#    except Exception as exc:
#        return {"error": str(exc)}, 400
#
#    return post_schedule_job(scheduler, handlers.GitHubMostStarred.__name__, **kwargs)
#
#
#@requires_auth
#@uses_scheduler
#def github_manifests(scheduler, **kwargs):
#    return post_schedule_job(scheduler, handlers.GitHubManifests.__name__, **kwargs)
#
#
#@requires_auth
#@uses_scheduler
#def aggregate_github_manifest_pkgs(scheduler, **kwargs):
#    return post_schedule_job(scheduler, handlers.AggregateGitHubManifestPackages.__name__, **kwargs)
#
#
#@requires_auth
#@uses_scheduler
#def post_clean_postgres(scheduler, **kwargs):
#    return post_schedule_job(scheduler, handlers.CleanPostgres.__name__, **kwargs)
#
#
#@requires_auth
#@uses_scheduler
#def post_sync_to_graph(scheduler, **kwargs):
#    return post_schedule_job(scheduler, handlers.SyncToGraph.__name__, **kwargs)
#
#
#@requires_auth
#@uses_scheduler
#def post_aggregate_topics(scheduler, **kwargs):
#    return post_schedule_job(scheduler, handlers.AggregateTopics.__name__, **kwargs)
#
#
#@requires_auth
#def post_queue_purge(queues):
#    try:
#        report = purge_queues(queues.split(','))
#    except Exception as exc:
#        return {'error': str(exc)}, 500
#    return report, 200
#
#
#@requires_auth
#@uses_scheduler
#def post_maven_releases(scheduler, **kwargs):
#    return post_schedule_job(scheduler, handlers.MavenReleasesAnalyses.__name__, **kwargs)
#
#
#@requires_auth
#def get_maven_releases():
#    s3 = StoragePool.get_connected_storage('S3MavenIndex')
#    return {'last_offset': s3.get_last_offset()}, 200
#
#
#@requires_auth
#def put_maven_releases(offset):
#    s3 = StoragePool.get_connected_storage('S3MavenIndex')
#    s3.set_last_offset(offset)
#    return {'last_offset': s3.get_last_offset()}, 201
