#!/bin/bash
# RunPod Setup Script for Catalan-Spanish Model Training
#
# 1. Go to runpod.io and create an account
# 2. Launch a GPU Pod with:
#    - Template: RunPod Pytorch 2.1
#    - GPU: A100 (80GB) or A100 (40GB)
#    - Disk: 50GB+
# 3. Connect via SSH or Web Terminal
# 4. Run this script: bash runpod_setup.sh

set -e

echo "=============================================="
echo "RUNPOD SETUP - Catalan-Spanish Model"
echo "=============================================="

# Update system
apt-get update && apt-get install -y git wget

# Clone your repo (replace with your GitHub URL)
echo "Cloning repository..."
git clone https://github.com/shraavb/-Senior-Design-SpeakEasy.git
cd -Senior-Design-SpeakEasy/dataset-pipeline

# Install Python dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install vllm sglang

# Login to HuggingFace (for gated models like Llama)
echo ""
echo "=============================================="
echo "HuggingFace Login Required for Llama models"
echo "Get your token from: https://huggingface.co/settings/tokens"
echo "=============================================="
huggingface-cli login

# Download base model
echo "Downloading base model..."
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
model_name = 'meta-llama/Llama-3.2-1B-Instruct'
print(f'Downloading {model_name}...')
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
print('Model downloaded!')
"

echo ""
echo "=============================================="
echo "SETUP COMPLETE!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Upload your training data to data/processed/"
echo "  2. Run training: python src/finetune.py --num_epochs 3"
echo "  3. Or use vLLM: python src/inference_vllm.py serve"
echo ""
