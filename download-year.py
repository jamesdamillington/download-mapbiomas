from pathlib import Path
import ee
import requests
import json

# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------

PROJECT_ID = "ee-jamesmillington-01"

OUTDIR = Path("~/projects/mapbiomas/verena/outputs").expanduser()
OUTDIR.mkdir(exist_ok=True)

YEAR = 2024

# ---------------------------------------------------------
# Initialize Earth Engine
# ---------------------------------------------------------

ee.Initialize(project=PROJECT_ID)

# ---------------------------------------------------------
# Read tile metadata from JSON file
infile = OUTDIR / "AF-tiles.json"
with open(infile) as f:
    tile_metadata = json.load(f)

tiles = []

for tile in tile_metadata:

    tile["geometry"] = ee.Geometry.Rectangle(
        [
            tile["xmin"],
            tile["ymin"],
            tile["xmax"],
            tile["ymax"]
        ]
    )

    tiles.append(tile)

print(f"Loaded {len(tiles)} tiles from {infile}")


# ---------------------------------------------------------
# Collection 11
# ---------------------------------------------------------

mb = ee.Image(
    "projects/mapbiomas-public/assets/brazil/lulc/collection11/"
    "mapbiomas_brazil_collection11_coverage_v3"
)

# ---------------------------------------------------------
# Atlantic Forest biome
# ---------------------------------------------------------

biomes = ee.FeatureCollection(
    "projects/mapbiomas-territories/assets/"
    "TERRITORIES/BRAZIL/WORKSPACE/BIOMES/BIOMES_v4"
)

geom = (
    biomes
    .filter(ee.Filter.eq("NM_BIOMA", "Mata Atlântica"))
    .geometry()
)
    
# ---------------------------------------------------------
# Select year
# ---------------------------------------------------------

image = (
    mb.select(f"classification_{YEAR}")
      .clip(geom)
      .toByte()
)

# ---------------------------------------------------------
# Generate download URL
# ----------------------------------------------

for tile in tiles:

    print(f"Processing tile {tile['id']}...")
    print(f"Tile bounds: {tile['xmin']}, {tile['ymin']}, {tile['xmax']}, {tile['ymax']}")
    
    print("Generating download URL...")
    url = image.getDownloadURL(
        {
            "region": tile["geometry"],
            "scale": 30,
            "format": "GEO_TIFF"
    }
    )
    
    print(f"Download URL: {url}")


    # ---------------------------------------------------------
    # Download file
    # ---------------------------------------------------------

    print("Downloading file...")
    
    outfile = OUTDIR / f"{YEAR}" / f"mapbiomas_c11_{YEAR}_tile{tile['id']:03d}.tif"

    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(outfile, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    print(f"Saved to {outfile}")