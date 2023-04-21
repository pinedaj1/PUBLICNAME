#! /usr/bin/python3

"""
This is an example Flask | Python | Psycopg2 | PostgreSQL
application that connects to the 7dbs database from Chapter 2 of
_Seven Databases in Seven Weeks Second Edition_
by Luc Perkins with Eric Redmond and Jim R. Wilson.
The CSC 315 Virtual Machine is assumed.

John DeGood
degoodj@tcnj.edu
The College of New Jersey
Spring 2020

----

One-Time Installation

You must perform this one-time installation in the CSC 315 VM:

# install python pip and psycopg2 packages
sudo pacman -Syu
sudo pacman -S python-pip python-psycopg2

# install flask
pip install flask

----

Usage

To run the Flask application, simply execute:

export FLASK_APP=app.py 
flask run
# then browse to http://127.0.0.1:5000/

----

References

Flask documentation:  
https://flask.palletsprojects.com/  

Psycopg documentation:
https://www.psycopg.org/

This example code is derived from:
https://www.postgresqltutorial.com/postgresql-python/
https://scoutapm.com/blog/python-flask-tutorial-getting-started-with-flask
https://www.geeksforgeeks.org/python-using-for-loop-in-flask/
"""

import json
import psycopg2
import matplotlib
import matplotlib.pyplot as plt
import multiprocessing as mp
import numpy as np
from base64 import b64encode
from collections import namedtuple
from config import config
from flask import Flask, render_template, request, Response
from io import BytesIO
from flask import redirect
import os

matplotlib.use('agg')

# Connect to the PostgreSQL database server
def connect(query):
    conn = None
    try:
        # read connection parameters
        params = config()
 
        # connect to the PostgreSQL server
        print('Connecting to the %s database...' % (params['database']))
        conn = psycopg2.connect(**params)
        print('Connected.')
      
        # create a cursor
        cur = conn.cursor()
        
        # execute a query using fetchall()
        cur.execute(query)
        rows = cur.fetchall()

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
    # return the query result from fetchall()
    return rows
 
# app.py
app = Flask(__name__)

def name_and_county(mno):
    # sanitize inputs!
    mno = int(mno)
    # make query
    return tuple(connect(f'SELECT name, county FROM municipality WHERE mno = {mno};')[0])

def render_plot():
    fig = plt.gcf()
    f = BytesIO()
    fig.savefig(f, format='png')
    f.seek(0)
    return b64encode(f.getbuffer()).decode()

def get_sql_enum(name):
    return [row[0] for row in connect(f'SELECT UNNEST(ENUM_RANGE(NULL::{name}));')]

MOT_ENUM = get_sql_enum('means_of_transportation_type')

class YearTable:
    def __init__(self, columns, table, mno):
        self.header = ['Year'] + list(columns)
        self.rows = connect(f'SELECT year, {", ".join(columns)} FROM {table} WHERE mno = {mno};')

    def bar_chart(self, title, id, calculation, queue):
        # run in separate process because matplotlib leaks memory with repeated use
        years = [row[0] for row in self.rows]
        rows = [calculation(row[1:]) for row in self.rows]
        def worker():
            plt.cla()
            plt.clf()
            bar_chart(title, years, [''], rows)
            queue.put((id, render_plot()))
        proc = mp.Process(target=worker)
        proc.start()
        return proc

class TypedYearTable(YearTable):
    def __init__(self, column, table, mno):
        super().__init__(['Type', column], table, mno)
        self.types = get_sql_enum(table + '_type')
        self.header = ['Year'] + self.types
        year_rows = {}
        for year, type, value in self.rows:
            if year not in year_rows:
                year_rows[year] = [year] + [None for _ in range(len(self.types))]
            year_rows[year][self.types.index(type) + 1] = value
        self.rows = sorted(year_rows.values())

    def bar_chart(self, title, id, queue):
        # run in separate process because matplotlib leaks memory with repeated use
        years = [row[0] for row in self.rows]
        types = self.types
        rows = [row[1:] for row in self.rows]
        def worker():
            plt.cla()
            plt.clf()
            bar_chart(title, years, types, rows)
            queue.put((id, render_plot()))
        proc = mp.Process(target=worker)
        proc.start()
        return proc

