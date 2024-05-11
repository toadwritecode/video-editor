

from sqlalchemy import (Table, MetaData,
                        create_engine, Column,
                        Integer, String,
                        ForeignKey, UUID)
from sqlalchemy.orm import registry, relationship
from conf.config import BASE_DIR
import models
from models import User

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
              Column("user_id", ForeignKey("users.id"))
              )

tags = Table("tags",
             metadata,
             Column("id", Integer, primary_key=True, autoincrement=True),
             Column("name", String(255)))

video_tags = Table("video_tags",
                   metadata,
                   Column("id", Integer, primary_key=True, autoincrement=True),
                   Column("file_id", ForeignKey("files.id")),
                   Column("tag_id", ForeignKey("tags.id")))


def start_mappers():
    mapper_registry.metadata.create_all(engine)
    files_mapper = mapper_registry.map_imperatively(models.File, files)
    # tags_mapper = mapper_registry.map_imperatively(Tag, tags)
    # tokens_mapper = mapper_registry.map_imperatively(RefreshToken, refresh_tokens)
    mapper_registry.map_imperatively(
        User,
        users,
        properties={"files": relationship(files_mapper)}
    )


if __name__ == '__main__':
    start_mappers()