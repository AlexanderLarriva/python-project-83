#Makefile
# .PHONY: gendiff

install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run

#build:
#	poetry build

#publish:
#	poetry publish --dry-run

#package-install:
#	python3 -m pip install --user dist/*.whl

check:
	poetry run flake8 .
#	poetry run pytest

# test-coverage:
#	poetry run pytest --cov=gendiff tests/ --cov-report xml

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app
