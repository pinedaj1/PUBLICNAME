import csv

VMT_TYPES = (
    'combination long-haul truck',
    'combination short-haul truck',
    'intercity bus',
    'light commercial trucks',
    'motor home',
    'motorcycles',
    'passenger cars',
    'passenger trucks',
    'refuse truck',
    'school bus',
    'single unit long-haul truck',
    'single unit short-haul truck',
    'transit bus',
)

MOT_TYPES = (
    'car, truck, or van',
    'public transport',
    'taxicab',
    'motorcycle',
    'bicycle',
    'walked',
    'other means',
    'worked at home',
)

def clean_row(row, lower):
    """Clean up entries in a row."""
    return tuple(field.strip().lower() if lower else field.strip() for field in row)

def parse_int(i):
    """Parse an integer with commas."""
    if i == '#n/a':
        return 0
    return int(i.replace(',', ''))

def parse_float(i):
    """Parse a float with commas."""
    return float(i.replace(',', ''))

def import_csv(filename, lower=True):
    """Iterate over the rows."""
    keys = None
    with open(filename) as file:
        for row in csv.reader(file):
            row = clean_row(row, lower)
            if keys is None:
                keys = row
            else:
                yield {keys[i]: row[i] for i in range(len(keys))}

municipalities = {}

def get_mno(name, county):
    """Get the municipality number for a given name and county."""
    key = (name, county)
    if key not in municipalities:
        municipalities[key] = len(municipalities)
    return municipalities[key]

def clean_up_municipality_name(name):
    # capitalize town type, and remove duplicate town type if present
    parts = name.split(' ')
    if len(parts) > 1:
        parts[-1] = parts[-1][0].upper() + parts[-1][1:]
        if parts[-1] == parts[-2]:
            parts.pop()
    return ' '.join(parts)

with open('initialize_db.sql', 'wt') as file:
    print('DROP TABLE means_of_transportation;', file=file)
    print('DROP TABLE on_road_vehicle;', file=file)
    print('DROP TABLE population;', file=file)
    print('DROP TABLE municipality;', file=file)

    print('CREATE TYPE on_road_vehicle_type AS ENUM(', file=file)
    print(','.join("'" + t + "'" for t in VMT_TYPES), file=file)
    print(');', file=file)

    print('CREATE TYPE means_of_transportation_type AS ENUM(', file=file)
    print(','.join("'" + t + "'" for t in MOT_TYPES), file=file)
    print(');', file=file)

    print('CREATE TABLE municipality (', file=file)
    print('MNo SMALLINT,', file=file)
    print('Name VARCHAR(30),', file=file)
    print('County VARCHAR(10),', file=file)
    print('PRIMARY KEY (MNo)', file=file)
    print(');', file=file)

    print('CREATE TABLE population (', file=file)
    print('MNo SMALLINT,', file=file)
    print('Year SMALLINT,', file=file)
    print('Pop INT,', file=file)
    print('CO2 INT,', file=file)
    print('EVs SMALLINT,', file=file)
    print('PersonalVehicles INT,', file=file)
    print('PRIMARY KEY (MNo, Year),', file=file)
    print('FOREIGN KEY (MNo) REFERENCES municipality (MNo)', file=file)
    print(');', file=file)

    print('CREATE TABLE on_road_vehicle (', file=file)
    print('MNo SMALLINT,', file=file)
    print('Year SMALLINT,', file=file)
    print('Type on_road_vehicle_type,', file=file)
    print('CO2 DECIMAL(8,2),', file=file)
    print('Miles INT,', file=file)
    print('PRIMARY KEY (MNo, Year, Type)', file=file)
    print(');', file=file)

    print('CREATE TABLE means_of_transportation (', file=file)
    print('MNo SMALLINT,', file=file)
    print('Year SMALLINT,', file=file)
    print('Type means_of_transportation_type,', file=file)
    print('Percentage DECIMAL(7,3),', file=file)
    print('PRIMARY KEY (MNo, Year, Type),', file=file)
    print('FOREIGN KEY (MNo, Year) REFERENCES population (MNo, Year)', file=file)
    print(');', file=file)

    ev_data = {}
    for entry in import_csv('ev.csv'):
        mno = get_mno(entry['municipality'], entry['county'])
        year = int(entry['year'])
        personal = parse_int(entry['total personal vehicles'])
        count = parse_int(entry['# of evs'])
        ev_data[mno, year] = (personal, count)

    co2_data = {}
    for entry in import_csv('community_ghg.csv'):
        mno = get_mno(entry['municipality'], entry['county'])
        year = int(entry['year'])
        co2_data[mno, year] = parse_int(entry['total mtco2e'])

    # get names of municipalities and counties, properly capitalized
    names = {}
    counties = {}
    for entry in import_csv('ev.csv', lower=False):
        name = entry['Municipality']
        name_key = name.lower()
        name = clean_up_municipality_name(name)
        county = entry['County']
        county_key = county.lower()
        # ensure consistent capitalization
        assert name_key not in names or names[name_key] == name
        assert county_key not in counties or counties[county_key] == county
        # then add
        names[name_key] = name
        counties[county_key] = county

    print('INSERT INTO municipality (MNo, Name, County) VALUES', file=file)
    municipality_values = []
    for (name, county) in municipalities:
        municipality_values.append(f"({municipalities[name, county]}, '{names[name]}', '{counties[county]}')")
    print(',\n'.join(municipality_values) + ';', file=file)

    mot_data = []
    population_values = []
    for entry in import_csv('community.csv'):
        mno = get_mno(entry['municipality'], entry['county'])
        year = int(entry['year'])
        population = parse_int(entry['population'])
        personal, evs = ev_data[mno, year]
        co2 = co2_data[mno, year]
        population_values.append(f'({mno}, {year}, {evs}, {co2}, {population}, {personal})')
        for mot_type in MOT_TYPES:
            percentage = parse_float(entry[mot_type].replace('%', ''))
            mot_data.append(f"({mno}, {year}, '{mot_type}', {percentage})")
    print('INSERT INTO population (MNo, Year, EVs, CO2, Pop, PersonalVehicles) VALUES', file=file)
    print(',\n'.join(population_values) + ';', file=file)
    print(';INSERT INTO means_of_transportation (MNo, Year, Type, Percentage) VALUES', file=file)
    print(',\n'.join(mot_data) + ';', file=file)

    vehicle_values = []
    for (vmt_entry, ghg_entry) in zip(import_csv('vmt.csv'), import_csv('ghg.csv')):
        mno = get_mno(vmt_entry['municipality name'], vmt_entry['county'])
        year = int(vmt_entry['year'])
        for vmt_type in VMT_TYPES:
            miles = vmt_entry[vmt_type]
            # NOTE: there are a few cases where the data is not provided.
            # for each of these cases, we have no data for any type for the given
            # year, so we must not allow comparing data for these cases.
            if miles == 'nda':
                continue
            miles = parse_int(miles)
            co2 = parse_float(ghg_entry[vmt_type])
            vehicle_values.append(f"({mno}, {year}, '{vmt_type}', {co2}, {miles})")
    print('INSERT INTO on_road_vehicle (MNo, Year, Type, CO2, Miles) VALUES', file=file)
    print(',\n'.join(vehicle_values) + ';', file=file)
