from sqlalchemy.orm import sessionmaker

import models

from orm import start_mappers, engine

start_mappers()
default_session = sessionmaker(engine)


class Repository:
    def __init__(self, session = default_session):
        self.session_factory = session

    def __enter__(self):
        self.session = self.session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def get(self, username: str) -> models.User | None:
        return (self.session.query(models.User)
                .filter(models.User.username == username)
                .first())

    def add(self, user: models.User):
        self.session.add(user)

    def commit(self):
        self.session.commit()
