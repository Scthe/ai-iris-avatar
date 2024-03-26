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


# ------------- CNN STYLE TRANSFER:
gen-samples:
	python.exe main.py st-generate-samples -64 --count 300 -i "style_transfer_cnn/images_raw"

train-64:
	python.exe main.py st-train -e 1500 -n -i "style_transfer_cnn/samples_gen_64_2" --test-image "style_transfer_cnn/images_raw/input.unity.png"

st-test:
	python.exe main.py st-test --cpu -i "style_transfer_cnn/images_raw/input.unity.png"

