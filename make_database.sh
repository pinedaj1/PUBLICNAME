#!/bin/bash
set -e
cd db_scripts
python3 convert.py
echo SQL file is at db_scripts/initialize_db.sql