def bar_chart(title, years, types, rows):
    plt.figure(figsize=(8, 8))
    plt.subplots_adjust(bottom=0.3)
    indices = np.arange(len(types))

    width = 1.0 / len(years)
    offset = -0.5 + 0.5 * width
    for year, row in zip(years, rows):
        plt.bar(indices + offset, row, width, label=year)
        offset += width

    plt.title(title)
    plt.xticks(indices, types, rotation=90)

    plt.gca().ticklabel_format(style='plain', axis='y')

    plt.legend(years)

@app.route('/municipality', methods=['POST'])
def municipality():
    mno = int(request.form['mno'])
    name, county = name_and_county(mno)
    # check which years are supported for on_road_vehicle
    have_vmt = len(connect(f'SELECT DISTINCT year FROM on_road_vehicle WHERE mno = {mno};')) > 0
    return render_template('municipality.html', mno=mno, name=name, county=county, have_vmt=have_vmt)

Municipality = namedtuple('Municipality', ('mno', 'name', 'county'))

@app.route('/')
def home():
    municipalities = [Municipality(*row) for row in connect('SELECT mno, name, county FROM municipality;')]
    types = [{'index': i, 'name': v } for i, v in enumerate(MOT_ENUM)]
    return render_template('index.html', municipalities=municipalities, types=types)

@app.route('/mot', methods=['POST'])
def mot():
    mno = int(request.form['mno'])
    name, county = name_and_county(mno)
    year_table = TypedYearTable('Percentage', 'means_of_transportation', mno)
    queue = mp.Queue()
    proc = year_table.bar_chart('Percentage of Total Means of Transportation', '', queue)
    _, chart = queue.get()
    proc.join()
    return render_template('mot.html', mno=mno, name=name, county=county, chart=chart, year_table=year_table)

@app.route('/vmt', methods=['POST'])
def vmt():
    mno = int(request.form['mno'])
    name, county = name_and_county(mno)
    miles_year_table = TypedYearTable('Miles', 'on_road_vehicle', mno)
    if len(miles_year_table.rows) == 0:
        return Response(status=400)
    co2_year_table = TypedYearTable('CO2', 'on_road_vehicle', mno)
    queue = mp.Queue()
    miles_proc = miles_year_table.bar_chart('Miles Traveled by On-road Vehicles', 'miles', queue)
    co2_proc = co2_year_table.bar_chart('CO2 Emissions in Tons by On-road Vehicles', 'co2', queue)
    id1, chart1 = queue.get()
    id2, chart2 = queue.get()
    miles_chart = chart1 if id1 == 'miles' else chart2
    co2_chart = chart2 if id2 == 'co2' else chart1
    miles_proc.join()
    co2_proc.join()
    return render_template('vmt.html', mno=mno, name=name, county=county, miles_year_table=miles_year_table, miles_chart=miles_chart, co2_year_table=co2_year_table,co2_chart=co2_chart)

@app.route('/ev', methods=['POST'])
def ev():
    mno = int(request.form['mno'])
    name, county = name_and_county(mno)
    year_table = YearTable(["EVs", "PersonalVehicles", "Pop", "CO2"], "population", mno)
    queue = mp.Queue()
    ev_percentage_proc = year_table.bar_chart('Percentage of EVs out of Personal Vehicles', 'ev_percentage', lambda row: 100 * (row[0] / row[1]), queue)
    id1, chart1 = queue.get()
    per_person_proc = year_table.bar_chart('Number of Vehicles per Person', 'per_person', lambda row: (row[1] / row[2]), queue)
    id2, chart2 = queue.get()
    ev_percentage_chart = chart1 if id1 == 'ev_percentage' else chart2
    per_person_chart = chart2 if id2 == 'per_person' else chart1
    ev_percentage_proc.join()
    per_person_proc.join()
    return render_template('ev.html', mno=mno, name=name, county=county, year_table=year_table, ev_percentage_chart=ev_percentage_chart, per_person_chart=per_person_chart)

