# source .venv/Scripts/Activate

pip-freeze:
	pip freeze > requirements.txt

pip-install:
	pip install -r requirements.txt

help:
	python.exe main.py --help

serve:
	python.exe main.py serve --config "config_xtts.yaml"

serve-simple:
	python.exe main.py serve

# ------------- CURL PROMPT:
curl_prompt_get:
	curl "http://localhost:8080/prompt?value=Who%20is%20Michael%20Jordan%3F"

curl_prompt_post:
	curl --request POST --header "Content-Type: application/json" --data "{\"value\":\"Who is Michael Jordan?\"}" "http://localhost:8080/prompt"
  

# ------------- TTS UTILS:
tts-list-models:
	tts --list_models

# xtts_v2
# if this command errors, then the model has no defined speakers
xtts-list-speakers:
	tts --list_speaker_idxs --model_name "tts_models/multilingual/multi-dataset/xtts_v2"
	
xtts-create-speaker-samples:
	python.exe main.py create-speaker-samples -c "config_xtts.yaml"

xtts-speak-test:
	python.exe main.py speak -c "config_xtts.yaml"

xtts-clone-test:
	python.exe main.py speak -c "config_xtts.yaml" -v "voice_to_clone.wav"
