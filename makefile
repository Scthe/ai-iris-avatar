# source .venv/Scripts/Activate

pip-freeze:
	pip freeze > requirements.txt

pip-install:
	pip install -r requirements.txt

help:
	python.exe main.py --help

serve:
	python.exe main.py serve

serve-xtts:
	python.exe main.py serve --config "config_xtts.yaml"
