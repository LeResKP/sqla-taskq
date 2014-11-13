import os
import sys
import time
import ConfigParser
import signal
from optparse import OptionParser
import logging.config
import logging
import transaction

log = logging.getLogger(__name__)
# Can be overwrite by a config file
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
log.addHandler(ch)


loop = True


def sigterm_handler(signal_number, stack_frame):
    global loop
    loop = False
    log.info('Stopping the process by signal %i' % signal_number)


def run(models, sigterm=True):
    if sigterm:
        signal.signal(signal.SIGTERM, sigterm_handler)
    log.info('Process started')
    while loop:
        task = models.Task.query.filter_by(
            status=models.TASK_STATUS_WAITING).first()
        if not task:
            time.sleep(10)
            continue

        with transaction.manager:
            task.status = models.TASK_STATUS_IN_PROGRESS
            models.DBSession.add(task)

        with transaction.manager:
            models.DBSession.add(task)
            task.perform()
            models.DBSession.add(task)
        time.sleep(2)
    log.info('Process stopped')


def parse_config_file(filename):
    config = ConfigParser.ConfigParser()
    config.read(filename)

    try:
        config.items('loggers')
        # We have at least the loggers section so we can set logging config
        logging.config.fileConfig(filename)
    except ConfigParser.NoSectionError:
        log.info('No section loggers in %s' % filename)

    try:
        items = dict(config.items('taskq')).keys()
    except ConfigParser.NoSectionError:
        log.info('No section taskq in %s' % filename)
        return None

    dic = {}
    if 'sqla_url' in items:
        dic['sqla_url'] = config.get('taskq', 'sqla_url')

    if 'sigterm' in items:
        dic['sigterm'] = config.getboolean('taskq', 'sigterm')
    else:
        dic['sigterm'] = True

    if 'timeout' in items:
        dic['timeout'] = config.getint('taskq', 'timeout')
    else:
        dic['timeout'] = 60

    return dic


def parse_options(argv=sys.argv, parse_timeout=False):
    parser = OptionParser()
    parser.add_option(
        "-u", "--url", dest="sqla_url",
        help="SqlAlchemy url to access the DB",
        metavar="URL")
    parser.add_option(
        "-c", dest="config_filename",
        help="Filename containing the logging config",
        metavar="FILE")

    parser.add_option(
        "-s", "--nosigterm", dest="sigterm",
        action="store_false",
        default=True,
        help="Don't wait the process in progress to be finished")

    if parse_timeout:
        parser.add_option(
            "-t", "--timeout", dest="timeout",
            help=("The pid timeout of the process in second. "
                  "By default it waits 60 seconds the process to finish"),
            type="int", default=60,
            metavar="time")

    (options, args) = parser.parse_args(argv)

    dic = None
    if options.config_filename:
        dic = parse_config_file(options.config_filename)

    if dic is None:
        dic = vars(options)

    if dic.get('sqla_url'):
        os.environ['TASKQ_SQLALCHEMY_URL'] = dic.get('sqla_url')

    return dic
