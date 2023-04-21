#!/bin/bash
set -e
cd db_scripts
python3 convert.py

database="njdata"
dropdb --if-exists $database
createdb $database
psql -d $database -c "\i initialize_db.sql"
cd -

echo
echo successfully created database called njdata
echo creating web gui...
echo

. run_server.sh
