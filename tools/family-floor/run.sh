#!/bin/sh
# Rebuild the family floor data and write it into index.html. Needs: pip install policyengine-us openpyxl numpy
set -e
cd "$(dirname "$0")"
python3 fetch.py ../../index.html
python3 pe_grid.py $(cat raw/pe_counties.txt)
python3 inputs.py
python3 budget.py
python3 pack.py ../../index.html
