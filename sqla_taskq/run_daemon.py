from daemon import runner
from sqla_taskq import command


class TaskDaemonRunner(runner.DaemonRunner):

    def _status(self):
        pid = self.pidfile.read_pid()
        message = []
        if pid:
            message += ['Daemon started with pid %s' % pid]
        else:
            message += ['Daemon not running']

        tasks = self.app.models.Task.query.filter_by(
            status=self.app.models.TASK_STATUS_WAITING).all()
        message += ['Number of waiting tasks: %s' % len(tasks)]
        runner.emit_message('\n'.join(message))

    action_funcs = {
        u'start': runner.DaemonRunner._start,
        u'stop': runner.DaemonRunner._stop,
        u'restart': runner.DaemonRunner._restart,
        u'status': _status,
    }


class TaskRunner():

    def __init__(self, models, timeout, kill):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/tmp/task-runner.pid'
        self.pidfile_timeout = timeout
        self.models = models
        self.kill = kill

    def run(self):
        command.run(self.models, self.kill)


def main():
    dic = command.parse_options(parse_timeout=True)
    # Import models here since we can have set the sqlalchemy url to use in the
    # environment
    from sqla_taskq import models
    timeout = dic['timeout']
    kill = dic['kill']
    app = TaskRunner(models, timeout, kill)
    daemon_runner = TaskDaemonRunner(app)
    daemon_runner.do_action()


if __name__ == '__main__':
    main()
