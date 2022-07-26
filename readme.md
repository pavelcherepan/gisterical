# Introduction
GISterical is a command-line tool for managing a photo library. The primary use is to
sort photos in a user-defined folder structure. User defines the sorting by 
adding command-line flags in a specific order, for example, `YmC` will create 
and populate the folder structure where the top level is year (**Y**), followed by month
(**m**) and then country (**C**) where the photo was taken:
```
2022
  |___1
  |   |__ Australia
  |   |__ Hong Kong
  |
  |___2
      |__Australia
```

The full list of available flags is:
* Y -- sort by year
* m -- sort by month
* d -- sort by calendar date
* C -- sort by country where the photo was taken
* c -- sort by the nearest city within a certain distance

The tool is very fast in comparison to most other photo managers I used and 3-level
sorting of a 15,000 files and 40 Gb size photo collection including copying files to 
the target location on a different physical drive takes approximately 3-4 minutes.


# Initial setup 
The tool works by building a (local) PostGIS database containing metadata extracted 
from user folders and additional data for coordinates of 47,000 of major cities and 
country boundaries. This allows to perform merges between images with location data 
and spatial objects.

For this a PostgreSQL service has to be running either locally on a remote location and 
a blank database needs to be created with a superuser created.

Depending on the system the instructions for setting up a PostgreSQL service can be found:
* [Fedora Linux](https://docs.fedoraproject.org/en-US/quick-docs/postgresql/)
* [Ubuntu-based distributions](https://ubuntu.com/server/docs/databases-postgresql)
* [Windows](https://www.microfocus.com/documentation/idol/IDOL_12_0/MediaServer/Guides/html/English/Content/Getting_Started/Configure/_TRN_Set_up_PostgreSQL.htm)

After the installation has been completed, a PostGIS extension needs to be additionally 
installed, which on common Linux distributions can be done via:
```
sudo dnf install postgis

or

sudo apt install postgis
```
On Windows systems PostGIS can be installed from a binary that can be downloaded [here](https://postgis.net/windows_downloads/).

Once this has been done the final step is to create a database, user and add the 
extension to the database. To do it first we log into PostgreSQL management tool as a superuser
```
sudo -U postgres psql
```

Now in the console we run the following commands:

```
CREATE USER <new_user_name> WITH PASSWORD <password>;
CREATE DATABASE <new_db_name> OWNER <new_user_name>;
\connect <new_db_name>
CREATE EXTENSION postgis;
```

And now you should be ready to use the tool.

# Usage

## Populated database
The first task is to run initial set-up of the image database and populate spatial data into the 
database. For this use `--setup` flag followed by `-i` or `--input` and the folder where photos 
are located:
```
python gisterical.py --setup -i /home/pav/Pictures
```
For my 15,000-file photo collection the setup takes about 40 seconds. The only other option
that can be used during the initial set-up is whether or not to hash the images using `--hash` option. 
Hashing will allow you to identify duplicated images even when they've been cropped and resize. 
If hashing is enabled then perceptual and color hashes are calculated for each image using
[Imagehash](https://pypi.org/project/ImageHash/) library.

**Note:** The process is approximately 100x slower with hashing enabled! So use only if you 
specifically need to deal with duplicates.

New folders can be added at any time to the existing database using:
```
python gisterical.py --add-folder -i <path_to_folder>
```

## Sort photos
To sort images use `--sort` option followed by any combination of sorting flags listed above.
The order of the flags will deternime the sorting order in the resulting file structure, 
for example, `YmC` will sort with year at top level, but `CYm` will have country as the top-level
folder.

The command also needs to be followed by the output folder name where the new file structure 
will be created using `-o` or `--output` options. The files are only ever copied to the new 
location so the original files will never be affected. The full syntax of sorting command is:
```
python gisterical.py --sort <sorting_flags> -o <output_folder>
```

Sorting by city is the most expensive operation since a complicated merge needs to be calculated 
in the database. This sorting operation also finds cities within a certain radius (in kilometers) 
of photo location which needs to be provided using `--distance` option.

**Note:** When multiple cities fall within the search radius the one with the largest population
will be selected as the location of the photo. This can also occasionally create inconsistencies
between country and city of of origin in which case the best option is to reduce the search distance.

To sort with "nearest city" as one of the parameters:
```
python gisterical.py --sort <sorting_flags> -o <output_folder> --distance 50
```

## Find images
The tool can additionally be used to locate images by country or nearest city. In this case
the script will locate all the relevant photos and output them to an `--output` (`-o`) folder.
As is for sorting, to find by city, a distance parameter is required.
For example,
```
python gisterical.py --find-by-city Melbourne -o /home/Pictures/Melbourne_stuff --distance 50
```

To search by country of origin distance is not required:
```
python gisterical.py --find-by-country Malaysia -o <output_folder>
```


