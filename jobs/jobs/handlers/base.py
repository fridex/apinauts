#!/usr/bin/env python3

import logging
from selinon import run_flow
from selinon import run_flow_selective
from myapp.configuration import init


class BaseHandler(object):
    """ Base handler class for user defined handlers"""
    _initialized_celery = False

    def __init__(self, job_id):
        self.log = logging.getLogger(__name__)
        self.job_id = job_id
        # initialize always as the assumption is that we will use it
        self._init_celery()

    def _init_celery(self):
        """ Initialize celery and connect to the broker """
        if not self._initialized_celery:
            init(with_result_backend=False)
            self._initialized_celery = True

    def run_selinon_flow(self, flow_name, node_args):
        """Connect to broker, if not connected, and run Selinon flow

        :param flow_name: flow that should be run
        :param node_args: flow arguments
        """
        self.log.debug("Scheduling Selinon flow '%s' with node_args: '%s', job '%s'",
                       flow_name, node_args, self.job_id)

        if self.job_id:
            node_args['job_id'] = self.job_id

        return run_flow(flow_name, node_args)

    def run_selinon_flow_selective(self, flow_name, task_names, node_args, follow_subflows,
                                   run_subsequent):
        """Connect to broker, if not connected, and run Selinon selective flow

        :param flow_name: flow that should be run
        :param task_names: a list of tasks that should be executed
        :param node_args: flow arguments
        :param follow_subflows: follow subflows when resolving tasks to be executed
        :param run_subsequent: run tasks that follow after desired tasks stated in task_names
        """
        self.log.debug("Scheduling selective Selinon flow '%s' with tasks '%s' and node_args: "
                       "'%s', job '%s'", flow_name, task_names, node_args, self.job_id)
        return run_flow_selective(flow_name, task_names, node_args, follow_subflows,
                                  run_subsequent)

    def execute(self, **kwargs):
        """ User defined job handler implementation """
        raise NotImplementedError()
