#!/usr/bin/env python3

from PIL import Image, ImageOps, ImageChops
import numpy as np
import os

from typing import Callable, List, Any

from toolbox.logger import console


WHITE = (255, 255, 255)


def rgba_white_alpha(img: Image.Image, **kwargs):
    """Convert an RGBA to B&W, changing white pixels to transparent."""
    alpha = np.array(img.convert("L"))
    out_array = np.full(alpha.shape + (4,), 255, dtype=np.uint8)
    out_array[:, :, 3] = alpha
    return Image.fromarray(out_array)

def resize_and_pad(img: Image.Image, **kwargs):
    """Resize the image to the specified dimensions, padding with the specified color."""
    size = (1024, 1024)
    with img as img:
        # Convert to RGB to ensure white padding works (handles PNG transparency)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # Resize image while maintaining aspect ratio
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Create a new white background canvas
        new_img = Image.new("RGB", size, WHITE)
        
        # Paste the resized image into the center of the canvas
        upper_left = (
            (size[0] - img.size[0]) // 2,
            (size[1] - img.size[1]) // 2
        )
        new_img.paste(img, upper_left)
        return new_img
    
def exif_rotate(img: Image.Image, **kwargs):
    """
    Reads an image, rotates it according to EXIF data so it appears upright,
    and saves it back to disk.
    """
    with img as img:
        try:
            fixed_img = ImageOps.exif_transpose(img)
            return fixed_img
            
        except Exception:
            return img
        
        
def crop_white(img: Image.Image, **kwargs):
    """Removes white borders from an image."""
    
    # Tolerance can be increased if the 'white' isn't perfectly #FFFFFF.
    tolerance = 0
    
    # Ensure image is in RGB mode
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Create a solid white background the same size as the image
    bg = Image.new("RGB", img.size, WHITE)
    
    # Calculate the difference between the image and the white background
    diff = ImageChops.difference(img, bg)
    
    # If tolerance is needed, apply a threshold here
    if tolerance > 0:
        diff = diff.point(lambda p: p if p > tolerance else 0)

    # Find the bounding box of the non-white area
    bbox = diff.getbbox()

    if bbox:
        return img.crop(bbox)
    else:
        # If the image is entirely white, return the original or a 1x1 pixel
        return img
    

def convert_images(filenames, converters: List[Callable[[Image.Image], Image.Image]], overwrite_existing: bool=False, overwrite: bool=False, **kwargs: Any):
    suffix = "_converted"
    filenames = filter(lambda f: not os.path.splitext(f)[0].endswith(suffix), filenames)
    
    for filename in filenames:
        img = Image.open(filename)
        for converter in converters:
            img = converter(img)
        if img:
            *pre, ext = filename.split(".")
            
            if overwrite_existing:
                out_file = filename
            else:
                out_file = f"{'.'.join(pre)}_converted.{ext}"
                
            if overwrite_existing or overwrite or not os.path.exists(out_file):
                console.log(f"Saving {out_file}")
                img.save(out_file)
            else:
                console.log(f"{out_file} already exists", style="red")
            
        
converters = dict(
    rgba_white_alpha=rgba_white_alpha,
    resize_and_pad=resize_and_pad,
    exif_rotate=exif_rotate,
    crop_white=crop_white,
)
