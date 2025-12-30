# RunPod Deployment Guide

Deploy and train the Catalan-Spanish model on RunPod's A100 GPUs.

## Prerequisites

- RunPod account ([runpod.io](https://runpod.io))
- HuggingFace account with Llama access ([huggingface.co](https://huggingface.co))
- `runpodctl` installed locally

## Files

| File | Description |
|------|-------------|
| `runpod_upload.zip` | Pre-packaged training data and scripts (1.1MB) |
| `runpod_train.py` | A100-optimized training script |
| `runpod_package/setup_and_train.sh` | One-liner setup script |
| `runpod_setup.sh` | Full environment setup (clones repo) |
| `modal_deploy.py` | Alternative: Modal serverless deployment |

## Quick Start

### 1. Create RunPod Pod

1. Go to [runpod.io](https://runpod.io)
2. Click **Deploy** → **GPU Pods**
3. Configure:
   - **Template**: RunPod Pytorch 2.1
   - **GPU**: A100 (40GB or 80GB recommended)
   - **Disk**: 50GB+
4. Launch the pod

### 2. Upload Training Data

From your **local machine**:

```bash
# Install runpodctl if needed
brew install runpodctl  # macOS
# or see: https://docs.runpod.io/cli/install

# Connect to your pod
runpodctl config

# Send the zip file
runpodctl send deploy/runpod_upload.zip
```

### 3. Setup on RunPod

In the **RunPod terminal**:

```bash
# Navigate to workspace
cd /workspace

# Unzip the package
unzip runpod_upload.zip
cd runpod_package

# Run setup script (installs dependencies, creates training script)
bash setup_and_train.sh

# Login to HuggingFace for Llama model access
huggingface-cli login
```

### 4. Start Training

```bash
# Quick training (1 epoch, ~30 min)
python runpod_train.py --quick

# Full training (3 epochs, ~2 hours)
python runpod_train.py --full

# Custom settings
python runpod_train.py --epochs 5 --batch-size 8 --lora-r 64
```

### 5. Download Your Model

After training completes, from your **local machine**:

```bash
runpodctl receive models/catalan-spanish-runpod
```

Or upload directly to HuggingFace from RunPod:

```bash
huggingface-cli upload your-username/catalan-spanish models/catalan-spanish-runpod
```

## Training Options

| Flag | Description | Default |
|------|-------------|---------|
| `--quick` | 1 epoch, batch size 8 | - |
| `--full` | 3 epochs, batch size 4, LoRA r=64 | - |
| `--epochs N` | Number of training epochs | 3 |
| `--batch-size N` | Per-device batch size | 4 |
| `--lora-r N` | LoRA rank | 64 |
| `--lr RATE` | Learning rate | 2e-4 |
| `--use-4bit` | Enable 4-bit quantization | off |
| `--no-flash-attention` | Disable Flash Attention 2 | off |

## GPU Recommendations

| GPU | VRAM | Batch Size | Training Time (3 epochs) |
|-----|------|------------|--------------------------|
| A100 80GB | 80GB | 8 | ~1.5 hours |
| A100 40GB | 40GB | 4 | ~2 hours |
| A10G | 24GB | 2 | ~3 hours |

## Troubleshooting

### "CUDA out of memory"
- Reduce batch size: `--batch-size 2`
- Enable 4-bit quantization: `--use-4bit`

### "Flash Attention not available"
- Use: `--no-flash-attention`

### HuggingFace authentication error
- Run `huggingface-cli login` with a valid token
- Ensure you've accepted the Llama license at [meta-llama/Llama-3.2-1B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct)

## Alternative: Modal Deployment

For serverless GPU inference (pay-per-use):

```bash
pip install modal
modal token new
modal deploy deploy/modal_deploy.py
```

See `modal_deploy.py` for API endpoint and batch inference options.
