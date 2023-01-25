from multiprocessing import cpu_count
from os import makedirs
from os.path import isfile
from tempfile import gettempdir

import numpy as np
import requests
import whisper
from ovos_plugin_manager.templates.stt import STT
from ovos_utils.xdg_utils import xdg_data_home
from whisper.tokenizer import LANGUAGES, get_tokenizer

try:
    from tensorflow.lite import Interpreter
except ImportError:
    from tflite_runtime.interpreter import Interpreter


class WhisperTFLiteSTT(STT):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        n = max(cpu_count() - 1, 1)
        model_path = self.config.get("model") or \
                     "https://github.com/usefulsensors/openai-whisper/raw/main/models/whisper-tiny.en.tflite"
        if model_path.startswith("http"):
            model_path = self.download_model(model_path)
        self.interpreter = Interpreter(model_path, num_threads=n)
        self.interpreter.allocate_tensors()
        self.input_tensor = self.interpreter.get_input_details()[0]['index']
        self.output_tensor = self.interpreter.get_output_details()[0]['index']
        self.tokenizers = {}
        self.get_tokenizer(self.lang)

    def download_model(self, url):
        model_folder = f"{xdg_data_home()}/whisper_tflite"
        makedirs(model_folder, exist_ok=True)
        model_name = url.split("/")[-1]
        model_path = f"{model_folder}/{model_name}"
        if not isfile(model_path):
            with open(model_path, "wb") as f:
                f.write(requests.get(url).content)
        return model_path

    def get_tokenizer(self, lang):
        lang = lang.split("-")[0]
        if lang not in self.tokenizers:
            if lang == "en":
                self.tokenizers[lang] = get_tokenizer(False, language="en")
            else:
                self.tokenizers[lang] = get_tokenizer(True, language=lang)
        return self.tokenizers[lang]

    def transcribe(self, audio_file, lang):
        wtokenizer = self.get_tokenizer(lang)
        print(f'Calculating mel spectrogram...')
        mel_from_file = whisper.audio.log_mel_spectrogram(audio_file)
        input_data = whisper.audio.pad_or_trim(mel_from_file, whisper.audio.N_FRAMES)
        input_data = np.expand_dims(input_data, 0)
        # print("Input data shape:", input_data.shape)

        # input_data = np.frombuffer(wf.readframes(wf.getnframes()), np.int16)
        # input_data = np.random.randn(1, 256, 256, 3)

        print("Invoking interpreter ...")
        self.interpreter.set_tensor(self.input_tensor, input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_tensor)

        print("Preparing output data ...")
        output_details = self.interpreter.get_output_details()
        output_data = self.interpreter.get_tensor(output_details[0]['index'])
        # output_data = output_data.squeeze()
        # print(output_data)
        # np.savetxt("output.txt", output_data)
        # print(interpreter.get_output_details()[0])

        # convert tokens to text
        print("Converting tokens ...")
        for token in output_data:
            # print(token)
            token[token == -100] = wtokenizer.eot
            text = wtokenizer.decode(token, skip_special_tokens=True)
            return text

    def execute(self, audio, language=None):
        lang = language or self.lang
        lang = lang.split("-")[0]
        # TODO - figure out how to avoid writing file
        audio_file = f"{gettempdir()}/whisper_stt.wav"
        with open(audio_file, "wb") as f:
            f.write(audio.get_wav_data())
        utt = self.transcribe(audio_file, lang)
        return utt

    def available_languages(self) -> set:
        return set(LANGUAGES.keys())


WhisperTFLiteSTTConfig = {}
