#mosaicks tiles downloaded by download-years.py into a single raster for each year

import json
import sys
from pathlib import Path

import rasterio
from rasterio.merge import merge


# Set to a list of years (e.g. [2023, 2024]) or None to process every
# numeric year folder found in outputs_dir
YEARS = list(range(1985, 1987))

outputs_dir = Path("outputs").expanduser()
tiles_json = Path(__file__).parent / "outputs" / "AF-tiles.json"

with open(tiles_json) as f:
    n_expected = len(json.load(f))


def mosaic_year(year):
    tile_dir = outputs_dir / str(year)
    tile_files = sorted(tile_dir.glob("*.tif"))
    print(f"{year}: found {len(tile_files)} tiles in {tile_dir}")

    # Check the number of tif files matches the number of tiles specified
    if len(tile_files) != n_expected:
        print(
            f"{year}: tile count mismatch, expected {n_expected} "
            f"({tiles_json.name}); skipping"
        )
        return False

    src_files = [rasterio.open(f) for f in tile_files]
    try:
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

        outfile = outputs_dir / f"mapbiomas_c11_atlantic_forest_{year}.tif"
        with rasterio.open(outfile, "w", **metadata) as dst:
            dst.write(mosaic)
    finally:
        for src in src_files:
            src.close()

    print(f"{year}: saved {outfile}")
    return True


if YEARS is None:
    years = sorted(
        int(p.name) for p in outputs_dir.iterdir()
        if p.is_dir() and p.name.isdigit()
    )
else:
    years = YEARS

failed = [y for y in years if not mosaic_year(y)]

if failed:
    sys.exit(f"Not mosaicked (tile count mismatch): {failed}")