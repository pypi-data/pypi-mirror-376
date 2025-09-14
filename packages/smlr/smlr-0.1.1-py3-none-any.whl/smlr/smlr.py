from . import dct
import os
import numpy as np
from PIL import Image

class SMLR:
    @classmethod
    def compress(self, filepath, ratio=4):
        if not os.path.isfile(filepath):
            raise ValueError(f"Invalid filepath: {filepath}")

        if ratio <= 0:
            raise ValueError("ratio must be >= 1")

        # Load image as-is and capture EXIF to reuse on output
        img = Image.open(filepath)
        exif_bytes = None
        try:
            exif_bytes = img.info.get("exif")
            if not exif_bytes:
                exif = img.getexif()
                if exif:
                    exif_bytes = exif.tobytes()
        except Exception:
            exif_bytes = None

        # Convert to RGB to preserve color and get a 3D array
        img = img.convert("RGB")
        img_arr = np.asarray(img)

        # Ensure output matches the input shape by padding to tile size
        # and cropping back after decompression. Do not use EXIF orientation.
        h, w = img_arr.shape[:2]
        T = 8
        pad_h = (T - (h % T)) % T
        pad_w = (T - (w % T)) % T
        if pad_h or pad_w:
            img_arr_padded = np.pad(
                img_arr,
                ((0, pad_h), (0, pad_w), (0, 0)),
                mode="edge",
            )
        else:
            img_arr_padded = img_arr

        # Run compression on padded data
        compressed_img = dct.compress(img_arr_padded, ratio)

        # Crop back to original dimensions
        if pad_h or pad_w:
            compressed_img = compressed_img[:h, :w]

        # Convert to uint8 image for saving
        compressed_img = np.clip(compressed_img, 0, 255).astype(np.uint8)
        out_name = "compressed_" + os.path.basename(filepath)
        out_img = Image.fromarray(compressed_img)
        try:
            if exif_bytes:
                out_img.save(out_name, exif=exif_bytes)
            else:
                out_img.save(out_name)
        except Exception:
            out_img.save(out_name)
