# %%
from figurex.figure import Figure, Panel
import matplotlib.pyplot as plt
from figurex.geo.figure import GeoPanel
# %%
# Use gridspec instead: https://stackoverflow.com/questions/74028676/how-to-change-an-existing-normal-axis-to-cartopy-axis-in-different-size-subplots
# Use mosaic but only on init: https://stackoverflow.com/questions/76239866/how-to-combine-3d-projections-with-2d-subplots-and-set-the-width
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
import contextily as ctx
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt

# Scatterplot-Daten generieren
x = np.random.randint(1, 11, size=50)
y = np.random.randint(1, 11, size=50)

# %%

with Figure(size=(8,3), layout=(1,3)):
    with Panel() as ax:
        ax.scatter(x, y)

    # with Panel() as ax:
    #     ax.scatter(x, y)
    print("List:", np.array(plt.gcf().axes))

    with GeoPanel() as ax:
        make_hawaii(ax)

    # with GeoPanel() as ax:
    #     make_hawaii(ax)

    print("List:", np.array(plt.gcf().axes))

    with Panel() as ax:
        ax.scatter(x, y)
    print("List:", np.array(plt.gcf().axes))
    with Panel() as ax:
        ax.scatter(x, y)
    print("List:", np.array(plt.gcf().axes))

# %%
fig, axes = plt.subplots(2,3, figsize=(6,2))
# axes[0].set_title("A")
# axes[1].set_title("B")
# axes[2].set_title("C")
# print("List:", np.array(plt.gcf().axes))
# fig.delaxes(axes[0])
# print("List:", np.array(plt.gcf().axes))
rows, cols, start, stop = fig.get_subplotspec().get_geometry()
axnew = plt.subplot(235, projection=ccrs.PlateCarree()) #rows, cols, start+1
fig.add_axes(axnew)
make_hawaii(axnew)
# print("List:", np.array(plt.gcf().axes))

# %%
fig = plt.figure(figsize=(6,2))
ax1 = fig.add_subplot(1,3,1)
ax2 = fig.add_subplot(1,3,2, projection=ccrs.PlateCarree())
ax3 = fig.add_subplot(1,3,3)
make_hawaii(ax2)

# %%
fig, axes = plt.subplot_mosaic([[0,0,1],[2,3,1]], figsize=(6,2))
rows, cols, start, stop = axes[0].get_subplotspec().get_geometry()
print(rows, cols, start, stop)
rows, cols, start, stop = axes[1].get_subplotspec().get_geometry()
print(rows, cols, start, stop)
rows, cols, start, stop = axes[2].get_subplotspec().get_geometry()
print(rows, cols, start, stop)
rows, cols, start, stop = axes[3].get_subplotspec().get_geometry()
print(rows, cols, start, stop)
ax0 = fig.add_subplot(2, 3, 1)
ax1 = fig.add_subplot(2, 3, 3, projection=ccrs.PlateCarree())
ax2 = fig.add_subplot(2, 3, 4, projection=ccrs.PlateCarree())
ax3 = fig.add_subplot(2, 3, 5)
# start+1
make_hawaii(ax1)
make_hawaii(ax2)

# %%
# import cartopy
def test_geopanel(a=1, b=2):
    with Figure("nix", layout=(3,1)):
        print(plt.gcf().axes[0].get_subplotspec().get_geometry())
        with GeoPanel("Map", projection="flat", tiles="osm", zoom=11) as ax:
            ax.plot([12,12.1],[50,50.1])
        # with Panel("Map") as ax:
        print(plt.gcf().axes[0].get_subplotspec().get_geometry())
        with GeoPanel("_Map_", projection="flat", tiles="osm", zoom=11) as ax:
            ax.plot([12,12.1],[50,50.1])
        
        print(plt.gcf().axes[1].get_subplotspec().get_geometry())
test_geopanel()

# %%
# Geographische Koordinaten von Honolulu, Hawaii
honolulu_coords = (-157.8583, 21.3069)

# Eine GeoDataFrame für den Punkt der Hauptstadt erstellen
geometry = [Point(honolulu_coords)]
gdf = gpd.GeoDataFrame(geometry=geometry, crs="EPSG:4326")

# Erstellen der Figure und der zwei Panels
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))

