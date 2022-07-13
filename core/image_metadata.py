import datetime as dt
from pathlib import Path
from dateutil import parser

from exif import Image
from attrs import define
from loguru import logger

from image_paths import PhotoPaths


@define
class RawCoordinates:
    latitude: tuple[int, int, int]
    latitude_ref: str
    longitude: tuple[int, int, int]
    longitude_ref: str
    altitude: float


@define
class Coordinates:
    latitude: float
    longitude: float
    altitude: float


class PhotoMetadata:
    def __init__(self, image_paths: PhotoPaths):
        logger.info("Collecting metadata from image files.")
        self.paths: tuple[Path] = image_paths.photo_paths

    @property
    def metadata(self) -> list[Image]:
        metadata: list[Image] = []
        for p in self.paths:
            with open(p, "rb") as f:
                metadata.append(Image(f))
        return metadata

    @property
    def _raw_coords(self) -> list[RawCoordinates]:
        res: list[RawCoordinates] = []
        for img in self.metadata:
            lat = img["gps_latitude"]
            lon = img["gps_longitude"]
            alt = img["gps_altitude"]
            lat_ref = img["gps_latitude_ref"]
            lon_ref = img["gps_longitude_ref"]
            res.append(
                RawCoordinates(
                    latitude=lat,
                    longitude=lon,
                    altitude=alt,
                    latitude_ref=lat_ref,
                    longitude_ref=lon_ref,
                )
            )
        return res

    @property
    def coords(self) -> list[Coordinates]:
        logger.info("Parsing coordinates and converting to decimal format.")
        coords: list[Coordinates] = []
        for c in self._raw_coords:
            lat = self._convert_coords_to_decimal(c.latitude, c.latitude_ref)
            lon = self._convert_coords_to_decimal(c.longitude, c.longitude_ref)
            coords.append(Coordinates(latitude=lat, longitude=lon, altitude=c.altitude))
        return coords

    @property
    def gps_accuracy(self) -> list[float]:
        logger.info("Extracting GPS accuracy data.")
        return [img.gps_horizontal_positioning_error for img in self.metadata]

    @property
    def photo_direction(self):
        pass

    @property
    def timestamp(self) -> list[dt.datetime]:
        logger.info("Parsing image timestamps.")
        return [parser.parse(img.datetime, dayfirst=True, fuzzy=True) for img in self.metadata]

    @property
    def make(self) -> list[str]:
        logger.info("Extracting camera make.")
        return [img.make for img in self.metadata]

    @property
    def model(self) -> list[str]:
        logger.info("Extracting camera model.")
        return [img.model for img in self.metadata]

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
