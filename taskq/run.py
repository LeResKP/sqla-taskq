import time
import transaction
from taskq import models
from daemon import runner


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
    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.do_action()


if __name__ == '__main__':
    main()
