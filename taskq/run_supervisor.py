from taskq import command


def main():
    dic = command.parse_options()
    from taskq import models
    command.run(models, sigterm=dic['sigterm'])

if __name__ == '__main__':
    main()
