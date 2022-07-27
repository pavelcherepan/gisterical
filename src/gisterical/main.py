import argparse
from time import time
from pathlib import Path
from loguru import logger
from shutil import copyfile

from gisterical.core.image_metadata import MetadataExtractor
from gisterical.core.image_paths import get_paths
from gisterical.core.create_folder_structure import Node, traverse, populate_folder_structure, make_folder
from gisterical.database.db_api import DbApi
from gisterical.database.schema import create_schema
from gisterical.settings.settings import load_settings, update_settings
from gisterical.util.file_meta import FileMeta


SETTINGS = load_settings()
api = DbApi()
parser = argparse.ArgumentParser(
    description="Sort images based on date and/or location using a local PostGIS database to store metadata.",
)

# give option of using either a long or short labels
inp = parser.add_mutually_exclusive_group(required=False)
out = parser.add_mutually_exclusive_group(required=False)
nam = parser.add_mutually_exclusive_group(required=False)

parser.add_argument(
    "--set-connection", 
    action="store_true", 
    help="Perform intial setup", 
    default=False, 
    required=False
)
parser.add_argument(
    "--setup", 
    action="store_true", 
    help="Perform intial setup", 
    default=False, 
    required=False
)
parser.add_argument(
    "--add-folder", 
    action="store_true", 
    help="Add photos to the database. Input folder has to be provided.",
    default=False,
    required=False
)
parser.add_argument(
    "--sort",
    action="store",
    type=str,
    help="Sort images and output to a folder",
    nargs="+",
    default=False, 
    required=False
)

inp.add_argument("--input", action="store", type=str, help="Input folder for initial setup")
inp.add_argument("-i", action="store", type=str, help="Input folder for initial setup")

out.add_argument("--output", action="store", type=str, help="Output folder for sorting and search operations")
out.add_argument("-o", action="store", type=str, help="Output folder for sorting and search operations")

parser.add_argument("--find-by-city", action="store", type=str, 
                    help="Find photos taken within certain distance from a specific city and output to target folder. " 
                    "Output folder, city name, and distance parameters have to be provided.")
parser.add_argument("--find-by-country", action="store", type=str, 
                    help="Find photos taken within a country and output to target folder. "
                    "Country name and output folder parameters need to be provided.")
nam.add_argument("--name", action="store", type=str, help="A city or country name to search in photos.")
nam.add_argument("-n", action="store", type=str, help="A city or country name to search in photos.")

parser.add_argument("--distance", action="store", type=int, help="Maximum match distance to between a photo location and a city.")
 
parser.add_argument(
    "--hash",
    help="Calculate image hashes during setup and store in the database",
    action="store_true",
)

args = parser.parse_args()


def perform_initial_setup(source_folder: str):
    """Perform initial set-up of the database for which we create 
    the base schema, extract the necessary metadata extracted from images,
    and populate image data along with the country and city data into
    the db.

    Args:
        source_folder (str): A string of the source folder containing images.
    """
    do_hash = bool(args.hash)
    create_schema()
    p = get_paths([source_folder])
    meta = MetadataExtractor(p, hash_images=do_hash)
    api.add_photo_to_db(meta.metadata)


def check_flags(args: argparse.Namespace) -> tuple[list[str], int, Path]:
    """Check positional flags and validate.

    Args:
        args (argparse.Namespace): A Namespace object containing all passed arguments

    Raises:
        ValueError: raised if unrecognised arguments are passed; output folder is missing;
            distance argument not present when "c" flag is included.

    Returns:
        tuple[list[str], int, Path]: A tuple consisting of a list of individual positional params, 
            integer of distance to find nearest city in kilometres and the output path.
    """
    inp = list(args.sort[0]) if len(args.sort) == 1 else args.sort
    v = set(inp).intersection({'C', 'c', 'Y', 'm', 'd'})

    if not args.output and not args.o:
        raise ValueError('Output folder parameter required when sorting!')
    p = args.output or args.o
    pth = Path(p)

    if len(v) != len(inp):
        logger.exception(f'Some of the input arguments {inp} not recognised. '
                        f'Accepted flags are "C", "c", "Y", "m" and "d".')
        raise ValueError('Positional arguments not recognised!')
    if "c" in inp and not args.distance:
        raise ValueError("Distance argument (--distance) required when sorting by city.")
    return inp, args.distance , pth 


