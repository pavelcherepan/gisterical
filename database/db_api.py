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


if __name__ == "__main__":
    import time

    t = time.time()
    p = PhotoPaths(("/media/storage/Photo",))
    meta = MetadataExtractor(p)

    api = DbApi()
    api.add_photo_to_db(meta.metadata)
    print(f"Completed in {time.time() - t} seconds")
