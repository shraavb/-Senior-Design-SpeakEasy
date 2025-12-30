#!/usr/bin/env python3
"""
SGLang Integration for Catalan-Spanish Model

SGLang provides structured generation, efficient batching, and
advanced prompting patterns for language learning scenarios.

Requirements:
    pip install sglang

Usage:
    # Start SGLang server
    python src/inference_sglang.py serve --model meta-llama/Llama-3.2-1B-Instruct

    # Run structured conversation scenarios
    python src/inference_sglang.py scenarios --scenario greetings

    # Evaluate model on all scenarios
    python src/inference_sglang.py evaluate --output eval_results.json
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import time


def check_sglang():
    """Check if SGLang is installed."""
    try:
        import sglang as sgl
        return True
    except ImportError:
        print("SGLang not installed. Install with:")
        print("  pip install sglang")
        return False


# ============================================================
# SGLang Program Definitions
# ============================================================

def create_conversation_program():
    """
    Create an SGLang program for multi-turn conversations.

    SGLang uses decorators to define structured generation programs
    that can be efficiently batched and cached.
    """
    import sglang as sgl

    @sgl.function
    def conversation(s, user_message: str, scenario: str = "general"):
        """Generate a response in a conversation."""
        system_prompts = {
            "general": "Eres un hablante nativo de español con acento catalán. Responde de manera natural y conversacional.",
            "greetings": "Eres un hablante nativo de español de Barcelona. Responde a los saludos de forma amigable y natural.",
            "farewells": "Eres un hablante nativo de español de Cataluña. Despídete de forma cálida y natural.",
            "family": "Eres un hablante nativo de español. Habla sobre temas familiares de forma cercana.",
            "emotions": "Eres un hablante nativo de español empático. Responde a las emociones de forma comprensiva.",
            "plans": "Eres un hablante nativo de español sociable. Ayuda a hacer planes de forma entusiasta.",
            "requests": "Eres un hablante nativo de español servicial. Responde a las peticiones amablemente.",
            "apologies": "Eres un hablante nativo de español comprensivo. Acepta disculpas con gracia.",
            "opinions": "Eres un hablante nativo de español. Comparte opiniones de forma respetuosa.",
        }

        system = system_prompts.get(scenario, system_prompts["general"])

        s += sgl.system(system)
        s += sgl.user(user_message)
        s += sgl.assistant(sgl.gen("response", max_tokens=150, temperature=0.7))

    return conversation


def create_dialogue_program():
    """
    Create an SGLang program for generating complete dialogues.

    This generates both sides of a conversation for training data augmentation.
    """
    import sglang as sgl

    @sgl.function
    def generate_dialogue(s, scenario: str, context: str = ""):
        """Generate a complete dialogue for a scenario."""
        s += sgl.system(f"""Eres un escritor de diálogos en español.
Genera un diálogo natural y realista para la siguiente situación: {scenario}
El diálogo debe tener entre 4 y 6 intercambios.
Usa español conversacional con influencia catalana cuando sea apropiado.
{f'Contexto adicional: {context}' if context else ''}""")

        s += sgl.user("Genera el diálogo:")
        s += sgl.assistant(sgl.gen("dialogue", max_tokens=500, temperature=0.8))

    return generate_dialogue


def create_evaluation_program():
    """
    Create an SGLang program for evaluating responses.

    Uses the model to self-evaluate naturalness and appropriateness.
    """
    import sglang as sgl

    @sgl.function
    def evaluate_response(s, prompt: str, response: str, scenario: str):
        """Evaluate a response for quality metrics."""
        s += sgl.system("""Eres un evaluador de respuestas en español.
Evalúa la respuesta según estos criterios:
1. Naturalidad (1-5): ¿Suena como un hablante nativo?
2. Relevancia (1-5): ¿Responde apropiadamente al contexto?
3. Fluidez (1-5): ¿Es gramaticalmente correcta y fluida?
Responde SOLO con JSON en este formato:
{"naturalidad": N, "relevancia": N, "fluidez": N, "comentario": "breve explicación"}""")

        s += sgl.user(f"""Escenario: {scenario}
Prompt: {prompt}
Respuesta: {response}

Evalúa esta respuesta:""")

        s += sgl.assistant(sgl.gen("evaluation", max_tokens=200, temperature=0.3))

    return evaluate_response


def create_roleplay_program():
    """
    Create an SGLang program for roleplay scenarios.

    Useful for language learning with specific character roles.
    """
    import sglang as sgl

    @sgl.function
    def roleplay(s, character: str, situation: str, user_message: str):
        """Roleplay as a specific character in a situation."""
        s += sgl.system(f"""Eres {character}.
