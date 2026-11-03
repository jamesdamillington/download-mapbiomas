#creates a list of rectangular Earth Engine tiles covering the atlantic forest biome
#saves the tile metadata to a JSON file for use by download-years.py

from pathlib import Path
import ee
import json

# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------

PROJECT_ID = "ee-jamesmillington-01"

OUTDIR = Path("~/projects/mapbiomas/verena/outputs").expanduser()
OUTDIR.mkdir(exist_ok=True)

YEAR = 2024

# --------------------------------------------------------- 
# functions
# ---------------------------------------------------------
def make_tiles(geometry, dx=1.33, dy=1.33):
    """
    Create a list of rectangular Earth Engine tiles covering a geometry.

    Parameters
    ----------
    geometry : ee.Geometry
        Geometry to be tiled (e.g. the Atlantic Forest biome).

    dx : float
        Tile width in decimal degrees.

    dy : float
        Tile height in decimal degrees.

    Returns
    -------
    list of dict
        Each dictionary contains:
            id        : unique tile identifier
            geometry  : ee.Geometry.Rectangle
            xmin      : tile western boundary
            ymin      : tile southern boundary
            xmax      : tile eastern boundary
            ymax      : tile northern boundary
    """

    # ------------------------------------------------------------------
    # Get a rectangular bounding box around the input geometry.
    # This is easier to tile than the irregular biome shape itself.
    # ------------------------------------------------------------------

    bounds = geometry.bounds()

    # Earth Engine returns rectangle coordinates as:
    #
    # [
    #   [xmin, ymin],
    #   [xmin, ymax],
    #   [xmax, ymax],
    #   [xmax, ymin],
    #   [xmin, ymin]
    # ]
    #
    coords = bounds.coordinates().getInfo()[0]

    xmin = coords[0][0]
    ymin = coords[0][1]
    xmax = coords[2][0]
    ymax = coords[2][1]

    tiles = []
    tile_id = 0

    # ------------------------------------------------------------------
    # Step through the bounding box in columns (x direction)
    # and rows (y direction).
    # ------------------------------------------------------------------

    x = xmin

    while x < xmax:

        y = ymin

        while y < ymax:

            # ----------------------------------------------------------
            # Create one rectangular tile.
            #
            # min(...) prevents the final row/column of tiles
            # extending beyond the bounding box.
            # ----------------------------------------------------------

            print(f"Creating tile {tile_id} at ({x}, {y})")
            tile_geom = ee.Geometry.Rectangle(
                [
                    x,
                    y,
                    min(x + dx, xmax),
                    min(y + dy, ymax)
                ]
            )

            # ----------------------------------------------------------
            # Keep only tiles that intersect the target geometry.
            #
            # This avoids downloading large numbers of empty tiles
            # outside the biome.
            # ----------------------------------------------------------

            intersects = tile_geom.intersects(
                geometry,
                maxError=1
            ).getInfo()

            print(f"Tile {tile_id} intersects geometry: {intersects}")

            if intersects:
                tiles.append(
                    {
                        "id": tile_id,
                        "geometry": tile_geom,
                        "xmin": x,
                        "ymin": y,
                        "xmax": min(x + dx, xmax),
                        "ymax": min(y + dy, ymax)
                    }
                )

                tile_id += 1

            y += dy

        x += dx

    return tiles


# ---------------------------------------------------------
# Initialize Earth Engine
# ---------------------------------------------------------

ee.Initialize(project=PROJECT_ID)

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

tiles = make_tiles(geom, dx=1.33, dy=1.33)
print(f"Created {len(tiles)} tiles covering the Atlantic Forest biome.")

tile_metadata = []

for tile in tiles:
    tile_metadata.append({
        "id": tile["id"],
        "xmin": tile["xmin"],
        "ymin": tile["ymin"],
        "xmax": tile["xmax"],
        "ymax": tile["ymax"]
    })

print("writing tile metadata to JSON file...")
outfile = OUTDIR / "AF-tiles.json"

with open(outfile, "w") as f:
    json.dump(tile_metadata, f, indent=2)
