import json
from pathlib import Path

from loguru import logger
from geoalchemy2 import Geometry
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
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

from gisterical.settings.settings import load_settings

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
    phash = Column(String)
    colorhash = Column(String)

    objects = relationship("Object", secondary=image_objects)

    unique_path = UniqueConstraint("path", name="unique_path")


class Object(Base):
    __tablename__ = "object"

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_type = Column(String)
    object_name = Column(String)
    object_path = Column(String)


class Country(Base):
    __tablename__ = "country"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    iso_code = Column(String)
    geometry = Column(Geometry)


class City(Base):
    __tablename__ = "city"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    country = Column(String)
    location = Column(Geometry("POINT"))
    population = Column(Integer)


def populate_cities(session: sessionmaker):
    logger.info("Adding coordinates for world cities.")
    cities = Path(__file__).parent.parent / SETTINGS.cities_data
    with open(cities, "r") as f:
        with session.begin() as sess:
            for idx, row in enumerate(f.readlines()):
                r = row.split(",")
                
                try:
                    city = r[0].replace('"', "")
                except (TypeError, ValueError):
                    city = None
                    
                try:
                    country = r[4].replace('"', "")
                except (TypeError, ValueError):
                    country = None
                
                try:
                    pop = int(r[9].replace('"', ""))
                except (TypeError, ValueError):
                    pop = None

                try:
                    lat = float(r[2].replace('"', ""))
                    lon = float(r[3].replace('"', ""))
                    loc = f"POINT({lon} {lat})"
                except (TypeError, ValueError):
                    loc = None

                if idx >= 1:
                    new_city = City(
                        name=city,
                        country=country,
                        location=loc,
                        population=pop,
                    )
                    sess.add(new_city)
                    sess.flush()
            sess.commit()


def populate_countries(session: sessionmaker):
    logger.info("Adding country boundaries.")
    path = Path(__file__).parent.parent / SETTINGS.countries_data
    with open(path) as f:
        cnt = json.load(f)
    ft = cnt["features"]
    with session.begin() as sess:
        for f in ft:
            new_cnt = Country(
                name=f["properties"]["ADMIN"],
                iso_code=f["properties"]["ISO_A3"],
                geometry=json.dumps(f["geometry"]),
            )
            sess.add(new_cnt)
        sess.commit()


def create_schema():
    session = sessionmaker(engine)
    Base.metadata.create_all(engine)
    populate_cities(session)
    populate_countries(session)


if __name__ == "__main__":
    create_schema()
