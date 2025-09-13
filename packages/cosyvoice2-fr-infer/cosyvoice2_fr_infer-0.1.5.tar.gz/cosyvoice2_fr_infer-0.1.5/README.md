cosyvoice2-fr-infer
====================

Minimal, plug-and-play CosyVoice2 French inference CLI that downloads the model from Hugging Face and runs cross-lingual cloning. It bundles the required `cosyvoice` runtime and `matcha` module so you don't need the full upstream repo.

## License

This project is licensed under the Apache License 2.0. 

**Note**: This package includes vendored code from:
- [CosyVoice2](https://github.com/FunAudioLLM/CosyVoice2) (Apache 2.0)
- [Matcha-TTS](https://github.com/shivammathur/Matcha-TTS) (Apache 2.0)

All original licenses and attributions are preserved.

Install (editable for local dev)
--------------------------------

```bash
cd standalone_infer
pip install -e .
```

For enhanced English phonemization (optional):
```bash
pip install -e .[piper]
```

**Note**: The `piper` optional dependency requires compilation tools and may fail in some environments (like Google Colab). The package will work without it, using the standard phonemizer as fallback.

If you are on Linux with GPU, ensure you install torch/torchaudio matching your CUDA and have `onnxruntime-gpu` available. If CPU-only, `onnxruntime` will be sufficient.

Usage
-----

```bash
cosy2-tts \
  --text "Bonjour, je m'appelle ..." \
  --prompt /path/to/prompt.wav \
  --out /tmp/out.wav
```

First run will download the model assets to `~/.cache/cosyvoice2-fr` (configurable via `--model-dir`).

Advanced options: `--setting`, `--llm-run-id`, `--flow-run-id`, `--hifigan-run-id`, `--final`, `--stream`, `--speed`, `--no-text-frontend`, `--repo-id`, `--no-hf`.




