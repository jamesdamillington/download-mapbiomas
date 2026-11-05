#downloads MapBiomas Collection 11 land cover classification rasters 
#for tiles created by create-tiles.py

from pathlib import Path
import ee
import requests
import json
import time

# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------

PROJECT_ID = "ee-jamesmillington-01"

OUTDIR = Path("outputs").expanduser()
OUTDIR.mkdir(exist_ok=True)

years = list(range(1985, 2026))

# ---------------------------------------------------------
# Retry configuration for handling transient server errors
# ---------------------------------------------------------

MAX_RETRIES = 4
INITIAL_WAIT = 2  # seconds
MAX_WAIT = 32     # seconds
REQUEST_TIMEOUT = (30, 300)  # (connect, read) seconds; read is long as Earth Engine builds the file before sending
MAX_READ_TIMEOUT = 1200      # seconds; cap for the read timeout, which doubles after each ReadTimeout

# ---------------------------------------------------------
# Initialize Earth Engine
# ---------------------------------------------------------

ee.Initialize(project=PROJECT_ID)

# ---------------------------------------------------------
# Read tile metadata from JSON file (created by the script "create-tiles.py")
# ---------------------------------------------------------
infile = OUTDIR / "AF-tiles.json"
with open(infile) as f:
    tile_metadata = json.load(f)

tiles = []

for tile in tile_metadata:

    # Convert each tile's bounding box into an Earth Engine geometry
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
# Helper function for retrying downloads with exponential backoff
# ---------------------------------------------------------

def download_with_retry(url_generator, outfile, max_retries=MAX_RETRIES, initial_wait=INITIAL_WAIT):
    """
    Download file with exponential backoff retry logic.
    Regenerates URL on each attempt in case it expires.
    
    Args:
        url_generator: callable that returns a fresh download URL
        outfile: path where file will be saved
        max_retries: maximum number of retry attempts
        initial_wait: initial wait time in seconds between retries
    
    Returns True if successful, False if all retries exhausted.
    """
    wait_time = initial_wait
    connect_timeout, read_timeout = REQUEST_TIMEOUT
    
    for attempt in range(1, max_retries + 1):
        try:
            url = url_generator()
            response = requests.get(url, stream=True, timeout=(connect_timeout, read_timeout))
            response.raise_for_status()
            
            # Write to a temporary file so interrupted downloads aren't mistaken for complete ones
            tmpfile = Path(f"{outfile}.part")
            with open(tmpfile, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
            tmpfile.replace(outfile)
            
            print(f"  Download successful (attempt {attempt}/{max_retries})")
            return True
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            # Only server-side/rate-limit errors are worth retrying
            is_transient = status_code in (429, 500, 502, 503, 504)
            
            if is_transient and attempt < max_retries:
                print(f"  Attempt {attempt}/{max_retries} failed with HTTP {status_code}. "
                      f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
                wait_time = min(wait_time * 2, MAX_WAIT)
                continue
            else:
                print(f"  Failed with HTTP {status_code}: {e}")
                return False
                
        except requests.exceptions.ReadTimeout:
            # Earth Engine was still building the file: retry with a longer read timeout
            if attempt < max_retries:
                read_timeout = min(read_timeout * 2, MAX_READ_TIMEOUT)
                print(f"  Attempt {attempt}/{max_retries} timed out. "
                      f"Retrying in {wait_time}s with read timeout {read_timeout}s...")
                time.sleep(wait_time)
                wait_time = min(wait_time * 2, MAX_WAIT)
                continue
            else:
                print("  Failed: read timed out")
                return False

        except requests.exceptions.RequestException as e:
            # Network-level errors (timeouts, connection resets) are retried too
            if attempt < max_retries:
                print(f"  Attempt {attempt}/{max_retries} failed with {type(e).__name__}. "
                      f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
                wait_time = min(wait_time * 2, MAX_WAIT)
                continue
            else:
                print(f"  Failed: {e}")
                return False
    
    return False


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
# Loop over years
# ---------------------------------------------------------

for year in years:

    # Select the year's band, clip to the biome and cast to byte to reduce file size
    image = (
        mb.select(f"classification_{year}")
          .clip(geom)
      .toByte()
    )


    # ---------------------------------------------------------
    # Loop over tiles
    # ---------------------------------------------------------

    for tile in tiles: 

        print(f"Processing year {year}...")
        print(f"Processing tile {tile['id']:03d}...")
        print(f"Tile bounds: {tile['xmin']}, {tile['ymin']}, {tile['xmax']}, {tile['ymax']}")
        
        YEARDIR = OUTDIR / str(year)
        
        YEARDIR.mkdir(
            parents=True,
            exist_ok=True
        )
        
        outfile = YEARDIR / f"mapbiomas_c11_{year}_tile{tile['id']:03d}.tif"

        # Skip tiles already downloaded (checked before any Earth Engine request)
        if outfile.exists():
            print(f"Tile {tile['id']:03d} already downloaded, skipping: {outfile}")
            continue

        # URL is generated inside download_with_retry, once per attempt
        def get_url():
            return image.getDownloadURL(
                {
                    "region": tile["geometry"],
                    "scale": 30,
                    "format": "GEO_TIFF"
                }
            )

        # ---------------------------------------------------------
        # Download file
        # ---------------------------------------------------------

        print("Downloading file...")

        if download_with_retry(get_url, outfile):
            print(f"Saved to {outfile}")
        else:
            print(f"ERROR: Could not download tile {tile['id']:03d} for year {year} after {MAX_RETRIES} attempts. Skipping...")
