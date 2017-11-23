#!/usr/bin/env python3
import os
import json
import connexion
import logging
from flask import redirect, jsonify
from datetime import datetime
from flask_script import Manager
from jobs.scheduler import Scheduler
import jobs.defaults as defaults
from myapp.configuration import init

logger = logging.getLogger(__name__)


class SafeJSONEncoder(json.JSONEncoder):
    """ Convert objects to JSON, safely """
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        try:
            return json.JSONEncoder.default(self, o)
        except TypeError:
            return repr(o)


def init_logging():
    """ Initialize application logging """
    # Initialize flask logging
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    handler.setFormatter(formatter)
    # Use flask App instead of Connexion's one
    application.logger.addHandler(handler)
    # API logger
    logger.setLevel(logging.DEBUG)
    # lib logger
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    liblog = logging.getLogger('jobs')
    liblog.setLevel(logging.DEBUG)
    liblog.addHandler(handler)


app = connexion.App(__name__)
application = app.app
init_logging()
app.add_api(defaults.SWAGGER_YAML_PATH)
# Expose for uWSGI
application.json_encoder = SafeJSONEncoder
manager = Manager(application)


logger.debug("Initializing Selinon")
init()
logger.debug("Selinon initialized successfully")


@app.route('/')
def base_url():
    # Be nice with user access
    return redirect('api/v1/ui')


@app.route('/api/v1')
def api_v1():
    paths = []

    for rule in application.url_map.iter_rules():
        rule = str(rule)
        if rule.startswith('/api/v1'):
            paths.append(rule)

    return jsonify({'paths': paths})


@manager.command
def initjobs():
    """ initialize default jobs """""
    logger.debug("Initializing default jobs")
    Scheduler.register_default_jobs(defaults.DEFAULT_JOB_DIR)
    logger.debug("Default jobs initialized")


@manager.command
def runserver():
    """ run job service server """""
    #
    # The Flasks's runserver command was overwritten because we are using connexion.
    #
    # Make sure that you do not run the application with multiple processes since we would
    # have multiple scheduler instances. If you would like to do so, just create one scheduler
    # that would serve jobs and per-process scheduler would be in paused mode
    # just for creating/listing jobs.
    app.run(
        port=os.environ.get('JOB_SERVICE_PORT', defaults.DEFAULT_SERVICE_PORT),
        server='flask',
        debug=True,
        use_reloader=True,
        threaded=True,
        json_encoder=SafeJSONEncoder,
        processes=1
    )


if __name__ == '__main__':
    manager.run()
