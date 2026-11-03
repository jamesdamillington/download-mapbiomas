Scripts to download and manipulate MapBiomas data using the Goole Earth Engine API

Default use is to download Collection 11 land cover data for the Atlantic Forest biome. 

1. [create-tiles.py](https://github.com/jamesdamillington/download-mapbiomas/blob/main/create-tiles.py) creates rectangular tiles around a given geometry. There are output as json.
2. [dowbload-years/py](https://github.com/jamesdamillington/download-mapbiomas/blob/main/download-years.py) uses the json tile definition to create URLS and download tiles to disk, looping over multiple years
3. [mosaic-tiles.py](https://github.com/jamesdamillington/download-mapbiomas/blob/main/mosaic-tiles.py) mosaicks all files in a folder into a single .tif **To Do: loop over multiple years**
4. 
