from taskq import models


def main():
    models.Base.metadata.create_all(models.engine)


if __name__ == '__main__':
    main()
