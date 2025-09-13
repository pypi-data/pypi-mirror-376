# ESP32 Manager CLI

[![PyPI version](https://img.shields.io/pypi/v/esp32-manager.svg)](https://pypi.org/project/esp32-manager/)
[![Python versions](https://img.shields.io/pypi/pyversions/esp32-manager.svg)](https://pypi.org/project/esp32-manager/)
[![License](https://img.shields.io/github/license/juanmitaboada/esp32-manager.svg)](LICENSE)

A simple command-line utility to **upload, download, and manage files on ESP32 boards running MicroPython**.
Supports reliable file transfers with chunked **SHA256 per-chunk validation**, auto-port detection, and friendly CLI commands.

⚠️  DISCLAIMER: It probably works with other MicroPython boards like ESP8266, Pyboard, etc. but it hasn't been tested.

---

## ✨ Features

- 📡 Auto-detect serial port (`/dev/ttyUSB*`, `CH340`, `CP210`, etc.)
- 📂 **List files** on the device
- ⬆️ Reliable file upload with **chunked transfers** and per-chunk hash validation
- ⬇️ Download and view files from the ESP32
- 📄 **Read files** (`cat`) directly from the device
- 🗑️ Remove individual or all files (`clean` command preserves `boot.py`)
- 🔁 Reset the board and run `main.py`
- Works out of the box with **MicroPython raw REPL**

---

## 📦 Installation

```bash
pip install esp32-manager
```

Or, install from source:

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/esp32-manager.git
cd esp32-manager
pip install -e .
```

---

## 🚀 Usage

After installation, the CLI is available as:

```bash
esp32-manager <command> [options]
```

### Available commands

- `ls` - List files on the ESP32
- `put <files>` - Upload one or more files
- `get <files>` - Download files from the ESP32 
- `cat <files>` - Print file contents
- `rm <files>` - Delete files
- `clean` - Delete all files (except `boot.py`) 
- `run` - Reboot the board (`machine.reset()`)

### Options

- `--port DEVICE` - Serial port (default: auto-detected)
- `--baudrate N` - Baudrate (default: `115200`) 
- `--raw` - Suppress emojis / extra formatting (for scripting)

---

## 🛠 Example

```bash
# List files on device
esp32-manager ls

# Upload main.py
esp32-manager put src/main.py

# Upload all files in src/
esp32-manager put src/*

# Download files
esp32-manager get config.json main.py

# Print contents of a file
esp32-manager cat main.py

# Delete a file
esp32-manager rm main.py

# Clean all files (except boot.py)
esp32-manager clean

# Reboot device
esp32-manager run

# Specify port and baudrate
python3 esp32_manager.py put main.py --port /dev/ttyUSB1 --baudrate 921600

# Raw output (no emojis)
python3 esp32_manager.py ls --raw
```

⚠️ **Tip:** Use `put` for all source files (`main.py`, `wifi.py`, `cam.py`, `control.py`, `webserver.py`, etc.) to keep your ESP32 in sync with your local project.

---

## 📜 License

This project is licensed under the Apache License, Version 2.0. You may not use this file except in compliance with the License. A copy of the License is provided in the [LICENSE](LICENSE) file.
