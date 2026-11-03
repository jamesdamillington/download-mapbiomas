import rasterio
import matplotlib.pyplot as plt

with rasterio.open(
    "outputs/mapbiomas_c11_atlantic_forest_2024.tif"
) as src:

    data = src.read(1)

plt.imshow(data)
plt.colorbar()
plt.show()