def _parse_positional_args(input_args: argparse.Namespace) -> tuple[Path, list[FileMeta], list[str]]:
    """Parse positional flags used for sorting and decide which specific
    database api method to run to get the data necessary to build a tree-like
    folder structure.

    Args:
        input_args (argparse.Namespace): A Namespace object with input arguments.

    Returns:
        tuple[Path, list[FileMeta], list[str]]: A tuple consisting of the output path location,
            a list of FileMeta objects representing required file metadata and the list of
            validated sorting flags.
    """
    sorted_flags, distance, out_path = check_flags(input_args) 
    if len({"C", "c"}.intersection(sorted_flags)) == 2:
        # a lot of photos don't have location data but often you'd still want
        # to sort them by date. If you do a spatial join then these photos will
        # be missed so we run another query on the db where we extract all
        # photos with missing location information. This is computationally
        # very cheap so there's little benefit to not doing this.
        data_mis = api.get_photo_no_location()
        data_loc = api.get_photo_city_country(distance)
        data = data_loc + data_mis
    elif "c" in sorted_flags:
        data_mis = api.get_photo_no_location()
        data_loc = api.get_photos_by_city(distance)
        data = data_loc + data_mis
    elif "C" in sorted_flags:
        data_mis = api.get_photo_no_location()
        data_loc = api.get_photo_country()
        data = data_mis + data_loc
    else:
        data = api.get_photo_path_date()
    return out_path, data, sorted_flags


def run_sort_task(input_args: argparse.Namespace):
    """Run the sorting task. For this use the helper function to
    get the required data, then using metadata extracted from db
    build an m-ary tree of folder structure, traverse the tree to
    build the dataset and finally create necessary folders and
    move files to new locations.

    Args:
        input_args (argparse.Namespace): A Namespace object with input arguments.
    """
    out_path, data, sorted_flags = _parse_positional_args(input_args)    
    n = Node(out_path, data, sorted_flags)
    tree = traverse(n)
        
    for leaf in tree:
        make_folder(leaf)
    
    populate_folder_structure(tree)  
 
 
def copy_files(paths: list[Path], target_folder: Path):
    if not target_folder.exists():
        make_folder(target_folder)
    for f in paths:
        target_file = target_folder / f.name
        copyfile(str(f), str(target_file))  
        

def _validate_search_inputs(args: argparse.Namespace) -> Path:
    if not args.output and not args.o:
        raise ValueError('Output folder must be provided for search operations.')
    t = args.output or args.o
    out = Path(t)
    if args.find_by_city and not args.distance:
        raise ValueError('Distance needs to be provided to search by city name.')
    return out
    
        
def main():   
    t = time() 
    if args.set_connection:
        update_settings()
    elif args.setup and (args.input or args.i):
        perform_initial_setup(args.input or args.i)
    elif args.sort:
        run_sort_task(args)
    elif args.find_by_city:
        out = _validate_search_inputs(args)
        paths = api.find_photos_by_city_name(args.distance, args.find_by_city)
        copy_files(paths, out)
    elif args.find_by_country:
        out = _validate_search_inputs(args)
        paths = api.find_photos_by_country_name(args.find_by_country)
        copy_files(paths, out)       
    elif args.add_folder:
        if not args.input and not args.i:
            raise ValueError("Input folder must be provided.")
        fol = args.input or args.i
        p = get_paths([fol])
        meta = MetadataExtractor(p, hash_images=args.hash)
        api.add_photo_to_db(meta.metadata)
    logger.info(f'Successfully completed in {time() - t} seconds.')        


if __name__ == "__main__":
    main()
