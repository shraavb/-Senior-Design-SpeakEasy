#!/usr/bin/env python3
"""
Modal Deployment for Catalan-Spanish Model

Modal provides serverless GPU inference - you only pay when running.
Perfect for batch inference and API endpoints.

Setup:
    1. pip install modal
    2. modal token new
    3. python deploy/modal_deploy.py

Usage:
    # Deploy the inference endpoint
    modal deploy deploy/modal_deploy.py

    # Run batch inference
    modal run deploy/modal_deploy.py::batch_inference --input prompts.json

    # Interactive test
    modal run deploy/modal_deploy.py::test_model
"""

import modal

# Create Modal app
app = modal.App("catalan-spanish-model")

# Define the container image with all dependencies
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "torch>=2.1.0",
    "transformers>=4.36.0",
    "accelerate>=0.25.0",
    "peft>=0.7.0",
    "vllm>=0.3.0",
    "huggingface_hub",
)

# Volume to cache model weights
model_cache = modal.Volume.from_name("catalan-spanish-cache", create_if_missing=True)

# Constants
MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"
LORA_REPO = None  # Set to HuggingFace repo if you upload your LoRA adapter
MODEL_DIR = "/cache/models"


@app.cls(
    image=image,
    gpu="A100",  # Can also use "A10G", "T4", "H100"
    timeout=600,
    volumes={MODEL_DIR: model_cache},
    secrets=[modal.Secret.from_name("huggingface-secret")],  # For gated models
)
class CatalanSpanishModel:
    """Modal class for serving the Catalan-Spanish model."""

    @modal.enter()
    def load_model(self):
        """Load model when container starts."""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        import os

        print("Loading model...")

        # Load base model
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            cache_dir=MODEL_DIR,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float16,
            device_map="auto",
            cache_dir=MODEL_DIR,
        )

        # Load LoRA adapter if available
        if LORA_REPO:
            print(f"Loading LoRA adapter from {LORA_REPO}...")
            self.model = PeftModel.from_pretrained(
                self.model,
                LORA_REPO,
                cache_dir=MODEL_DIR,
            )

        self.model.eval()
        print("Model loaded!")

    @modal.method()
    def generate(
        self,
        prompt: str,
        max_tokens: int = 150,
        temperature: float = 0.7,
        system_prompt: str = None,
    ) -> str:
        """Generate a response for a single prompt."""
        import torch

        if system_prompt is None:
            system_prompt = "Eres un hablante nativo de español con acento catalán. Responde de manera natural y conversacional."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        inputs = self.tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True,
        ).to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        response = self.tokenizer.decode(
            outputs[0][inputs.shape[1]:],
            skip_special_tokens=True,
        )

        return response.strip()

    @modal.method()
    def batch_generate(
        self,
        prompts: list[str],
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> list[str]:
        """Generate responses for multiple prompts."""
        return [
            self.generate(p, max_tokens, temperature)
            for p in prompts
        ]


# vLLM-based high-throughput endpoint
@app.cls(
    image=image.pip_install("vllm>=0.3.0"),
    gpu="A100",
    timeout=600,
    volumes={MODEL_DIR: model_cache},
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
class CatalanSpanishVLLM:
    """High-throughput inference using vLLM."""

    @modal.enter()
    def load_model(self):
        """Initialize vLLM engine."""
        from vllm import LLM, SamplingParams

        print("Initializing vLLM engine...")

        self.llm = LLM(
            model=MODEL_NAME,
            download_dir=MODEL_DIR,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.9,
            max_model_len=2048,
        )

        self.default_params = SamplingParams(
            max_tokens=150,
            temperature=0.7,
            top_p=0.9,
        )

        print("vLLM engine ready!")

    @modal.method()
    def generate_batch(
        self,
        prompts: list[str],
        max_tokens: int = 150,
        temperature: float = 0.7,
    ) -> list[str]:
        """Generate responses for a batch of prompts."""
        from vllm import SamplingParams

        # Format prompts
        system = "Eres un hablante nativo de español con acento catalán."
        formatted = [
            f"<|system|>\n{system}\n<|user|>\n{p}\n<|assistant|>\n"
            for p in prompts
        ]

        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
        )

        outputs = self.llm.generate(formatted, params)

        return [o.outputs[0].text.strip() for o in outputs]


# Web endpoint for API access
@app.function(
    image=image,
    gpu="A100",
    timeout=300,
    volumes={MODEL_DIR: model_cache},
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
@modal.web_endpoint(method="POST")
def inference_endpoint(request: dict) -> dict:
    """
    Web endpoint for inference.

    POST /inference_endpoint
    {
        "prompt": "¡Hola! ¿Cómo estás?",
        "max_tokens": 150,
        "temperature": 0.7
    }
    """
    model = CatalanSpanishModel()

    prompt = request.get("prompt", "")
    max_tokens = request.get("max_tokens", 150)
    temperature = request.get("temperature", 0.7)

    response = model.generate.remote(prompt, max_tokens, temperature)

    return {
        "prompt": prompt,
        "response": response,
    }


# Test function
@app.local_entrypoint()
def test_model():
    """Test the deployed model."""
    model = CatalanSpanishModel()

    test_prompts = [
        "¡Hola! ¿Cómo estás?",
        "¿Qué planes tienes para el fin de semana?",
        "Me puedes recomendar un buen restaurante?",
    ]

    print("\n" + "=" * 60)
    print("TESTING CATALAN-SPANISH MODEL ON MODAL")
    print("=" * 60 + "\n")

    for prompt in test_prompts:
        print(f"User: {prompt}")
        response = model.generate.remote(prompt)
        print(f"Model: {response}\n")


@app.local_entrypoint()
def batch_inference(input_file: str = "prompts.json", output_file: str = "results.json"):
    """Run batch inference on a file of prompts."""
    import json

    with open(input_file, 'r') as f:
        data = json.load(f)

    prompts = [item.get("prompt", item.get("text", "")) for item in data]

    print(f"Processing {len(prompts)} prompts...")

    # Use vLLM for high-throughput
    vllm_model = CatalanSpanishVLLM()
    responses = vllm_model.generate_batch.remote(prompts)

    results = [
        {"prompt": p, "response": r}
        for p, r in zip(prompts, responses)
    ]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    # For local testing
    test_model()
