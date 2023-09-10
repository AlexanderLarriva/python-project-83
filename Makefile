#Makefile
# .PHONY: gendiff

install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run

build:
	./build.sh

check:
	poetry run flake8 .
#	poetry run pytest

# test-coverage:
#	poetry run pytest --cov=gendiff tests/ --cov-report xml

flask-start:
	poetry run flask --app page_analyzer.app --debug run --port 8000

PORT ?= 8000
start:
	poetry run gunicorn --workers=5 --bind=0.0.0.0:$(PORT) page_analyzer.app:app
