from sqla_taskq import command


def main():
    dic = command.parse_options()
    from sqla_taskq import models
    command.run(models, kill=dic['kill'])

if __name__ == '__main__':
    main()
