import datetime as dt
from pathlib import Path
from dateutil import parser

from exif import Image
from attrs import define, field
from loguru import logger

from core.image_paths import PhotoPaths


@define
class RawCoordinates:
    latitude: tuple[int, int, int]
    latitude_ref: str
    longitude: tuple[int, int, int]
    longitude_ref: str
    altitude: float


@define
class PhotoData:
    path: str
    latitude: float = field(default=-999)
    longitude: float = field(default=-999)
    altitude: float = field(default=-999)
    timestamp: dt.datetime = field(default=dt.datetime(1900, 1, 1))
    gps_accuracy: float = field(default=-999)
    photo_direction: float = field(default=-999)
    camera_make: str = field(default="unknown device")
    camera_model: str = field(default="unknown model")


class MetadataExtractor:
    def __init__(self, image_paths: PhotoPaths):
        logger.info("Collecting metadata from image files.")
        self.paths: tuple[Path] = image_paths.photo_paths

    @property
    def _raw_metadata(self) -> dict[str, Image]:
        data: dict[str, Image] = {}
        for p in self.paths:
            with open(p, "rb") as f:
                data[str(p)] = Image(f)
        return data

    @property
    def metadata(self) -> list[PhotoData]:
        res: list[PhotoData] = []
        for pth, img in self._raw_metadata.items():
            try:
                lat = self._convert_coords_to_decimal(img.gps_latitude, img.gps_latitude_ref)
                lon = self._convert_coords_to_decimal(img.gps_longitude, img.gps_longitude_ref)
                alt = img.gps_altitude
            except (AttributeError, KeyError):
                lat = lon = alt = -999

            try:
                timestamp = parser.parse(img.datetime, dayfirst=True, fuzzy=True)
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
    p = PhotoPaths(("/media/storage/Photo",))
    meta = MetadataExtractor(p)
    r = meta.metadata
    elapsed = time.time() - t

    print(f"Length: {len(r)} -- Memory: {sys.getsizeof(r)} -- Elapsed: {elapsed}")
