import time
import transaction
from daemon import runner
from taskq import models


class TaskDaemonRunner(runner.DaemonRunner):

    def _status(self):
        pid = self.pidfile.read_pid()
        message = []
        if pid:
            message += ['Daemon started with pid %s' % pid]
        else:
            message += ['Daemon not running']

        tasks = models.Task.query.filter_by(
            status=models.TASK_STATUS_WAITING).all()
        message += ['Number of waiting tasks: %s' % len(tasks)]
        runner.emit_message('\n'.join(message))

    action_funcs = {
        u'start': runner.DaemonRunner._start,
        u'stop': runner.DaemonRunner._stop,
        u'restart': runner.DaemonRunner._restart,
        u'status': _status,
    }


class TaskRunner():

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/tmp/task-runner.pid'
        self.pidfile_timeout = 5

    def run(self):
        while True:
            task = models.Task.query.filter_by(
                status=models.TASK_STATUS_WAITING).first()
            if not task:
                time.sleep(2)
                continue

            with transaction.manager:
                task.status = models.TASK_STATUS_IN_PROGRESS
                task.perform()
                task.status = models.TASK_STATUS_FINISHED
                models.DBSession.add(task)
            time.sleep(2)


def main():
    app = TaskRunner()
    daemon_runner = TaskDaemonRunner(app)
    daemon_runner.do_action()


if __name__ == '__main__':
    main()
