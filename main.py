import argparse
from pathlib import Path

from core.image_metadata import MetadataExtractor
from core.image_paths import get_paths
from database.db_api import DbApi
from database.schema import create_schema
from settings.settings import load_settings


SETTINGS = load_settings()

parser = argparse.ArgumentParser(
    description="Sort images based on date and/or location using a local PostGIS database to store metadata.",
)

# give option of using either a long or short labels
inp = parser.add_mutually_exclusive_group(required=True)
out = parser.add_mutually_exclusive_group(required=False)

parser.add_argument(
    "setup", action="store", type=str, help="Perform intial setup", nargs="*", default=False
)
parser.add_argument(
    "sort-files",
    action="store",
    type=str,
    help="Sort images and output to a folder",
    nargs="*",
    default=False,
)

inp.add_argument("--input", action="store", type=str, help="Input folder for initial setup")
inp.add_argument("-i", action="store", type=str, help="Input folder for initial setup")

out.add_argument("--output", action="store", type=str, help="Output folder for sorting operation")
out.add_argument("-o", action="store", type=str, help="Output folder for sorting operation")

parser.add_argument(
    "--hash",
    help="Calculate image hashes during setup and store in the database",
    action="store_true",
)
parser.add_argument("-C", help="Add sorting by country location", action="store_true")
parser.add_argument("-c", help="Add sorting by city location", action="store_true")
parser.add_argument("-Y", help="Date sort by year photo taken", action="store_true")
parser.add_argument("-m", help="Date sort by month", action="store_true")
parser.add_argument("-d", help="Date sort by day", action="store_true")

args = parser.parse_args()

print(f"Input: {args.input or args.i}")
print(f"Args: {args}")


def perform_initial_setup(source_folder: str):
    do_hash = bool(args.hash)
    create_schema()
    p = get_paths([source_folder])
    meta = MetadataExtractor(p, hash_images=do_hash)
    api = DbApi()
    api.add_photo_to_db(meta.metadata)


def create_folder_structure():
    pass


if args.setup and (args.input or args.i):
    perform_initial_setup(args.input or args.i)


if __name__ == "__main__":
    pass
