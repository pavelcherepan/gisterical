from pathlib import Path


def get_paths(
    folders: tuple[str | Path],
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
    ),
) -> tuple[Path]:
    all_files: list[Path] = []
    for fol in folders:
        if isinstance(fol, str):
            fol = Path(fol)
        for e in search_extensions:
            all_files.extend(list(fol.rglob(f"*{e}")))
    return tuple(all_files)


if __name__ == "__main__":
    p = get_paths(("/media/storage/Photo/Photo/Phone",))
    for i in p:
        print(i)
