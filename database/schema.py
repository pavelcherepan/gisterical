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

Base = declarative_base()
engine = create_engine("postgresql+psycopg2://gis:gis@localhost/photo")


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
    location = Column(Geometry("POINT"))
    timestamp = Column(DateTime)
    gps_accuracy = Column(Float)
    photo_direction = Column(String)
    device_make = Column(String)
    device_model = Column(String)

    objects = relationship("Object", secondary=image_objects)

    unique_path = UniqueConstraint("path", name="unique_path")


class Object(Base):
    __tablename__ = "object"

    id = Column(Integer, primary_key=True, autoincrement=True)
    saved_data = Column(String)


def main():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
