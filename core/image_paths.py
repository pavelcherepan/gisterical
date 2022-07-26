from pathlib import Path


def get_paths(
    folders: list[str | Path],
    search_extensions: tuple[str, ...] = (
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".bmp",
        ".gif",
        ".png",
    ),
) -> tuple[Path]:
    all_files: list[Path] = []
    for fol in folders:
        if isinstance(fol, str):
            fol = Path(fol)
        
        # on occasion extensions can be in upper case so adding
        # a second array containing uppercase extensions
        ext = list(search_extensions)
        extensions = ext + [i.upper() for i in ext]
        
        for e in extensions:
            all_files.extend(list(fol.rglob(f"*{e}")))
    return tuple(all_files)


if __name__ == "__main__":
    p = get_paths(["/media/storage/Photo/Photo/Phone",])
    for i in p:
        print(i)
