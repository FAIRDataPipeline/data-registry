#!/bin/bash
cd ..

find . -path '*/migrations/*.py*' -not -path './venv/*' -not -name '__init__.py' -delete
if [ -f "db.sqlite3" ]; then
    rm db.sqlite3
fi

python3 manage.py makemigrations custom_user
python3 manage.py makemigrations data_management
python3 manage.py migrate
python3 manage.py graph_models data_management --arrow-shape crow -X "BaseModel,DataObject,DataObjectVersion" -E -o schema.dot
python3 manage.py collectstatic --noinput > /dev/null 2>&1
python3 manage.py createsuperuser --noinput
python3 manage.py set_site_info

if command -v dot &> /dev/null
then
    dot schema.dot -Tsvg -o static/images/schema.svg
fi
