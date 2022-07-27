import os
import time
import warnings
import datetime as dt
from pathlib import Path
from typing import Any

from PIL import Image as PILImage
from exif import Image
import imagehash as imh
from attrs import define
from loguru import logger

from gisterical.core.image_paths import get_paths

warnings.filterwarnings('ignore', module='exif')

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

    def __raw_metadata(self) -> dict[str, dict[str, Any]]:
        # this is bloody ugly but I' building the dict instead of
        # using Image object because the latter eats too much memory
        # and has caused crashes in the past. With this memory 
        # issues are solved.
        data: dict[str, dict[str, Any]] = {}
        for p in self.paths:
            with open(p, "rb") as f:
                tmp = Image(f)
                try:
                    lat = tmp.get('gps_latitude')
                    lat_ref = tmp.get('gps_latitude_ref')
                    lon = tmp.get('gps_longitude')
                    lon_ref = tmp.get('gps_longitude_ref')
                    alt = tmp.get('gps_altitude')
                except (AttributeError, KeyError):
                    lat = lon = alt = None
                    lat_ref = lon_ref = None
                    
                try:
                    date = tmp.get('datetime_original') or '1900:1:1 00:00:00'
                except (AttributeError, KeyError):
                    date = '1900:1:1 00:00:00'
                    
                try:
                    hor_pos = tmp.get('gps_horizontal_positioning_error')
                    direct = tmp.get('gps_img_direction')
                except (AttributeError, KeyError):
                    hor_pos = direct = -999
                    
                try:
                    mk = tmp.get('make')
                    mod = tmp.get('model') 
                except (AttributeError, KeyError):
                    mk = "unknown device"
                    mod = "unknown model"
                
                
                data[str(p)] = {'gps_latitude': lat,
                    'gps_latitude_ref': lat_ref,
                    'gps_longitude': lon,
                    'gps_longitude_ref': lon_ref,
                    'gps_altitude': alt,
                    'datetime_original': date,
                    'gps_horizontal_positioning_error': hor_pos,
                    'gps_img_direction': direct,
                    'make': mk,
                    'model': mod                 
                }
        return data

    @property
    def metadata(self) -> list[PhotoData]:
        res: list[PhotoData] = []
        for cnt, (pth, dic) in enumerate(self._raw_metadata.items(), start=1):
            # logger.info(f"Processing image {cnt}/{len(self._raw_metadata)}")
            try:
                lat = self._convert_coords_to_decimal(dic['gps_latitude'], dic['gps_latitude_ref'])
                lon = self._convert_coords_to_decimal(dic['gps_longitude'], dic['gps_longitude_ref'])
                alt = dic['gps_altitude']
            except (AttributeError, KeyError):
                lat = lon = alt = -999

            # when getting dates so images (like those sent through WhataApp, Telegram etc)
            # won't have correct date recorded so instead we take the last modified date
            # and select it instead            
            try:                
                timestamp = dt.datetime.strptime(dic['datetime_original'], "%Y:%m:%d %H:%M:%S")
            except (AttributeError, KeyError, ValueError):
                ts = os.path.getmtime(pth)
                timestamp = dt.datetime.utcfromtimestamp(ts)
            else:
                # if the image has datetime recorded we check whether it is in the future
                # (due to incorrect camera setup and such) or whether it is before 1/1/1970
                # and if either of these is true then we take modified date still
                if timestamp > dt.datetime.now() or timestamp < dt.datetime(1970, 1, 1):
                    ts = os.path.getmtime(pth)
                    timestamp = dt.datetime.utcfromtimestamp(ts)                

            gps_accuracy = dic['gps_horizontal_positioning_error']
            photo_direction = dic['gps_img_direction']
            camera_make = dic['make']
            camera_model = dic['model']

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
