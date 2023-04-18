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
import numpy as np
from base64 import b64encode
from collections import namedtuple
from config import config
from flask import Flask, render_template, request, Response
from io import BytesIO

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

class YearTable:
    def __init__(self, columns, table, mno):
        self.header = ['Year'] + list(columns)
        self.rows = connect(f'SELECT year, {", ".join(columns)} FROM {table} WHERE mno = {mno};')

class TypedYearTable(YearTable):
    def __init__(self, column, table, mno):
        super().__init__(['Type', column], table, mno)
        self.types = [row[0] for row in connect(f'SELECT UNNEST(ENUM_RANGE(NULL::{table}_type));')]
        self.header = ['Year'] + self.types
        year_rows = {}
        for year, type, value in self.rows:
            if year not in year_rows:
                year_rows[year] = [year] + [None for _ in range(len(self.types))]
            year_rows[year][self.types.index(type) + 1] = value
        self.rows = sorted(year_rows.values())

    def bar_chart(self, title):
        plt.cla()
        plt.clf()
        bar_chart(title, [row[0] for row in self.rows], self.types, [row[1:] for row in self.rows])
        return render_plot()

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

    yticks, _ = plt.yticks()
    plt.yticks(yticks, ['%.2f' % tick if (int(tick) != tick) else '%d' % tick for tick in yticks])

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
    return render_template('index.html', municipalities=municipalities)

@app.route('/mot', methods=['POST'])
def mot():
    mno = int(request.form['mno'])
    name, county = name_and_county(mno)
    year_table = TypedYearTable('Percentage', 'means_of_transportation', mno)
    chart = year_table.bar_chart('Percentage of Total Means of Transportation')
    return render_template('mot.html', name=name, county=county, chart=chart, year_table=year_table)

@app.route('/vmt', methods=['POST'])
def vmt():
    mno = int(request.form['mno'])
    name, county = name_and_county(mno)
    miles_year_table = TypedYearTable('Miles', 'on_road_vehicle', mno)
    if len(miles_year_table.rows) == 0:
        return Response(status=400)
    miles_chart = miles_year_table.bar_chart('Miles Traveled by On-road Vehicles',)
    co2_year_table = TypedYearTable('CO2', 'on_road_vehicle', mno)
    co2_chart = co2_year_table.bar_chart('CO2 Emissions in Tons by On-road Vehicles',)
    return render_template('vmt.html', name=name, county=county, miles_year_table=miles_year_table, miles_chart=miles_chart, co2_year_table=co2_year_table,co2_chart=co2_chart)

@app.route('/ev', methods=['POST'])
def ev():
    mno = int(request.form['mno'])
    name, county = name_and_county(mno)
    year = int(request.form['year'])
    evs, personal, pop = connect(f'SELECT evs, personalvehicles, pop FROM population WHERE mno = {mno} AND year = {year};')[0]
    return render_template('ev.html', name=name, county=county, year=year, evs=evs, personal=personal, pop=pop)

@app.route('/ghg', methods=['POST'])
def ghg():
    year = int(request.form['year'])
    return render_template('map.html', query_path=f'/ghg.json?year={year}')

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

if __name__ == '__main__':
    app.run(debug = True)
