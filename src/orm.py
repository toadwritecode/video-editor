from sqlalchemy import (Table, MetaData,
                        create_engine, Column,
                        Integer, String,
                        ForeignKey, UUID, Text)
from sqlalchemy.orm import registry, relationship
from conf.config import BASE_DIR
import models

db_path = BASE_DIR / "db/new.db"

engine = create_engine(f'sqlite:///{db_path}', echo=True)
metadata = MetaData()

mapper_registry = registry(metadata=metadata)

users = Table("users",
              metadata,
              Column("id", Integer, primary_key=True, autoincrement=True),
              Column("uuid", String(50), nullable=False),
              Column("hashed_password", String(255), nullable=False),
              Column("username", String(255), nullable=False),
              Column("email", String(255)),
              Column("full_name", String(100)),
              Column("role", String(100))
              )

refresh_tokens = Table("refresh_tokens",
                       metadata,
                       Column("id", Integer, primary_key=True, autoincrement=True),
                       Column("refresh_token", String(255)),
                       Column("user_id", ForeignKey("users.uuid", ondelete="CASCADE"), unique=True)
                       )

files = Table("files",
              metadata,
              Column("id", Integer, primary_key=True, autoincrement=True),
              Column("uuid", UUID),
              Column("path", String(255)),
              Column("name", String(255)),
              Column("extracted_text", Text),
              Column("user_id", ForeignKey("users.id"))
              )

tags = Table("singing_mistakes",
             metadata,
             Column("id", Integer, primary_key=True, autoincrement=True),
             Column("name", String(255)))

vocal_lesson_singing_mistakes = Table("vocal_lesson_singing_mistakes",
                                      metadata,
                                      Column("id", Integer, primary_key=True, autoincrement=True),
                                      Column("file_id", ForeignKey("files.id")),
                                      Column("mistake_id", ForeignKey("singing_mistakes.id")))


def start_mappers():
    mapper_registry.metadata.create_all(engine)
    # tags_mapper = mapper_registry.map_imperatively(models.Tag, tags)
    files_mapper = mapper_registry.map_imperatively(models.File, files,
                                                    # properties={"tags": relationship(tags_mapper)}
                                                    )
    mapper_registry.map_imperatively(
        models.User,
        users,
        properties={"files": relationship(files_mapper)}
    )
    # mapper_registry.map_imperatively(models.File,
    #                                  )


if __name__ == '__main__':
    start_mappers()
