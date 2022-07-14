from geoalchemy2 import Geometry
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Float,
    DateTime,
    UniqueConstraint,
    Table,
    create_engine,
)

from settings.settings import load_settings

SETTINGS = load_settings()

Base = declarative_base()
engine = create_engine(SETTINGS.conn_str)


image_objects = Table(
    "image_objects",
    Base.metadata,
    Column("image_id", ForeignKey("image.id")),
    Column("object_id", ForeignKey("object.id")),
    Column("match_accuracy", Float),
)


class Image(Base):
    __tablename__ = "image"

    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String)
    location = Column(Geometry("POINTZ"))
    timestamp = Column(DateTime)
    gps_accuracy = Column(Float)
    photo_direction = Column(Float)
    device_make = Column(String)
    device_model = Column(String)

    objects = relationship("Object", secondary=image_objects)

    unique_path = UniqueConstraint("path", name="unique_path")


class Object(Base):
    __tablename__ = "object"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_type = Column(String)
    object_name = Column(String)
    object_path = Column(String)


def main():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
