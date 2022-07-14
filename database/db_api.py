import datetime as dt
from pathlib import Path
from shutil import copyfile

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from database.schema import Image
from core.image_metadata import PhotoData, MetadataExtractor
from core.image_paths import PhotoPaths
from settings.settings import load_settings


SETTINGS = load_settings()


class DbApi:
    conn_str = SETTINGS.conn_str
    engine: Engine = create_engine(conn_str)
    session = sessionmaker(engine)

    def add_photo_to_db(self, data: list[PhotoData]):
        with self.session.begin() as sess:
            for d in data:
                if -999 not in {d.latitude, d.longitude, d.altitude}:
                    loc = f"POINTZ({d.latitude} {d.longitude} {d.altitude})"
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
                )

                sess.add(new_result)
                sess.flush()
            sess.commit()

    def select_files_and_output(
        self,
        location: tuple[float, ...] = (0, 0, 0),
        distance_km: int | float = 1e10,
        start_date: dt.datetime = dt.datetime(1900, 1, 1),
        end_date: dt.datetime = dt.datetime(9999, 1, 1),
        target_folder: str | Path = "/home/pavel/Pictures/temp",
    ):
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

        for pth in res:
            fname = Path(pth).name
            copyfile(str(pth), str(p / fname))


if __name__ == "__main__":
    # import time

    # t = time.time()
    # p = PhotoPaths(("/media/storage/Photo",))
    # meta = MetadataExtractor(p)

    # api = DbApi()
    # api.add_photo_to_db(meta.metadata)
    # print(f"Completed in {time.time() - t} seconds")

    api = DbApi()
    res = api.select_files_and_output(location=(-31.95, 115.86, 0), distance_km=50)
