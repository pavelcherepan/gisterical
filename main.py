from core.image_metadata import PhotoData, MetadataExtractor
from core.image_paths import PhotoPaths
from database.schema import Image
from database.db_api import DbApi


p = PhotoPaths(("/media/storage/Photo/Photo/phone",))
meta = MetadataExtractor(p)

api = DbApi("postgresql+psycopg2://gis:gis@localhost/photo")
api.add_photo_to_db(meta.metadata[0])
