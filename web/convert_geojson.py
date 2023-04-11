# Converts the official geojson into a format more suited for our database.
# The database server must be running.

import json

import psycopg2
from config import config

def connect(query):
    params = config()
    with psycopg2.connect(**params) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()

with open('municipalities.json') as file:
    original = json.load(file)

features = []

# get our own municipality table
municipalities = {(name.lower(), county.lower()): mno for (mno, name, county) in connect('select * from municipality;')}
used_mno = set()

for feature in original['features']:
    properties = feature['properties']
    try:
        mno = municipalities[properties['NAME'].lower(), properties['COUNTY'].lower()]
    except KeyError:
        try:
            mno = municipalities[properties['NAME'].lower() + ' ' + properties['MUN_TYPE'].lower(), properties['COUNTY'].lower()]
        except KeyError:
            # only one we fail to match is peapack-gladstone
            assert properties['NAME'] == 'Peapack-Gladstone Borough'
            mno = municipalities['peapack and gladstone borough', 'somerset']
    assert mno not in used_mno
    used_mno.add(mno)
    features.append({
        'type': 'Feature',
        'properties': { 'mno': mno },
        'geometry': feature['geometry'],
    })

result = {
    'type': 'FeatureCollection',
    'name': 'Municipalities',
    'features': features,
}

with open('templates/geometry.json', 'w') as file:
    json.dump(result, file)
