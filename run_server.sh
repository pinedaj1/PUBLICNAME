#!/bin/bash

set -e

cd web
export FLASK_APP=app.py
exec flask run
