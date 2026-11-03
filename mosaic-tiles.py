#mosaicks tiles downloaded by download-years.py into a single raster for each year

from pathlib import Path

import rasterio
from rasterio.merge import merge


YEAR = 2024

outputs_dir = Path(f"~/projects/mapbiomas/verena/outputs")
tile_dir = Path(f"{outputs_dir}/{YEAR}").expanduser()

print(tile_dir)

tile_files = sorted(
    tile_dir.glob("*.tif")
)

print(f"Found {len(tile_files)} tiles")

# Open all rasters

if(len(tile_files) > 0):
    src_files = [
        rasterio.open(f)
        for f in tile_files
    ]

    # Merge

    mosaic, transform = merge(src_files)

    # Copy metadata from first tile

    metadata = src_files[0].meta.copy()

    metadata.update(
        {
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": transform,
            "compress": "lzw",
            "tiled": True,
        }
    )

    outfile = (
        outputs_dir /
        f"mapbiomas_c11_atlantic_forest_{YEAR}.tif"
    ).expanduser()

    with rasterio.open(
        outfile,
        "w",
        **metadata
    ) as dst:

        dst.write(mosaic)

    for src in src_files:
        src.close()

    print(f"Saved {outfile}")
    
else:
    print("No tiles found to merge")