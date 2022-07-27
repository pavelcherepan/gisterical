from __future__ import annotations

from typing import Any
from pathlib import Path
from shutil import copyfile
from dataclasses import dataclass, field

from gisterical.util import FileMeta


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
            if current_condition == "C":
                children_data[str(f)]["metadata"] = [i or "Unknown_country" for i in self.metadata if i.country == f]

            elif current_condition == "Y":
                children_data[str(f)]["metadata"] = [i for i in self.metadata if i.date.year == f]
            elif current_condition == "c":
                children_data[str(f)]["metadata"] = [i or "Unknown_city" for i in self.metadata if i.city == f]


            elif current_condition == "d":
                children_data[str(f)]["metadata"] = [i for i in self.metadata if i.date.day == f]
            elif current_condition == "m":
                children_data[str(f)]["metadata"] = [i for i in self.metadata if i.date.month == f]
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


def populate_folder_structure(files: dict[Path, list[str | Path]]):
    for target_fol, original_files in files.items():
        for f in original_files:
            target_file = target_fol / Path(f).name
            copyfile(str(f), str(target_file))


if __name__ == "__main__":
    pass
    # from database.db_api import DbApi
    # COND = ["Y", "m", ]

    # api = DbApi()
    # d = api.get_photo_path_date()
    
    # n = Node(Path('temp'), metadata=d, conditions=COND)
    
    # tree = traverse(n)
    
    # for leaf in tree:
    #     make_folder(leaf)
        
    # move_files(tree)

