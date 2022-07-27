import datetime as dt
from pathlib import Path
from shutil import copyfile

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from gisterical.database.schema import Image, Country, City
from gisterical.core.image_metadata import PhotoData
from gisterical.settings.settings import load_settings
from gisterical.util.file_meta import FileMeta


SETTINGS = load_settings()


class DbApi:
    conn_str = SETTINGS.conn_str
    engine: Engine = create_engine(conn_str)
    session = sessionmaker(engine)

    def add_photo_to_db(self, data: list[PhotoData]):
        logger.debug(f"Adding {len(data)} files to the database.")
        with self.session.begin() as sess:
            for d in data:
                if -999 not in {d.latitude, d.longitude, d.altitude}:
                    loc = f"POINTZ({d.longitude} {d.latitude} {d.altitude})"
                else:
                    loc = None
                acc = d.gps_accuracy if d.gps_accuracy != -999 else None
                direction = d.photo_direction if d.photo_direction != -999 else None

                new_result = Image(
                    path=d.path,
                    location=loc,
                    timestamp=d.timestamp,
                    gps_accuracy=acc,
                    photo_direction=direction,
                    device_make=d.camera_make,
                    device_model=d.camera_model,
                    phash=d.phash,
                    colorhash=d.colorhash,
                )

                sess.add(new_result)
                sess.flush()
            sess.commit()
        logger.debug("Successfully added!")

    def select_files_and_output(
        self,
        location: tuple[float, ...] = (0, 0, 0),
        distance_km: int | float = 1e10,
        start_date: dt.datetime = dt.datetime(1900, 1, 1),
        end_date: dt.datetime = dt.datetime(9999, 1, 1),
        target_folder: str | Path = "/home/pavel/Pictures/temp",
    ):
        logger.info(
            f"Searching for images within {distance_km} kilometers "
            f"from coordinates {location} between {start_date} "
            f"and {end_date}."
        )
        p = Path(target_folder)
        if not p.is_dir():
            p.mkdir()

        with self.session.begin() as sess:
            q = (
                sess.query(Image.path)
                .filter(
                    Image.location.ST_DistanceSphere(
                        f"POINTZ({location[0]} {location[1]} {location[2]})"
                    )
                    <= distance_km * 1000
                )
                .filter(Image.timestamp >= start_date)
                .filter(Image.timestamp <= end_date)
            )

            res: list[str] = [i[0] for i in q.all()]
            logger.info(f"{len(res)} files found. Copying the files to {target_folder}.")

        for pth in res:
            fname = Path(pth).name
            copyfile(str(pth), str(p / fname))
        logger.info("Success!")
        
    def get_photos_by_city(self, distance_km: int):
        logger.info('Querying images with nearest city data.')        
        with self.session.begin() as sess:
            q = sess.query(Image.path, Image.timestamp, City.name).distinct(Image.path).\
                join(City, Image.location.ST_DWithin(City.location, distance_km * 1000, True)).\
                    order_by(Image.path, City.population.desc()).all()
        return [FileMeta(path=Path(i[0]), date=i[1], city=i[2]) for i in q]
    
    def get_photo_path_date(self):
        logger.info("Querying photo datetime information")
        with self.session.begin() as sess:
            q = sess.query(Image.path, Image.timestamp).all()
            return [FileMeta(path=Path(i[0]), date=i[1]) for i in q]        
        
    def get_photo_city_country(self, distance_km: int):
        logger.info('Querying images with nearest city and country information.')
        with self.session.begin() as sess:
            q = sess.query(Image.path, Image.timestamp, Country.name, City.name).distinct(Image.path).\
                join(City, Image.location.ST_DWithin(City.location, distance_km * 1000, True)).\
                join(Country, Country.geometry.ST_Contains(Image.location)).\
                    order_by(Image.path, City.population.desc()).all()    
        return [FileMeta(path=Path(i[0]), date=i[1], country=i[2], city=i[3]) for i in q]
                    
    def get_photo_country(self):
        logger.info('Querying images with country information.')
        with self.session.begin() as sess:
            q = sess.query(Image.path, Image.timestamp, Country.name).\
                join(Country, Country.geometry.ST_Contains(Image.location)).all()
        return [FileMeta(path=Path(i[0]), date=i[1], country=i[2]) for i in q]   
    
    def get_photo_no_location(self):
        with self.session.begin() as sess:
            q = sess.query(Image.path, Image.timestamp).\
                filter(Image.location==None).all()
        return [FileMeta(path=Path(i[0]), date=i[1], country="Uknown", city="Unknown") for i in q]
    
    def find_photos_by_city_name(self, distance_km: int, name: str) -> list[Path]:
        with self.session.begin() as sess:
            q: list[tuple[str]] = sess.query(Image.path)\
                .join(City, Image.location.ST_DWithin(City.location, distance_km * 1000, True))\
                    .filter(City.name == name).all()
        return [Path(i[0]) for i in q]
    
    def find_photos_by_country_name(self, name: str) -> list[Path]:
        with self.session.begin() as sess:
            q = sess.query(Image.path)\
                .join(Country, Country.geometry.ST_Contains(Image.location))\
                    .filter(Country.name == name)
        return [Path(i[0]) for i in q]
     

if __name__ == "__main__":
    # import time
    # from core.image_paths import PhotoPaths
    # from core.image_metadata import MetadataExtractor

    # t = time.time()
    # p = PhotoPaths(["/media/storage/Photo"])
    # meta = MetadataExtractor(p)

    # api = DbApi()
    # api.add_photo_to_db(meta.metadata)
    # print(f"Completed in {time.time() - t} seconds")

    api = DbApi()
    # res = api.select_files_and_output(location=(-31.95, 115.86, 0), distance_km=50)
    # res = api.get_photo_country()
    
    res = api.find_photos_by_country_name('Russia')
    print(res)
