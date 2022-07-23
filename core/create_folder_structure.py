from __future__ import annotations

import datetime as dt
from typing import Any
from pathlib import Path
from shutil import copyfile
from dataclasses import dataclass, field


@dataclass
class FileMeta:
    path: str | Path
    date: dt.datetime
    country: str
    city: str


def filter_year(data: list[FileMeta]) -> set[int]:
    return {i.date.year for i in data}


def filter_month(data: list[FileMeta]) -> set[int]:
    return {i.date.month for i in data}


def filter_day(data: list[FileMeta]) -> set[int]:
    return {i.date.day for i in data}


def filter_country(data: list[FileMeta]) -> set[str]:
    return {i.country for i in data}


def filter_city(data: list[FileMeta]) -> set[str]:
    return {i.city for i in data}


condition_dict = {
    "Y": {"fun": filter_year, "id": 1},
    "m": {"fun": filter_month, "id": 1},
    "d": {"fun": filter_day, "id": 1},
    "C": {"fun": filter_country, "id": 2},
    "c": {"fun": filter_city, "id": 3},
}


@dataclass
class Node:
    folder: Path
    metadata: list[FileMeta] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)

    @property
    def children(self) -> list["Node"] | None:
        if len(self.conditions) == 0:
            return None
        current_condition = self.conditions[0]
        fun = condition_dict[current_condition]["fun"]

        fnames: list[int | str] = fun(self.metadata)
        children_data: dict[str, dict[str, Any]] = {str(n): {} for n in fnames}
        for f in fnames:
            children_data[str(f)]["folder"] = self.folder / str(f)
            children_data[str(f)]["conditions"] = self.conditions[1:]
            if current_condition == "Y":
                children_data[str(f)]["metadata"] = [i for i in self.metadata if i.date.year == f]
            elif current_condition == "m":
                children_data[str(f)]["metadata"] = [i for i in self.metadata if i.date.month == f]
            elif current_condition == "d":
                children_data[str(f)]["metadata"] = [i for i in self.metadata if i.date.day == f]
            elif current_condition == "C":
                children_data[str(f)]["metadata"] = [i for i in self.metadata if i.country == f]
            elif current_condition == "c":
                children_data[str(f)]["metadata"] = [i for i in self.metadata if i.city == f]

        return [Node(**i) for i in children_data.values()]


def traverse(
    root: Node, folders: dict[Path, list[str | Path]] | None = None
) -> dict[Path, list[str | Path]]:
    # build a dictionary with folderPath as the key and list of file paths as value
    folders = folders or {}
    r = root.children
    if not r or len(root.conditions) == 0:
        if root.folder not in folders:
            # for leaf node add folder name and corresponding files
            folders[root.folder] = [i.path for i in root.metadata]
    else:
        for child in r:
            if isinstance(child, Node):
                par = child.folder.parent
                # we only want the data from leaf nodes so
                # if the record for the current folder's parent
                # already exists we delete it from the dictionary
                # and add the current folder data
                if par in folders:
                    del folders[par]
                folders[child.folder] = [i.path for i in child.metadata]
                traverse(child, folders)
    return folders


def make_folder(path: Path, children: list[Path] = None) -> None:
    if path.exists():
        return
    children = children or []
    if path.parent.is_dir():
        # print(f'Creating folder {path}')
        path.mkdir()
        if not children:
            return
        return make_folder(children[0])

    else:
        # print(f'Folder {path} does not exist')
        children.append(path)
        return make_folder(path.parent, children)


def move_files(files: dict[Path, list[str]]):
    for target_fol, original_files in files.items():
        for f in original_files:
            target_file = target_fol / Path(f).name
            copyfile(str(f), str(target_file))


if __name__ == "__main__":
    COND = ["Y", "m", "C"]

    # d - 2d list in form [[fname, date, country, city]]
    d = [
        ("/media/storage/Photo/Photo/Phone/IMAG0036.jpg", dt.datetime(2019, 1, 1), "Aus", "Bri"),
        ("/media/storage/Photo/Photo/Phone/IMAG0037.jpg", dt.datetime(2019, 1, 5), "Aus", "Bri"),
        ("/media/storage/Photo/Photo/Phone/IMAG0038.jpg", dt.datetime(2019, 2, 10), "Aus", "Mel"),
        ("/media/storage/Photo/Photo/Phone/IMAG0039.jpg", dt.datetime(2020, 1, 1), "Aus", "Per"),
        ("/media/storage/Photo/Photo/Phone/IMAG0042.jpg", dt.datetime(2020, 1, 10), "Aus", "Per"),
        ("/media/storage/Photo/Photo/Phone/IMAG0043.jpg", dt.datetime(2020, 1, 25), "Aus", "Per"),
        ("/media/storage/Photo/Photo/Phone/IMAG0046.jpg", dt.datetime(2020, 10, 5), "My", "KL"),
        ("/media/storage/Photo/Photo/Phone/IMAG0047.jpg", dt.datetime(2020, 11, 6), "Ru", "Led"),
        ("/media/storage/Photo/Photo/Phone/IMAG0048.jpg", dt.datetime(2020, 12, 1), "Ru", "Mos"),
        ("/media/storage/Photo/Photo/Phone/IMAG0050.jpg", dt.datetime(2021, 3, 5), "Aus", "Syd"),
        ("/media/storage/Photo/Photo/Phone/IMAG0051.jpg", dt.datetime(2021, 5, 1), "Aus", "Mel"),
        ("/media/storage/Photo/Photo/Phone/IMAG0052.jpg", dt.datetime(2021, 6, 1), "Aus", "Per"),
        ("/media/storage/Photo/Photo/Phone/IMAG0053.jpg", dt.datetime(2021, 11, 1), "Chi", "Bei"),
        ("/media/storage/Photo/Photo/Phone/IMAG0055.jpg", dt.datetime(2021, 11, 15), "Jp", "Tok"),
        ("/media/storage/Photo/Photo/Phone/IMAG0076.jpg", dt.datetime(2022, 1, 1), "Aus", "Per"),
        ("/media/storage/Photo/Photo/Phone/IMAG0078.jpg", dt.datetime(2022, 3, 1), "Aus", "Bri"),
        ("/media/storage/Photo/Photo/Phone/IMAG0079.jpg", dt.datetime(2022, 3, 5), "Aus", "Per"),
        ("/media/storage/Photo/Photo/Phone/IMAG0080.jpg", dt.datetime(2022, 3, 11), "My", "KL"),
        ("/media/storage/Photo/Photo/Phone/IMAG0095.jpg", dt.datetime(2022, 5, 1), "Aus", "Syd"),
        ("/media/storage/Photo/Photo/Phone/IMAG0096.jpg", dt.datetime(2022, 8, 8), "Aus", "Bri"),
    ]

    data = [FileMeta(*i) for i in d]
