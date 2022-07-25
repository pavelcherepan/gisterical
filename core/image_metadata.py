import time
import datetime as dt
from pathlib import Path

from PIL import Image as PILImage
from exif import Image
import imagehash as imh
from attrs import define
from loguru import logger
from sqlalchemy import func

from core.image_paths import get_paths
from util.decorators import func_time


@define
class PhotoData:
    path: str
    latitude: float
    longitude: float
    altitude: float
    timestamp: dt.datetime
    gps_accuracy: float
    photo_direction: float
    camera_make: str
    camera_model: str
    phash: str | None = None
    colorhash: str | None = None


class MetadataExtractor:
    def __init__(self, image_paths: tuple[Path], hash_images: bool = False):
        logger.info("Collecting metadata from image files.")
        self.paths: tuple[Path] = image_paths
        self.__hash_images = hash_images
        self._raw_metadata = self.__raw_metadata()

    def __raw_metadata(self) -> dict[str, Image]:
        data: dict[str, Image] = {}
        for p in self.paths:
            with open(p, "rb") as f:
                data[str(p)] = Image(f)
        return data

    @property
    def metadata(self) -> list[PhotoData]:
        res: list[PhotoData] = []
        for cnt, (pth, img) in enumerate(self._raw_metadata.items(), start=1):
            logger.info(f"Processing image {cnt}/{len(self._raw_metadata)}")
            try:
                lat = self._convert_coords_to_decimal(img.gps_latitude, img.gps_latitude_ref)
                lon = self._convert_coords_to_decimal(img.gps_longitude, img.gps_longitude_ref)
                alt = img.gps_altitude
            except (AttributeError, KeyError):
                lat = lon = alt = -999

            try:                
                timestamp = dt.datetime.strptime(img.datetime_original, "%Y:%m:%d %H:%M:%S")
            except (AttributeError, KeyError):
                timestamp = dt.datetime(1900, 1, 1)

            try:
                gps_accuracy = img.gps_horizontal_positioning_error
            except (AttributeError, KeyError):
                gps_accuracy = -999

            try:
                photo_direction = img.gps_img_direction
            except (AttributeError, KeyError):
                photo_direction = -999

            try:
                camera_make = img.make
                camera_model = img.model
            except (AttributeError, KeyError):
                camera_make = "unknown device"
                camera_model = "unknown model"

            if self.__hash_images:
                logger.debug("Calculating image hashes.")
                t = time.time()
                im = PILImage.open(str(pth))
                phash = str(imh.phash(im))
                chash = str(imh.colorhash(im))
                print(f"Hashing image took {time.time() - t} seconds")
            else:
                phash = chash = None

            res.append(
                PhotoData(
                    path=pth,
                    latitude=lat,
                    longitude=lon,
                    altitude=alt,
                    timestamp=timestamp,
                    gps_accuracy=gps_accuracy,
                    photo_direction=photo_direction,
                    camera_make=camera_make,
                    camera_model=camera_model,
                    phash=phash,
                    colorhash=chash,
                )
            )
        return res

    def _convert_coords_to_decimal(self, coords: tuple[float, ...], ref: str) -> float:
        """Covert a tuple of coordinates in the format (degrees, minutes, seconds)
        and a reference to a decimal representation.

        Args:
            coords (tuple[float,...]): A tuple of degrees, minutes and seconds
            ref (str): Hemisphere reference of "N", "S", "E" or "W".

        Returns:
            float: A signed float of decimal representation of the coordinate.
        """
        if ref.upper() in {"W", "S"}:
            mul = -1
        elif ref.upper() in {"E", "N"}:
            mul = 1
        else:
            msg = f"Incorrect hemisphere reference. Expecting one of 'N', 'S', 'E' or 'W', got {ref} instead."
            logger.debug(msg)
            raise ValueError(msg)
        return mul * (coords[0] + coords[1] / 60 + coords[2] / 3600)


if __name__ == "__main__":
    import sys
    import time

    t = time.time()
    p = get_paths(["/media/storage/Photo"])
    meta = MetadataExtractor(p, hash_images=True)
    r = meta.metadata
    elapsed = time.time() - t

    print(f"Length: {len(r)} -- Memory: {sys.getsizeof(r)} -- Elapsed: {elapsed}")
