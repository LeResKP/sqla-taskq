from taskq import models


if __name__ == '__main__':
    models.Base.metadata.create_all(models.engine)
