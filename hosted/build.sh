#!/usr/bin/env bash
set -euo pipefail
pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r hosted/requirements.txt
python hosted/engine.py warmup
