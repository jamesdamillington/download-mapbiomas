import ee

ee.Initialize(project="ee-jamesmillington-01")

print("Connected")

mb = ee.Image(
    "projects/mapbiomas-public/assets/brazil/lulc/collection11/"
    "mapbiomas_brazil_collection11_coverage_v3"
)

print(mb.bandNames().getInfo()[:5])