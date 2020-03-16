import os
import sys
import time
import ConfigParser
import signal
from optparse import OptionParser
import logging.config
import logging
import transaction
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import datetime
import sys


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


def sigterm_kill_handler(signal_number, stack_frame):
    global loop
    loop = False
    log.info('Killing the process by signal %i' % signal_number)
    sys.exit(0)


def _lock_task(connection, models):
    select_query = """
(
    SELECT MIN(idtask) AS idtask, unique_key
     FROM task
    WHERE status='%s'
      AND pid IS NULL
      AND unique_key IS NOT NULL
 GROUP BY unique_key
    LIMIT 5
) UNION (
    SELECT idtask, unique_key
     FROM task
    WHERE status='%s'
      AND pid IS NULL
      AND unique_key IS NULL
    LIMIT 5
)
    """ % (
        models.TASK_STATUS_WAITING,
        models.TASK_STATUS_WAITING,
    )

    rows = connection.execute(select_query)
    for row in rows:
        idtask = row[0]
        unique_key = row[1]

        unique_key_extra_query = ''
        if unique_key:
            unique_key_extra_query = '''
          AND unique_key NOT IN (
            SELECT unique_key
              FROM task
             WHERE status = '%s'
               AND unique_key = '%s'
          )''' % (
                models.TASK_STATUS_IN_PROGRESS,
                unique_key)

        query = """
        UPDATE task
           SET pid = %i,
               status = '%s',
               lock_date = '%s'
        WHERE idtask = %i
          AND pid IS NULL
          %s""" % (
            os.getpid(),
            models.TASK_STATUS_IN_PROGRESS,
            datetime.datetime.utcnow(),
            idtask,
            unique_key_extra_query
        )

        updated_rows = connection.execute(text(query).execution_options(autocommit=True))
        if updated_rows.rowcount:
            return idtask


def lock_task(models):
    for i in range(5):
        # Make many tries since when we use sqlite the DB can be locked.
        try:
            connection = models.engine.connect()
            idtask = _lock_task(connection, models)
            connection.close()
            return idtask
        except OperationalError:
            pass
        time.sleep(10)

    return None


def _run(models):
    idtask = lock_task(models)
    if not idtask:
        return False

    task = models.Task.query.get(idtask)
    with transaction.manager:
        task.perform()
        models.DBSession.add(task)
    return True


def run(models, kill=False):
    if kill:
        signal.signal(signal.SIGTERM, sigterm_kill_handler)
    else:
        signal.signal(signal.SIGTERM, sigterm_handler)

    log.info('Process started')
    while loop:
        _run(models)
        time.sleep(1)
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
        items = dict(config.items('sqla_taskq')).keys()
    except ConfigParser.NoSectionError:
        log.info('No section sqla_taskq in %s' % filename)
        return None

    dic = {}
    if 'sqla_url' in items:
        dic['sqla_url'] = config.get('sqla_taskq', 'sqla_url')

    if 'kill' in items:
        dic['kill'] = config.getboolean('sqla_taskq', 'kill')
    else:
        dic['kill'] = False

    if 'timeout' in items:
        dic['timeout'] = config.getint('sqla_taskq', 'timeout')
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
        "-c", "--config-file", dest="config_filename",
        help="Filename containing the logging config",
        metavar="FILE")

    parser.add_option(
        "-k", "--kill", dest="kill",
        action="store_true",
        default=False,
        help="Don't wait the process in progress to be finished, kill it")

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
        os.environ['SQLA_TASKQ_SQLALCHEMY_URL'] = dic.get('sqla_url')

    return dic
