#!/usr/bin/env python3
"""
vLLM Inference Engine for Catalan-Spanish Model

High-throughput inference using vLLM for faster generation.
Supports both the base model and LoRA adapters.

Requirements:
    pip install vllm

Usage:
    # Start vLLM server
    python src/inference_vllm.py serve --model meta-llama/Llama-3.2-1B-Instruct --lora models/catalan-spanish-finetuned

    # Run batch inference
    python src/inference_vllm.py batch --input data/eval/prompts.json --output results.json

    # Interactive chat
    python src/inference_vllm.py chat --model meta-llama/Llama-3.2-1B-Instruct
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional
import time


def check_vllm():
    """Check if vLLM is installed."""
    try:
        import vllm
        return True
    except ImportError:
        print("vLLM not installed. Install with:")
        print("  pip install vllm")
        return False


def create_vllm_engine(
    model_name: str,
    lora_path: Optional[str] = None,
    tensor_parallel_size: int = 1,
    max_model_len: int = 2048,
    gpu_memory_utilization: float = 0.9,
):
    """
    Create a vLLM inference engine.

    Args:
        model_name: HuggingFace model ID or local path
        lora_path: Path to LoRA adapter (optional)
        tensor_parallel_size: Number of GPUs for tensor parallelism
        max_model_len: Maximum sequence length
        gpu_memory_utilization: Fraction of GPU memory to use
    """
    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest

    # Configure engine
    engine_args = {
        "model": model_name,
        "tensor_parallel_size": tensor_parallel_size,
        "max_model_len": max_model_len,
        "gpu_memory_utilization": gpu_memory_utilization,
        "trust_remote_code": True,
    }

    # Enable LoRA if provided
    if lora_path:
        engine_args["enable_lora"] = True
        engine_args["max_lora_rank"] = 64

    print(f"Initializing vLLM engine with {model_name}...")
    llm = LLM(**engine_args)

    return llm, lora_path


def generate_responses(
    llm,
    prompts: List[str],
    lora_path: Optional[str] = None,
    max_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> List[str]:
    """
    Generate responses for a batch of prompts.

    Args:
        llm: vLLM engine
        prompts: List of input prompts
        lora_path: Path to LoRA adapter
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Top-p sampling parameter

    Returns:
        List of generated responses
    """
    from vllm import SamplingParams
    from vllm.lora.request import LoRARequest

    sampling_params = SamplingParams(
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
    )

    # Create LoRA request if adapter provided
    lora_request = None
    if lora_path:
        lora_request = LoRARequest("catalan-spanish", 1, lora_path)

    # Generate
    if lora_request:
        outputs = llm.generate(prompts, sampling_params, lora_request=lora_request)
    else:
        outputs = llm.generate(prompts, sampling_params)

    # Extract text
    responses = [output.outputs[0].text for output in outputs]
    return responses


def format_chat_prompt(
    messages: List[Dict[str, str]],
    system_prompt: str = "Eres un hablante nativo de español con acento catalán. Responde de manera natural y conversacional."
) -> str:
    """Format messages into a chat prompt."""
    prompt = f"<|system|>\n{system_prompt}\n"

    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            prompt += f"<|user|>\n{content}\n"
        elif role == "assistant":
            prompt += f"<|assistant|>\n{content}\n"

    prompt += "<|assistant|>\n"
    return prompt


def run_batch_inference(
    model_name: str,
    input_file: str,
    output_file: str,
    lora_path: Optional[str] = None,
    max_tokens: int = 256,
    batch_size: int = 32,
):
    """
    Run batch inference on a file of prompts.

    Input file format (JSON):
    [
        {"id": "1", "prompt": "¡Hola! ¿Cómo estás?"},
        {"id": "2", "prompt": "¿Qué planes tienes?"},
        ...
    ]
    """
    # Load prompts
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    prompts = [item.get("prompt", item.get("text", "")) for item in data]
    ids = [item.get("id", str(i)) for i, item in enumerate(data)]

    print(f"Loaded {len(prompts)} prompts from {input_file}")

    # Create engine
    llm, lora = create_vllm_engine(model_name, lora_path)

    # Format prompts
    formatted_prompts = [
        format_chat_prompt([{"role": "user", "content": p}])
        for p in prompts
    ]

    # Generate in batches
    all_responses = []
    start_time = time.time()

    for i in range(0, len(formatted_prompts), batch_size):
        batch = formatted_prompts[i:i + batch_size]
        responses = generate_responses(llm, batch, lora, max_tokens)
        all_responses.extend(responses)
        print(f"Processed {min(i + batch_size, len(prompts))}/{len(prompts)}")

    elapsed = time.time() - start_time

    # Save results
    results = [
        {
            "id": ids[i],
            "prompt": prompts[i],
            "response": all_responses[i],
        }
        for i in range(len(prompts))
    ]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {output_file}")
    print(f"Total time: {elapsed:.2f}s")
    print(f"Throughput: {len(prompts) / elapsed:.2f} prompts/second")


def run_interactive_chat(
    model_name: str,
    lora_path: Optional[str] = None,
    max_tokens: int = 256,
):
    """Run interactive chat session."""
    llm, lora = create_vllm_engine(model_name, lora_path)

    print("\n" + "=" * 60)
    print("CATALAN-SPANISH CHAT (vLLM)")
    print("=" * 60)
    print("Type 'quit' to exit, 'clear' to reset conversation")
    print("=" * 60 + "\n")

    history = []

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'clear':
            history = []
            print("Conversation cleared.\n")
            continue
        elif not user_input:
            continue

        history.append({"role": "user", "content": user_input})
        prompt = format_chat_prompt(history)

        responses = generate_responses(llm, [prompt], lora, max_tokens)
        response = responses[0].strip()

        history.append({"role": "assistant", "content": response})
        print(f"Assistant: {response}\n")


def start_openai_server(
    model_name: str,
    lora_path: Optional[str] = None,
    host: str = "0.0.0.0",
    port: int = 8000,
):
    """
    Start an OpenAI-compatible API server.

    This allows using the model with any OpenAI client:

        from openai import OpenAI
        client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
        response = client.chat.completions.create(
            model="catalan-spanish",
            messages=[{"role": "user", "content": "¡Hola!"}]
        )
    """
    import subprocess
    import sys

    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", model_name,
        "--host", host,
        "--port", str(port),
    ]

    if lora_path:
        cmd.extend(["--enable-lora", "--lora-modules", f"catalan-spanish={lora_path}"])

    print(f"Starting vLLM OpenAI-compatible server on {host}:{port}")
    print(f"Model: {model_name}")
    if lora_path:
        print(f"LoRA: {lora_path}")
    print("\nAccess the API at:")
    print(f"  http://localhost:{port}/v1/chat/completions")
    print("\nExample curl:")
    print(f'  curl http://localhost:{port}/v1/chat/completions \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"model": "catalan-spanish", "messages": [{"role": "user", "content": "¡Hola!"}]}\'')

    subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser(description="vLLM inference for Catalan-Spanish model")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Batch inference
    batch_parser = subparsers.add_parser("batch", help="Run batch inference")
    batch_parser.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct")
    batch_parser.add_argument("--lora", default="models/catalan-spanish-finetuned")
    batch_parser.add_argument("--input", required=True, help="Input JSON file")
    batch_parser.add_argument("--output", required=True, help="Output JSON file")
    batch_parser.add_argument("--max-tokens", type=int, default=256)
    batch_parser.add_argument("--batch-size", type=int, default=32)

    # Interactive chat
    chat_parser = subparsers.add_parser("chat", help="Interactive chat")
    chat_parser.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct")
    chat_parser.add_argument("--lora", default="models/catalan-spanish-finetuned")
    chat_parser.add_argument("--max-tokens", type=int, default=256)

    # API server
    serve_parser = subparsers.add_parser("serve", help="Start OpenAI-compatible server")
    serve_parser.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct")
    serve_parser.add_argument("--lora", default="models/catalan-spanish-finetuned")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    if not check_vllm():
        return

    if args.command == "batch":
        run_batch_inference(
            args.model, args.input, args.output,
            args.lora, args.max_tokens, args.batch_size
        )
    elif args.command == "chat":
        run_interactive_chat(args.model, args.lora, args.max_tokens)
    elif args.command == "serve":
        start_openai_server(args.model, args.lora, args.host, args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