# Scatterplot im ersten Panel
ax1.scatter(x, y)
ax1.set_title('Scatterplot von zufälligen Zahlen')
ax1.set_xlabel('x')
ax1.set_ylabel('y')

# Geo-Karte im zweiten Panel
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Hawaii filtern
hawaii = world[(world.name == 'United States') & (world.geometry.intersects(gdf.unary_union.buffer(2)))]

# Hawaii plotten
hawaii.plot(ax=ax2, color='none', edgecolor='k')

# Hauptstadt plotten
gdf.plot(ax=ax2, color='red', markersize=100)

# Satellitenkarte hinzufügen
ctx.add_basemap(
    ax2,
    crs=gdf.crs.to_string(),
    source=ctx.providers.Esri.WorldImagery,
    #  source=ctx.providers.OpenStreetMap.Mapnik
    zoom=11
)

# Kreis um die Hauptstadt hinzufügen
circle = plt.Circle(honolulu_coords[::-1], 0.5, color='blue', fill=False, linewidth=2)
ax2.add_artist(circle)

# Achsenbegrenzungen anpassen
ax2.set_xlim(honolulu_coords[0] - 1, honolulu_coords[0] + 1)
ax2.set_ylim(honolulu_coords[1] - 1, honolulu_coords[1] + 1)

# Achsenverhältnis beibehalten
ax2.set_aspect('equal', adjustable='datalim')

ax2.grid(True)
ax2.tick_params(axis='both', which='both', length=5)

# Titel für das zweite Panel
ax2.set_title('Geografische Karte von Hawaii mit Hauptstadt')
# ax2.set_axis_off()

# Abbildung speichern
plt.savefig('figure.png', dpi=300)
plt.show()
# %%
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt


# Scatterplot-Daten generieren
x = np.random.randint(1, 11, size=50)
y = np.random.randint(1, 11, size=50)

# Geographische Koordinaten von Honolulu, Hawaii
honolulu_coords = (-157.8583, 21.3069)

# Eine GeoDataFrame für den Punkt der Hauptstadt erstellen
geometry = [Point(honolulu_coords)]
gdf = gpd.GeoDataFrame(geometry=geometry, crs="EPSG:4326")

# Erstellen der Figure und der zwei Panels
# fig = plt.figure(figsize=(8, 5))
# fig, (ax1, ax2) = plt.subplots(1,2, figsize=(8, 5))
fig, axs = plt.subplot_mosaic([['scatter', 'map']], figsize=(8, 5))
print("List:", np.array(plt.gcf().axes))
# Scatterplot im ersten Panel
# ax1 = fig.add_subplot(1, 2, 1)
ax1 = axs['scatter']
ax1.scatter(x, y)
ax1.set_title('Scatterplot von zufälligen Zahlen')
ax1.set_xlabel('x')
ax1.set_ylabel('y')

# ax2 = fig.add_subplot(1, 2, 2)
# Geo-Karte im zweiten Panel mit Cartopy
# ax2.remove()

# ax2 = fig.add_subplot(1, 2, 2, projection=ccrs.PlateCarree())
# ax2 = fig.add_subplot(axs["map"], projection=ccrs.PlateCarree())
rows, cols, start, stop = axs['map'].get_subplotspec().get_geometry()
# print(rows, cols, start, stop)
ax2 = plt.subplot(rows, cols, start+1, projection=ccrs.PlateCarree())
# axs['map'].remove()  # Entfernt die standardmäßige Achse im Mosaik
fig.add_subplot(ax2)  # Fügt die Cartopy-Achse zum Figure hinzu

print("List:", np.array(plt.gcf().axes))
ax2.set_extent([-158.8583, -156.8583, 20.3069, 22.3069])

# Hinzufügen von Stamen Terrain Basemap
# tiler = Stamen('terrain-background')
tiler = cimgt.GoogleTiles(cache=True, style="satellite")
ax2.add_image(tiler, 8, alpha=0.5)


# Hinzufügen von Land und Ozean
ax2.add_feature(cfeature.LAND)
ax2.add_feature(cfeature.OCEAN)
ax2.add_feature(cfeature.COASTLINE)
ax2.add_feature(cfeature.BORDERS, linestyle=':')

