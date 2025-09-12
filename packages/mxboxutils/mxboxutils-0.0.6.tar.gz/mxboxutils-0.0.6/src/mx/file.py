import os
import pathlib

IMG_TYPE = ["jpg", "jpeg", "png"]

def all_files(f_path: str) -> list[str]:
    if not os.path.exists(f_path):
        return []
    if not os.path.isdir(f_path):
        return []

    return ["".join(pathlib.Path(f).suffixes) for f in os.listdir(f_path)]

def all_images(f_path: str, f_ext: list[str]) -> list[str]:
    files = all_files(f_path)
    images: list[str] = []
    if not files:
        return []
    exts = ["." + ext for ext in f_ext]

    for f in files:
        ext = f.split(".")[-1]
        if ext in exts:
            images.append(f)

    return images
