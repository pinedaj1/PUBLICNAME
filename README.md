# Project 13 - Vehicle Dependency and Emissions Database

With the push for New Jersey municipalities to be more sustainable, excessive CO2 emissions become a significant problem due to their effect on the environment. A large amount of these emissions come from vehicles. This project seeks to make statewide data collected by Sustainable Jersey easy to analyze as well as easy to compare different datasets to get information about vehicle dependency and use. This repository holds the database and website GUI for the project.


## Usage Instructions

The database and website involves the use of `python` and `postgres15`, as well as several python packages: `flask`, `psycopg2`, `matplotlib`. Make sure these are set up and the dependencies are installed.

The database creation, population, and server deployment can all be done by running `make_database.sh` in a `venv` environment. After running the script, the server will start and can be accessed by going to http://127.0.0.1:5000.

## Databases used

Various databases from the [Sustainable Jersey Data Center](https://www.sustainablejersey.com/resources/data-center/)

Municipality topology data from [NJGIN Open Data](https://njogis-newjersey.opendata.arcgis.com/datasets/newjersey::municipal-boundaries-of-nj)

Topology simplified using [MapShaper](https://mapshaper.org/)


## GUI Screenshots

![alt text](https://github.com/TCNJ-degoodj/cab-project-13/blob/main/screenshots/HomePage.jpg?raw=true)

![alt text](https://github.com/TCNJ-degoodj/cab-project-13/blob/main/screenshots/MunicipalitySearch.jpg?raw=true)

![alt text](https://github.com/TCNJ-degoodj/cab-project-13/blob/main/screenshots/MeansOfTransportation.jpg?raw=true)

![alt text](https://github.com/TCNJ-degoodj/cab-project-13/blob/main/screenshots/OnRoadVehicles.jpg?raw=true)

![alt text](https://github.com/TCNJ-degoodj/cab-project-13/blob/main/screenshots/EVOwnership.jpg?raw=true)

![alt text](https://github.com/TCNJ-degoodj/cab-project-13/blob/main/screenshots/StatewideCO2.jpg?raw=true)

![alt text](https://github.com/TCNJ-degoodj/cab-project-13/blob/main/screenshots/StatewideVehicleComparison.jpg?raw=true)
