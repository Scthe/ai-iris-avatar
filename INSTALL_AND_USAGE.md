`TODO image here`
`TODO unity - screen from editor, mark the play button`

## Usage

### Install ollama to access LLM models

[Ollama](https://ollama.com/) is used to manage locally installed LLM models.

1. Download ollama from [https://ollama.com/download](https://ollama.com/download).
2. `ollama pull gemma:2b-instruct`. Pull model file e.g. [gemma:2b-instruct](https://ollama.com/library/gemma:2b-instruct).
3. Verification:
   1. `ollama show gemma:2b-instruct --modelfile`. Inspect model file data.
   2. `ollama run gemma:2b-instruct`. Open the chat in the console to check everything is OK.

### Start the server

Requires Python version >3.9 and <=3.11. TTS library [does not work with the latest Python 3.12](https://github.com/coqui-ai/TTS/issues/3627).

1. `python3.11 -m venv .venv`. Create a virtual environment to not pollute global Python packages.
   1. You can also use [conda](https://conda.io/projects/conda/en/latest/index.html).
   2. If you have Python <=3.11 alongside the latest 3.12, use it instead e.g. `C:/programs/install/Python310/python.exe -m venv .venv`
2. `source .venv/Scripts/Activate`. Activate virtual environment.
3. `pip install -r requirements.txt`. Install dependencies.
4. (Optional) Install PyTorch CUDA for [GPU acceleration for TTS](https://stackoverflow.com/questions/66726331/how-can-i-run-mozilla-tts-coqui-tts-training-with-cuda-on-a-windows-system): `pip install torch==2.2.2+cu118 -f https://download.pytorch.org/whl/torch_stable.html`
5. `python.exe main.py serve --config "config_xtts.yaml"`. Start the server. The first time will also download the `XTTS v2.0` model.
6. Verification:
   1. [http://localhost:8080/index.html](http://localhost:8080/index.html) should the open control panel.

You can find other commands in the [makefile](makefile):

- `make curl_prompt_get` and `make curl_prompt_post`. Send prompt remotely through the `/prompt` endpoint. You can also use it in your scripts.
- `tts --list_models` or `make tts-list-models`. List models available in the TTS python package.
- `make xtts-list-speakers`. List speakers available for the `XTTS v2.0` model.
- `make xtts-create-speaker-samples`. Writes speaker samples for the `XTTS v2.0` into the `out_speaker_samples` directory. You will have 55+ .wav files (one per speaker) that say the same test sentence. Use it to select the preferred one.
- `make xtts-speak-test`. Speak the test sentence and write the result to `out_speak_result.wav`. Uses the same configuration as the app server.
- `make xtts-clone-test`. Speak test sentence using voice cloning based on the `voice_to_clone.wav` file (not provided in the repo). Write the result to `out_speak_result.wav`.

### Start unity client

Import unity project from `unity-project`. Read ["Oculus Lipsync for Unity Development"](https://developer.oculus.com/documentation/unity/audio-ovrlipsync-unity/) beforehand (requires Windows/macOS). Their documentation also contains the "Download and Import" section in case of any problems. Make sure to accept their licensing.

> I've added Oculus Lipsync's source code to this repo as it required some extra fixes inside C# scripts. Tested on Windows.

To create a production build follow official docs: [Publishing Builds](https://docs.unity3d.com/Manual/PublishingBuilds.html).

## Customization

### Server config

See [config.example.yaml](config.example.yaml) for all configuration options. If you followed the instructions above, you have already used [config_xtts.yaml](config_xtts.yaml). See [server/config.py](server/config.py) for default values.

### Changing the large language model

This depends if your selected LLM works with ollama or not. If it does:

1. `ollama pull <model_name>`.
2. Update the app's config file: `llm.model: <model_name>` (see `config.example.yaml` file).
3. Update `server\app_logic.py`:
   1. Rewrite the `GemmaChatContext` class to generate a prompt based on: the user's query, past messages, and the LLM model's card.
   2. In the `AppLogic` class, there is a `_exec_llm()` function. It **might** need adjusting e.g. to call `await self.llm.chat()` instead `await self.llm.generate()`. Depends on the model.

If you want to connect a model that is not available in ollama, just rewrite `AppLogic`'s `_exec_llm()` function. You get chat history, current message, and config file values. The function is async and returns a string. I assume this is exactly the API you would expect.

### Changing the text-to-speech model

With the [TTS](https://github.com/coqui-ai/TTS) library, you can select from many available models. You get e.g. [Bark](https://github.com/suno-ai/bark), [tortoise-tts](https://github.com/neonbjb/tortoise-tts), Glow/VITS, and a few more. I went with XTTS v2.0 as it performed best when I did a blind test on Hugging Face. Each model usually supports many languages and speakers. Not only can you select the model itself, but you also choose which of many male/female voices suits your avatar best.

Everything is controlled from the config file. See [config.example.yaml](config.example.yaml) for details. In "other commands" I've listed a few scripts that make it easier to choose. E.g. generating a sample .wav file for each speaker available in a selected model.

If you want to go beyond the TTS library, check the `_exec_tts()` function inside [server/app_logic.py](server/app_logic.py). I recommend splitting the text into separate sentences and streaming them to the client one by one.

### Voice cloning

Set `tts.sample_of_cloned_voice_wav` in `config_xtts.yaml` to point to the voice sample file. Unfortunately, this usually prolongs the inference time for TTS. I found one of the built-in voices good enough.

That's not the only way to customize the voice. You can always [apply a filter](https://github.com/jiaaro/pydub) to the output. Shift pitch, speed up, trim, cut etc. Given the wide range of available base voices, it should be enough to create something custom. This has a smaller runtime cost than stacking another neural net.

## FAQ

**Q: What to do if I get nothing in response?**

Usually caused by a lack of VRAM.

1. Check that there are no other apps that have loaded models on GPU (video games, stable diffusion, etc.). Even if they don't do anything ATM, they still take VRAM.
1. Close Ollama.
1. Make sure VRAM usage is at 0.
1. Start Ollama.
1. Restart the app.
1. Ask a question to load all models into VRAM.
1. Check you are not running out of VRAM.

**Q: How to add speech-to-text (STT)?**

This feature is not available, but you can easily add it yourself. There is a `/prompt` endpoint (either as GET or POST) used to send a query: `curl "http://localhost:8080/prompt?value=Who%20is%20Michael%20Jordan%3F"`.

The simplest way is a separate script that wraps around a speech-to-text model. ATM Whisper models are popular: [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [insanely-fast-whisper](https://github.com/Vaibhavs10/insanely-fast-whisper), etc.

**Q: Can I make the lip sync less robotic?**

The robotic feeling you get is when the mouth just [lerps](https://en.wikipedia.org/wiki/Linear_interpolation) between predefined shape keys. It's more natural to slur the shapes. Oculus lipsync allows you to adjust this tolerance. This setting is usually adjusted based on feeling and not any objective metric. I've chosen a conservative value to preserve a closed mouth on 'm', 'b', and 'p' sounds. From what I've perceived, this is the most important shape.

**Q: How to integrate DeepSpeed for faster TTS?**

[DeepSpeed](https://github.com/microsoft/DeepSpeed) is a library that can speed up TTS inference ~2x. You must satisfy following conditions:

- CUDA version of PyTorch is used.
- In config, both `tts.deepspeed_enabled` and `tts.use_gpu` are True (which are the default).
- TTS model is `tts_models/multilingual/multi-dataset/xtts_v2` (which is the default).
- DeepSpeed is installed.

To install DeepSpeed on non-Windows machine use `pip install deepspeed`. For Windows, the official readme suggests manually building it instead. Fortunately, the community [has done this for us](https://github.com/erew123/alltalk_tts?tab=readme-ov-file#-deepspeed-installation-options):

1. Find pre-compiled wheel library based on your Python, CUDA and PyTorch version. Check following repositories:
    1. [alltalk_tts/releases](https://github.com/erew123/alltalk_tts/releases)
    1. [Deepspeed-Windows/releases](https://github.com/S95Sedan/Deepspeed-Windows/releases)
    1. [deepspeed-windows-wheels/releases](https://github.com/daswer123/deepspeed-windows-wheels/releases)
2. Download the .whl file.
3. Install: `pip install {deep-speed-wheel-file-name-here}`.
   1. If you want to uninstall it later, use `pip uninstall deepspeed`.

I'm using Python 3.10. I've installed PyTorch with CUDA using `pip install torch==2.2.2+cu118 -f https://download.pytorch.org/whl/torch_stable.html` (Pytorch 2.2.2, CUDA 11.8). From [daswer123/deepspeed-windows-wheels](https://github.com/daswer123/deepspeed-windows-wheels/releases/tag/13.1) I've downloaded `deepspeed-0.13.1+cu118-cp310-cp310-win_amd64.whl`. Once you start the server next time, you should see the confirmation in the console.

**Q: How to trigger action from outside the Unity?**

Unity client [opens](unity-project\Assets\Scripts\WebSocketClientBehaviour.cs) WebSocket to the Python server. Add a new `onJsonMessage` handler to the existing object that has `WebSocketClientBehaviour`. For Particle effects I've already done that inside `WebSocketMsgHandler.cs`. It's `OnMessage()` function contains a switch based on the json's object `type` field.

Example flow when action is triggered from the web browser:

1. **The user** clicks on the [ParticleSystemsRow](server\static\app.mjs#L230).
2. **Browser** sends `{ type: 'play-vfx', vfx: '<vfx-name>' }` JSON through the WebSocket to the **Python server**.
3. **The Python server** forwards the `"play-vfx"` message to the **Unity client**.
4. In Unity, my object with `WebSocketClientBehaviour` component receives the message and determines it to be a string. This component is responsible for low level WebSocket operations as well as differentiating between JSON and WAV audio messages.
5. `WebSocketClientBehaviour.onJsonMessage()` delegates are called, which includes my object with `WebSocketMsgHandler`.
6. `WebSocketMsgHandler.OnMessage()` parses the message's `"type"` field. It can then trigger the corresponding action.