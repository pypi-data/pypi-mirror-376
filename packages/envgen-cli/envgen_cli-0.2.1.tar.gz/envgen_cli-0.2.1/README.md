# 🧰 envgen — Generate `.env` from `.env.example`

> A simple CLI tool that helps developers generate `.env` files interactively from `.env.example`.

## ✨ Features

- Reads `.env.example` in current directory
- Prompts for missing values
- Uses defaults if provided
- Safe — won’t overwrite `.env` unless forced
- Lightweight, zero config

## 🚀 Installation

```bash
pip install .
# or from PyPI later:
# pip install envgen
## 🚀 Advanced Usage

### Auto-generate secrets
```bash
envgen --auto-generate