@app.route('/ghg', methods=['POST'])
def ghg():
    year = int(request.form['year'])
    return render_template('map.html', query_path=f'/ghg.json?year={year}', color_map='heatmap', display_type='co2', title=f'CO₂ emissions in {year}')

@app.route('/mot2', methods=['POST'])
def mot2():
    year = int(request.form['year'])
    t1 = int(request.form['t1'])
    t2 = int(request.form['t2'])
    # validate range
    if t1 >= len(MOT_ENUM) or t1 < 0 or t2 >= len(MOT_ENUM) or t2 < 0:
        return Response(status=400)
    return render_template(
        'map.html',
        query_path=f'/mot.json?year={year}&t1={t1}&t2={t2}',
        color_map='diverging',
        display_type='mot',
        t1=MOT_ENUM[t1],
        t2=MOT_ENUM[t2],
        title=f'Compare {MOT_ENUM[t1]} to {MOT_ENUM[t2]} in {year}',
    )

@app.route('/population.json', methods=['GET'])
def population_handler():
    # cast year to int to avoid injection
    year = int(request.args.get('year'))
    return json.dumps({i[0]: i[1] for i in connect(f'SELECT mno, pop FROM population WHERE year = {year};')})

@app.route('/ghg.json', methods=['GET'])
def ghg_json():
    # cast year to int to avoid injection
    year = int(request.args.get('year'))
    return json.dumps({i[0]: i[1] for i in connect(f'SELECT mno, co2 FROM population WHERE year = {year};')})

@app.route('/mot.json', methods=['GET'])
def mot_json():
    # cast year to int to avoid injection
    year = int(request.args.get('year'))
    t1 = int(request.args.get('t1'))
    t2 = int(request.args.get('t2'))
    # validate range
    if t1 >= len(MOT_ENUM) or t1 < 0 or t2 >= len(MOT_ENUM) or t2 < 0:
        return Response(status=400)
    # comparison algorithm: 0 for all t1, 1 for all t2
    t1_values = connect(f"SELECT mno, percentage FROM means_of_transportation WHERE year = {year} AND type = '{MOT_ENUM[t1]}' ORDER BY mno;")
    t2_values = connect(f"SELECT mno, percentage FROM means_of_transportation WHERE year = {year} AND type = '{MOT_ENUM[t2]}' ORDER BY mno;")
    result = {}
    for t1_row, t2_row in zip(t1_values, t2_values):
        t1_mno, t1_percentage = t1_row
        t2_mno, t2_percentage = t2_row
        # should be guaranteed by ORDER BY
        assert t1_mno == t2_mno
        result[t1_mno] = ((float(t1_percentage) - float(t2_percentage)) + 100.0) / 200.0
    return json.dumps(result)

@app.route('/transportation.json', methods=['GET'])
def transportation_handler():
    # cast year to int to avoid injection
    year = int(request.args.get('year'))
    # for now, this one is hardcoded for working from home percentage
    return json.dumps({i[0]: float(i[1]) for i in connect(f"SELECT mno, percentage FROM means_of_transportation WHERE year = {year} and type = 'worked at home';")})

@app.route('/names.json', methods=['GET'])
def names_handler():
    # get data from database
    return json.dumps({i[0]: { 'name': i[1], 'county': i[2] } for i in connect(f'SELECT * FROM municipality;')})


@app.route("/redirectURL", methods=["GET"])
def redirectURL():
    return redirect("https://www.sustainablejersey.com/resources/data-center/sustainable-jersey-data-resources/", code=302)

if __name__ == '__main__':
    port = int(os.environment.get('PORT', 5000))
    app.run(debug = True, host='0.0.0.0', port=port)