Situación: {situation}
Responde en español de forma natural, manteniendo el personaje.
Usa expresiones coloquiales y regionales cuando sea apropiado.""")

        s += sgl.user(user_message)
        s += sgl.assistant(sgl.gen("response", max_tokens=200, temperature=0.8))

    return roleplay


# ============================================================
# Batch Processing with SGLang
# ============================================================

def run_batch_conversations(
    prompts: List[Dict[str, str]],
    backend_url: str = "http://localhost:30000",
) -> List[Dict[str, Any]]:
    """
    Run batch conversations using SGLang's efficient batching.

    Args:
        prompts: List of {"prompt": str, "scenario": str}
        backend_url: URL of SGLang server

    Returns:
        List of results with responses
    """
    import sglang as sgl

    sgl.set_default_backend(sgl.RuntimeEndpoint(backend_url))

    conversation = create_conversation_program()

    # Prepare batch inputs
    batch_inputs = [
        {"user_message": p["prompt"], "scenario": p.get("scenario", "general")}
        for p in prompts
    ]

    # Run in parallel
    start_time = time.time()
    results = conversation.run_batch(batch_inputs)
    elapsed = time.time() - start_time

    # Extract responses
    outputs = []
    for i, result in enumerate(results):
        outputs.append({
            "prompt": prompts[i]["prompt"],
            "scenario": prompts[i].get("scenario", "general"),
            "response": result["response"],
        })

    print(f"Processed {len(prompts)} prompts in {elapsed:.2f}s")
    print(f"Throughput: {len(prompts) / elapsed:.2f} prompts/second")

    return outputs


def generate_training_dialogues(
    scenarios: List[str],
    num_per_scenario: int = 10,
    backend_url: str = "http://localhost:30000",
) -> List[Dict[str, Any]]:
    """
    Generate synthetic training dialogues for data augmentation.

    Args:
        scenarios: List of scenario types
        num_per_scenario: Number of dialogues per scenario
        backend_url: URL of SGLang server

    Returns:
        List of generated dialogues
    """
    import sglang as sgl

    sgl.set_default_backend(sgl.RuntimeEndpoint(backend_url))

    dialogue_gen = create_dialogue_program()

    scenario_descriptions = {
        "greetings": "Dos personas se encuentran y se saludan",
        "farewells": "Dos amigos se despiden después de una reunión",
        "family": "Conversación entre miembros de una familia",
        "emotions": "Una persona comparte sus sentimientos con un amigo",
        "plans": "Amigos haciendo planes para el fin de semana",
        "requests": "Alguien pide un favor a otra persona",
        "apologies": "Una persona se disculpa por algo",
        "opinions": "Dos personas discuten sus opiniones sobre un tema",
        "small_talk": "Conversación casual sobre el tiempo o el día",
    }

    all_dialogues = []

    for scenario in scenarios:
        description = scenario_descriptions.get(scenario, scenario)
        print(f"Generating {num_per_scenario} dialogues for: {scenario}")

        batch_inputs = [
            {"scenario": description, "context": f"Variación {i+1}"}
            for i in range(num_per_scenario)
        ]

        results = dialogue_gen.run_batch(batch_inputs)

        for result in results:
            all_dialogues.append({
                "scenario": scenario,
                "dialogue": result["dialogue"],
            })

    return all_dialogues


# ============================================================
# Server Management
# ============================================================

def start_sglang_server(
    model_name: str,
    port: int = 30000,
    tp_size: int = 1,
):
    """
    Start an SGLang server for the model.

    The server provides high-throughput inference with:
    - RadixAttention for KV cache reuse
    - Continuous batching
    - Efficient memory management
    """
    import subprocess
    import sys

    cmd = [
        sys.executable, "-m", "sglang.launch_server",
        "--model-path", model_name,
        "--port", str(port),
        "--tp-size", str(tp_size),
    ]

    print(f"Starting SGLang server on port {port}")
    print(f"Model: {model_name}")
    print("\nServer will be available at:")
    print(f"  http://localhost:{port}")
    print("\nUse with SGLang client:")
    print(f'  sgl.set_default_backend(sgl.RuntimeEndpoint("http://localhost:{port}"))')

    subprocess.run(cmd)


# ============================================================
# Scenario Testing
# ============================================================

def run_scenario_tests(
    scenario: str,
    backend_url: str = "http://localhost:30000",
) -> List[Dict[str, Any]]:
    """Run predefined test prompts for a scenario."""
    import sglang as sgl

    sgl.set_default_backend(sgl.RuntimeEndpoint(backend_url))

    scenario_prompts = {
        "greetings": [
            "¡Hola! ¿Qué tal?",
            "Buenos días, ¿cómo estás?",
            "¡Buenas tardes! Cuánto tiempo sin verte.",
            "Hola, me llamo María. Encantada de conocerte.",
            "¿Qué hay? ¿Cómo va todo?",
        ],
        "farewells": [
            "Bueno, me tengo que ir. ¡Hasta luego!",
            "Ha sido un placer verte. ¡Cuídate!",
            "Adiós, nos vemos pronto.",
            "Que te vaya bien. ¡Hasta la próxima!",
            "Me voy ya. ¡Que tengas buen día!",
        ],
        "family": [
            "¿Cómo está tu familia?",
            "¿Tienes hermanos?",
            "¿Qué tal tus padres?",
            "Cuéntame de tu familia.",
            "¿Vives con tu familia?",
        ],
        "emotions": [
            "Hoy me siento muy feliz.",
            "Estoy un poco preocupado.",
            "Me siento triste hoy.",
            "Estoy muy emocionado por las noticias.",
            "No sé cómo me siento.",
        ],
        "plans": [
            "¿Qué planes tienes para el fin de semana?",
            "¿Quieres ir al cine mañana?",
            "¿Te apetece tomar un café?",
            "¿Quedamos esta tarde?",
            "¿Qué vas a hacer esta noche?",
        ],
        "requests": [
            "¿Me puedes ayudar con algo?",
            "¿Podrías hacerme un favor?",
            "Necesito tu ayuda, ¿puedes?",
            "¿Te importaría echarme una mano?",
            "¿Sería posible que me ayudaras?",
        ],
        "apologies": [
            "Lo siento mucho por llegar tarde.",
            "Perdona, no era mi intención.",
            "Disculpa si te he molestado.",
            "Perdóname, fue mi culpa.",
            "Lo siento, no volverá a pasar.",
        ],
        "opinions": [
            "¿Qué opinas sobre esto?",
            "¿Qué te parece la situación?",
            "¿Estás de acuerdo conmigo?",
            "¿Cuál es tu opinión?",
            "¿Qué piensas tú?",
        ],
    }

    prompts = scenario_prompts.get(scenario, scenario_prompts["greetings"])

    conversation = create_conversation_program()

    results = []
    for prompt in prompts:
        result = conversation.run(user_message=prompt, scenario=scenario)
        results.append({
            "prompt": prompt,
            "scenario": scenario,
            "response": result["response"],
        })
        print(f"Prompt: {prompt}")
        print(f"Response: {result['response']}\n")

    return results


def run_full_evaluation(
    output_file: str,
    backend_url: str = "http://localhost:30000",
):
    """Run evaluation on all scenarios."""
    scenarios = [
        "greetings", "farewells", "family", "emotions",
        "plans", "requests", "apologies", "opinions"
    ]

    all_results = {}

    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"Testing: {scenario.upper()}")
        print('='*60)

        results = run_scenario_tests(scenario, backend_url)
        all_results[scenario] = results

    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="SGLang integration for Catalan-Spanish model")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Start server
    serve_parser = subparsers.add_parser("serve", help="Start SGLang server")
    serve_parser.add_argument("--model", default="meta-llama/Llama-3.2-1B-Instruct")
    serve_parser.add_argument("--port", type=int, default=30000)
    serve_parser.add_argument("--tp-size", type=int, default=1)

    # Run scenarios
    scenario_parser = subparsers.add_parser("scenarios", help="Test specific scenario")
    scenario_parser.add_argument("--scenario", required=True,
                                 choices=["greetings", "farewells", "family", "emotions",
                                         "plans", "requests", "apologies", "opinions"])
    scenario_parser.add_argument("--backend", default="http://localhost:30000")

    # Full evaluation
    eval_parser = subparsers.add_parser("evaluate", help="Run full evaluation")
    eval_parser.add_argument("--output", default="eval_results.json")
    eval_parser.add_argument("--backend", default="http://localhost:30000")

    # Generate training data
    gen_parser = subparsers.add_parser("generate", help="Generate synthetic dialogues")
    gen_parser.add_argument("--output", default="synthetic_dialogues.json")
    gen_parser.add_argument("--num-per-scenario", type=int, default=10)
    gen_parser.add_argument("--backend", default="http://localhost:30000")

    args = parser.parse_args()

    if not check_sglang() and args.command != "serve":
        return

    if args.command == "serve":
        start_sglang_server(args.model, args.port, args.tp_size)
    elif args.command == "scenarios":
        run_scenario_tests(args.scenario, args.backend)
    elif args.command == "evaluate":
        run_full_evaluation(args.output, args.backend)
    elif args.command == "generate":
        scenarios = ["greetings", "farewells", "family", "emotions",
                    "plans", "requests", "apologies", "opinions"]
        dialogues = generate_training_dialogues(
            scenarios, args.num_per_scenario, args.backend
        )
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(dialogues, f, indent=2, ensure_ascii=False)
        print(f"Generated {len(dialogues)} dialogues to {args.output}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
