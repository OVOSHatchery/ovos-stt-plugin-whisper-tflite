## Description

A stt plugin for ovos using [whisper-tflite](https://github.com/fquirin/speech-recognition-experiments/blob/main/whisper-tflite)

## Install

`pip install ovos-stt-plugin-whisper-tflite`


## Configuration

```json
  "stt": {
    "module": "ovos-stt-plugin-whisper-tflite",
    "ovos-stt-plugin-whisper-tflite": {"model": "https://github.com/usefulsensors/openai-whisper/raw/main/models/whisper-tiny.en.tflite"}
  }
 
```