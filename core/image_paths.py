from pathlib import Path
from functools import lru_cache

from attrs import define


@define(frozen=True)
class PhotoPaths:
    folders: tuple[str | Path]
    search_extensions: tuple[str, ...] = (
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".bmp",
        ".gif",
        ".png",
        ".raw",
        ".cr2",
        ".nef",
        ".orf",
    )

    @property
    @lru_cache(maxsize=1)
    def photo_paths(self) -> tuple[Path]:
        all_files: list[Path] = []
        for fol in self.folders:
            if isinstance(fol, str):
                fol = Path(fol)
            for e in self.search_extensions:
                all_files.extend(list(fol.rglob(f"*{e}")))
        return tuple(all_files)


if __name__ == "__main__":
    p = PhotoPaths(("/media/storage/Photo/100MEDIA",))
    for p in p.photo_paths:
        print(p)
