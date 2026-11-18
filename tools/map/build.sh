#!/bin/sh
# Rebuild us-counties.json: Census 2023 cartographic county boundaries (1:5,000,000), simplified, as TopoJSON,
# with each county tagged by its 2023 CBSA (metro or micro area) code from the Census delineation file.
# Needs: npm i mapshaper; python3 with openpyxl. Run from this folder.
set -e
mkdir -p raw && cd raw
curl -sSLO https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_5m.zip && unzip -oq cb_2023_us_county_5m.zip
curl -sSL -o list1.xlsx https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx
npx mapshaper cb_2023_us_county_5m.shp -filter '!["60","66","69","72","78"].includes(STATEFP)' -each 'g=GEOID, n=NAMELSAD+", "+STUSPS' \
  -filter-fields g,n -simplify 7% keep-shapes -o format=topojson quantization=20000 counties.json
python3 - <<'PY'
import json, openpyxl
ws = openpyxl.load_workbook('list1.xlsx', read_only=True).active
m = {str(r[9]).zfill(2) + str(r[10]).zfill(3): str(r[0]) for i, r in enumerate(ws.iter_rows(values_only=True)) if i >= 3 and r[0] and r[9]}
t = json.load(open('counties.json')); o = list(t['objects'].values())[0]
for g in o['geometries']:
    k = m.get(g['properties']['g'])
    if k: g['properties']['k'] = k
t['objects'] = {'c': o}
json.dump(t, open('../../../us-counties.json', 'w'), separators=(',', ':'))
print(len(o['geometries']), 'counties')
PY