# Hauptstadt plotten
ax2.plot(honolulu_coords[0], honolulu_coords[1], 'ro', markersize=10)

# Kreis um die Hauptstadt hinzufügen
circle = plt.Circle(honolulu_coords[::-1], 0.5, color='blue', fill=False, linewidth=2, transform=ccrs.Geodetic())
ax2.add_patch(circle)

# Titel für das zweite Panel
ax2.set_title('Geografische Karte von Hawaii mit Hauptstadt')

# Gitter und Ticks hinzufügen
ax2.gridlines(draw_labels=True)

# Achsenbegrenzungen anpassen
ax2.set_xlim(honolulu_coords[0] - 1, honolulu_coords[0] + 1)
ax2.set_ylim(honolulu_coords[1] - 1, honolulu_coords[1] + 1)

# Achsenverhältnis beibehalten
ax2.set_aspect('equal', adjustable='datalim')

# Abbildung speichern
plt.savefig('figure_cartopy.png', dpi=300)
plt.show()


# %%
ax2 = Figure.get_next_axis()
ax2.remove()
ax2 = fig.add_subplot(1, 2, 2, projection=ccrs.PlateCarree())
ax2.set_extent([-158.8583, -156.8583, 20.3069, 22.3069])

tiler = cimgt.GoogleTiles(cache=True, style="satellite")
ax2.add_image(tiler, 8, alpha=0.5)
ax2.add_feature(cfeature.LAND)
ax2.add_feature(cfeature.OCEAN)
ax2.add_feature(cfeature.COASTLINE)
ax2.add_feature(cfeature.BORDERS, linestyle=':')

# Hauptstadt plotten
ax2.plot(honolulu_coords[0], honolulu_coords[1], 'ro', markersize=10)

# Kreis um die Hauptstadt hinzufügen
circle = plt.Circle(honolulu_coords[::-1], 0.5, color='blue', fill=False, linewidth=2, transform=ccrs.Geodetic())
ax2.add_patch(circle)

# Titel für das zweite Panel
ax2.set_title('Geografische Karte von Hawaii mit Hauptstadt')
ax2.gridlines(draw_labels=True)

# Achsenbegrenzungen anpassen
ax2.set_xlim(honolulu_coords[0] - 1, honolulu_coords[0] + 1)
ax2.set_ylim(honolulu_coords[1] - 1, honolulu_coords[1] + 1)

# Achsenverhältnis beibehalten
ax2.set_aspect('equal', adjustable='datalim')

# %%

# %%
def make_hawaii(ax2):
    # Geographische Koordinaten von Honolulu, Hawaii
    honolulu_coords = (-157.8583, 21.3069)

    # Eine GeoDataFrame für den Punkt der Hauptstadt erstellen
    geometry = [Point(honolulu_coords)]
    gdf = gpd.GeoDataFrame(geometry=geometry, crs="EPSG:4326")
    ax2.set_extent([-158.8583, -156.8583, 20.3069, 22.3069])

    tiler = cimgt.GoogleTiles(cache=True, style="satellite")
    ax2.add_image(tiler, 8, alpha=0.5)
    ax2.add_feature(cfeature.LAND)
    ax2.add_feature(cfeature.OCEAN)
    ax2.add_feature(cfeature.COASTLINE)
    ax2.add_feature(cfeature.BORDERS, linestyle=':')

    # Hauptstadt plotten
    ax2.plot(honolulu_coords[0], honolulu_coords[1], 'ro', markersize=10)

    # Kreis um die Hauptstadt hinzufügen
    circle = plt.Circle(honolulu_coords[::-1], 0.5, color='blue', fill=False, linewidth=2, transform=ccrs.Geodetic())
    ax2.add_patch(circle)

    # Titel für das zweite Panel
    ax2.set_title('Geografische Karte von Hawaii mit Hauptstadt')
    ax2.gridlines(draw_labels=True)

    # Achsenbegrenzungen anpassen
    ax2.set_xlim(honolulu_coords[0] - 1, honolulu_coords[0] + 1)
    ax2.set_ylim(honolulu_coords[1] - 1, honolulu_coords[1] + 1)

    # Achsenverhältnis beibehalten
    ax2.set_aspect('equal', adjustable='datalim')
# %%
