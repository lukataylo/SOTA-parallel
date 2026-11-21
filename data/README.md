# Data

Study area: Blackfriars Road at Southwark station, London (centre 51.5040 N, 0.1050 W).

| File | Contents |
|---|---|
| `blackfriars_512.npz` | 512 x 512 m crop at 1 m. Arrays: `dtm` (ground height, m AOD), `dsm` (first-return surface height), `buildings` (0/1 from OpenStreetMap), `rail` (0/1 railway lines), `osm_entrances_colrow` (column, row of mapped entrances). |
| `blackfriars_1024.npz` | Same arrays for a 1024 x 1024 m crop with the same centre, for upstream catchment context. |
| `*.meta.json` | Bounds in British National Grid (EPSG:27700), value ranges, coverage figures. Row 0 is the north edge. |
| `blackfriars_512_preview.png` | Ground height, surface minus ground, and building/railway masks. |

## Things to know before using it

- **The DTM is bare earth.** Buildings are removed and the ground under them is interpolated. Some footprints show pits about 2 m deep. Treat building cells as walls using the `buildings` mask, or those pits swallow the flood.
- **Railway viaducts cross the area** (east-west through the middle, and diagonally in the north-east). The DTM passes under them, which is right for surface water, but the ground there is interpolated.
- **The terrain is very flat.** 98% of the 512 m crop lies between 1.99 and 5.06 m AOD.
- **Only 15 entrances are mapped** in the 512 m crop, so receptors need generating along building edges.
- **No usable rainfall record.** `raw/openmeteo_july2021.json` is a coarse reanalysis that peaks at 5 mm/h for July 2021, far below what gauges recorded in those storms. Use design storms with stated assumptions.

## Sources and licence

- Environment Agency LIDAR Composite 2022, 1 m DTM and first-return DSM, tiles TQ3075 and TQ3080. Open Government Licence v3.0.
- OpenStreetMap contributors, via Overpass. ODbL.
- A 0.5 m DTM from 2012 also exists for both tiles (`lidar_tiles_dtm/2012/0.5`) and is not downloaded.

## Rebuilding

Raw downloads live in `data/raw/` and are not committed (about 270 MB zipped). Tile URLs follow
`https://environment.data.gov.uk/tiles/collections/survey/{product}/2022/1/{TQ3075|TQ3080}`.
Then run `uv run --with rasterio --with pyproj --with numpy --with matplotlib python scripts/prepare_data.py`.
