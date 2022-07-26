from pathlib import Path

import cv2
import numpy as np
import face_recognition as fc

# from core.image_paths import PhotoPaths

fol = Path("/media/storage/Photo/Photo/New Zealand")
# file = "/media/storage/Photo/Photo/New Zealand/DSC_7283.jpg"
files = list(fol.glob("*.jpg"))

for i, file in enumerate(files):
    print(f"Processing file {i+1}/{len(files)}")
    image = fc.load_image_file(file)
    face_locs: list[tuple[int, int, int, int]] = fc.face_locations(
        image, number_of_times_to_upsample=1
    )

    f = cv2.imread(str(file))

    if len(face_locs):
        for idx, r in enumerate(face_locs):
            x1 = np.maximum(0, r[0] - 100)
            x2 = np.minimum(image.shape[0], r[2] + 100)
            y1 = np.maximum(0, r[3] - 100)
            y2 = np.minimum(image.shape[1], r[1] + 100)

            f1 = f[x1:x2, y1:y2]
            try:
                cv2.imwrite(f"/home/pavel/Pictures/temp/{str(file.name)}-{idx}.png", f1)
            except Exception as e:
                print(e)
