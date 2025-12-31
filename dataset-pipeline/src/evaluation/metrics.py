#!/usr/bin/env python3
"""
Evaluation metrics for user response scoring.

This module implements various metrics for evaluating Spanish/Catalan language responses:
- Vocabulary scoring by difficulty level
- Slang usage detection (Spanish and Catalan)
- BLEU score calculation
- Semantic similarity
- CEFR level determination
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import Counter

# Try to import optional dependencies
try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


# ============================================================================
# VOCABULARY DEFINITIONS
# ============================================================================

# Spanish slang terms (used across Spain)
SPANISH_SLANG = {
    "common": [
        "vale", "guay", "mola", "molar", "genial", "brutal", "increíble",
        "flipar", "flipas", "flipo", "flipando", "alucinar", "alucino",
        "currar", "curro", "pasta", "quedamos", "quedar", "finde",
        "rollo", "movida", "marcha", "fiesta", "botellón", "resaca",
        "tope", "mazo", "mogollón", "cantidad",
    ],
    "address": [
        "tío", "tía", "chaval", "chavala", "colega", "macho", "pavo", "pava",
    ],
    "reactions": [
        "hostia", "joder", "coño", "mierda", "puta", "cabrón",
        "gilipollas", "capullo", "imbécil",
    ],
    "expressions": [
        "qué pasada", "qué fuerte", "en serio", "qué va", "tal cual",
        "en plan", "de tranquis", "la caña", "la leche",
    ],
}

# Catalan slang terms (Barcelona/Catalonia specific)
CATALAN_SLANG = {
    "address": [
        "nen", "nena", "nano", "nana", "home", "macu", "maco", "bonica",
    ],
    "fillers": [
        "apa", "vinga", "doncs", "va", "clar", "escolta", "ostras", "che",
    ],
    "reactions": [
        "hòstia", "hostia", "collons", "merda", "cony", "flipar", "flipat",
        "quina passada", "que fort", "ni de conya", "de debò",
    ],
    "expressions": [
        "ja està", "és veritat", "passa res", "molt heavy", "top",
        "quina mandra", "quin pal", "em fa pal", "estic mort", "estic morta",
    ],
    "verbs_phrases": [
        "quedem", "sortir de festa", "fer el vermut", "ens la fotem",
        "anar torrat", "anar molt content", "petar-ho", "ho peta",
        "plegar", "currar", "curro",
    ],
    "money": [
        "calés", "pelat", "pelada", "estic pelat",
    ],
    "catalan_words": [
        "adéu", "gràcies", "si us plau", "bon dia", "bona nit", "molt bé",
    ],
}

# Vocabulary by difficulty level (scenario-agnostic)
VOCABULARY_LEVELS = {
    "beginner": [
        "hola", "adiós", "buenos días", "buenas tardes", "buenas noches",
        "gracias", "por favor", "sí", "no", "bien", "mal",
        "mamá", "papá", "hermano", "hermana", "amigo", "amiga",
        "feliz", "triste", "casa", "trabajo", "escuela",
    ],
    "intermediate": [
        "qué tal", "cómo estás", "encantado", "mucho gusto", "nos vemos",
        "hasta pronto", "cuídate", "quedamos", "te apetece",
        "contento", "preocupado", "enfadado", "nervioso",
        "familia", "padres", "hijos", "abuelos",
        "creo que", "pienso que", "me parece",
    ],
    "advanced": [
        "qué hay", "cómo va", "un placer", "igualmente",
        "que te vaya bien", "ya nos veremos",
        "emocionado", "agotado", "aliviado", "frustrado",
        "parientes", "suegros", "cuñado", "sobrino",
        "estoy de acuerdo", "no estoy de acuerdo", "en mi opinión",
        "sería posible", "qué te parece si", "tengo previsto",
    ],
}


# ============================================================================
# SCORING FUNCTIONS
# ============================================================================

def tokenize_spanish(text: str) -> List[str]:
    """Simple Spanish tokenizer."""
    # Lowercase and split on whitespace/punctuation
    text = text.lower()
    # Keep accented characters
    tokens = re.findall(r"[a-záéíóúüñ]+", text)
    return tokens


def calculate_vocabulary_score(
    text: str,
    scenario_vocabulary: Optional[Dict] = None
) -> Dict:
    """
    Calculate vocabulary score based on word difficulty levels.

    Args:
        text: User response text
        scenario_vocabulary: Optional scenario-specific vocabulary dict

    Returns:
        Dict with score breakdown:
        {
            "total_score": int,
            "beginner": {"count": int, "words": list},
            "intermediate": {"count": int, "words": list},
            "advanced": {"count": int, "words": list},
            "regional": {"count": int, "words": list},
        }
    """
    tokens = tokenize_spanish(text)
    text_lower = text.lower()

    # Use scenario vocabulary if provided, otherwise use defaults
    vocab = scenario_vocabulary or VOCABULARY_LEVELS

    results = {
        "total_score": 0,
        "beginner": {"count": 0, "words": [], "points": 1},
        "intermediate": {"count": 0, "words": [], "points": 2},
        "advanced": {"count": 0, "words": [], "points": 3},
        "regional": {"count": 0, "words": [], "points": 4},
    }

    # Check each vocabulary level
    for level in ["beginner", "intermediate", "advanced"]:
        words = vocab.get(level, VOCABULARY_LEVELS.get(level, []))
        for word in words:
            if word.lower() in text_lower:
                results[level]["count"] += 1
                results[level]["words"].append(word)

    # Check regional/slang vocabulary
    regional_words = []
    if "catalan_regional" in vocab:
        regional_words.extend(vocab["catalan_regional"])
    if "spanish_slang" in vocab and isinstance(vocab["spanish_slang"], dict):
        regional_words.extend(vocab["spanish_slang"].get("terms", []))
    if "catalan_slang" in vocab and isinstance(vocab["catalan_slang"], dict):
        regional_words.extend(vocab["catalan_slang"].get("terms", []))

    # Also check our hardcoded slang lists
    for category_words in CATALAN_SLANG.values():
        regional_words.extend(category_words)
    for category_words in SPANISH_SLANG.values():
        regional_words.extend(category_words)

    regional_words = list(set(regional_words))  # Deduplicate

    for word in regional_words:
        if word.lower() in text_lower:
            results["regional"]["count"] += 1
            results["regional"]["words"].append(word)

    # Calculate total score
    results["total_score"] = (
        results["beginner"]["count"] * 1 +
        results["intermediate"]["count"] * 2 +
        results["advanced"]["count"] * 3 +
        results["regional"]["count"] * 4
    )

    # Cap at 15 for CEFR mapping
    results["capped_score"] = min(results["total_score"], 15)

    return results


def calculate_slang_rate(text: str) -> Dict[str, float]:
    """
    Calculate slang usage rates for Spanish and Catalan.

    Returns:
        Dict with rates:
        {
            "spanish_slang_rate": float,
            "catalan_slang_rate": float,
            "combined_rate": float,
            "spanish_slang_found": list,
            "catalan_slang_found": list,
        }
    """
    tokens = tokenize_spanish(text)
    text_lower = text.lower()
    total_words = len(tokens) if tokens else 1

    spanish_found = []
    catalan_found = []

    # Check Spanish slang
    for category, words in SPANISH_SLANG.items():
        for word in words:
            if word.lower() in text_lower:
                spanish_found.append(word)

    # Check Catalan slang
    for category, words in CATALAN_SLANG.items():
        for word in words:
            if word.lower() in text_lower:
                catalan_found.append(word)

    # Deduplicate
    spanish_found = list(set(spanish_found))
    catalan_found = list(set(catalan_found))

    return {
        "spanish_slang_rate": len(spanish_found) / total_words,
        "catalan_slang_rate": len(catalan_found) / total_words,
        "combined_rate": (len(spanish_found) + len(catalan_found)) / total_words,
        "spanish_slang_found": spanish_found,
        "catalan_slang_found": catalan_found,
    }


def calculate_bleu_score(
    user_response: str,
    ground_truth: str,
    smoothing: bool = True
) -> float:
    """
    Calculate BLEU score between user response and ground truth.

    Args:
        user_response: User's text
        ground_truth: Reference text
        smoothing: Apply smoothing for short sentences

    Returns:
        BLEU score (0-1)
    """
    if not NLTK_AVAILABLE:
        # Fallback: simple word overlap
        user_tokens = set(tokenize_spanish(user_response))
        ref_tokens = set(tokenize_spanish(ground_truth))
        if not ref_tokens:
            return 0.0
        overlap = len(user_tokens & ref_tokens)
        return overlap / len(ref_tokens)

    user_tokens = tokenize_spanish(user_response)
    ref_tokens = tokenize_spanish(ground_truth)

    if not user_tokens or not ref_tokens:
        return 0.0

    try:
        if smoothing:
            smoothing_fn = SmoothingFunction().method1
            score = sentence_bleu(
                [ref_tokens],
                user_tokens,
                smoothing_function=smoothing_fn
            )
        else:
            score = sentence_bleu([ref_tokens], user_tokens)
        return score
    except Exception:
        return 0.0


def calculate_semantic_similarity(
    user_response: str,
    ground_truth: str,
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
) -> float:
    """
    Calculate semantic similarity using sentence embeddings.

    Args:
        user_response: User's text
        ground_truth: Reference text
        model_name: Sentence transformer model

    Returns:
        Cosine similarity (0-1)
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        # Fallback: word overlap Jaccard similarity
        user_tokens = set(tokenize_spanish(user_response))
        ref_tokens = set(tokenize_spanish(ground_truth))
        if not user_tokens and not ref_tokens:
            return 1.0
        if not user_tokens or not ref_tokens:
            return 0.0
        intersection = len(user_tokens & ref_tokens)
        union = len(user_tokens | ref_tokens)
        return intersection / union if union > 0 else 0.0

    try:
        model = SentenceTransformer(model_name)
        embeddings = model.encode([user_response, ground_truth])
        # Cosine similarity
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(similarity)
    except Exception:
        return 0.0


def determine_cefr_level(vocabulary_score: int, grammar_score: float = 100) -> str:
    """
    Determine CEFR level based on vocabulary and grammar scores.

    Args:
        vocabulary_score: Score from calculate_vocabulary_score (0-15)
        grammar_score: Grammar score (0-100)

    Returns:
        CEFR level: "A1", "A2", "B1", or "B2"
    """
    # Weight vocabulary more heavily
    combined = (vocabulary_score / 15 * 0.6) + (grammar_score / 100 * 0.4)

    if combined < 0.25:
        return "A1"
    elif combined < 0.45:
        return "A2"
    elif combined < 0.70:
        return "B1"
    else:
        return "B2"


def calculate_composite_score(metrics: Dict) -> float:
    """
    Calculate weighted composite score from all metrics.

    Args:
        metrics: Dict containing individual metric scores

    Returns:
        Composite score (0-1)
    """
    weights = {
        "vocabulary_score": 0.25,  # Normalized to 0-1
        "slang_rate": 0.15,
        "bleu_score": 0.15,
        "semantic_similarity": 0.15,
        "grammar_score": 0.20,  # Normalized to 0-1
        "human_naturalness": 0.10,  # If available
    }

    composite = 0.0
    total_weight = 0.0

    for key, weight in weights.items():
        if key in metrics and metrics[key] is not None:
            value = metrics[key]
            # Normalize vocabulary_score (max 15) and grammar_score (max 100)
            if key == "vocabulary_score":
                value = min(value, 15) / 15
            elif key == "grammar_score":
                value = value / 100
            elif key == "human_naturalness":
                value = value / 5  # 1-5 scale

            composite += value * weight
            total_weight += weight

    if total_weight > 0:
        composite = composite / total_weight

    return composite


def generate_feedback(metrics: Dict, scenario: str = "general") -> List[str]:
    """
    Generate actionable feedback based on metrics.

    Args:
        metrics: Dict containing evaluation metrics
        scenario: Conversation scenario type

    Returns:
        List of feedback strings
    """
    feedback = []

    # Vocabulary feedback
    vocab = metrics.get("vocabulary_breakdown", {})
    if vocab.get("regional", {}).get("count", 0) > 0:
        regional_words = vocab["regional"]["words"]
        feedback.append(f"Great use of regional expressions: {', '.join(regional_words[:3])}")
    elif metrics.get("vocabulary_score", 0) < 5:
        feedback.append("Try incorporating more varied vocabulary")

    # Slang feedback
    slang = metrics.get("slang_rate", {})
    if slang.get("catalan_slang_found"):
        feedback.append(f"Good Catalan slang usage: {', '.join(slang['catalan_slang_found'][:3])}")
    elif slang.get("combined_rate", 0) < 0.05:
        feedback.append("Consider using more colloquial expressions for natural speech")

    # Similarity feedback
    if metrics.get("semantic_similarity", 0) > 0.8:
        feedback.append("Excellent contextual relevance!")
    elif metrics.get("semantic_similarity", 0) < 0.5:
        feedback.append("Try to stay closer to the conversation topic")

    # CEFR feedback
    cefr = metrics.get("cefr_level", "A1")
    if cefr in ["B1", "B2"]:
        feedback.append(f"Strong {cefr} level performance!")
    elif cefr == "A1":
        feedback.append("Keep practicing - aim for more complex sentences")

    return feedback


# ============================================================================
# BATCH EVALUATION
# ============================================================================

def evaluate_batch(
    responses: List[Dict],
    ground_truth_file: Optional[str] = None
) -> List[Dict]:
    """
    Evaluate a batch of user responses.

    Args:
        responses: List of dicts with 'user_response' and 'ground_truth' keys
        ground_truth_file: Optional path to ground truth JSON

    Returns:
        List of evaluation result dicts
    """
    results = []

    for item in responses:
        user_response = item.get("user_response", "")
        ground_truth = item.get("ground_truth", "")
        scenario = item.get("scenario", "general")

        vocab = calculate_vocabulary_score(user_response)
        slang = calculate_slang_rate(user_response)
        bleu = calculate_bleu_score(user_response, ground_truth)
        semantic = calculate_semantic_similarity(user_response, ground_truth)
        cefr = determine_cefr_level(vocab["total_score"])

        metrics = {
            "vocabulary_score": vocab["total_score"],
            "vocabulary_breakdown": vocab,
            "slang_rate": slang,
            "bleu_score": bleu,
            "semantic_similarity": semantic,
            "grammar_score": 100,  # Placeholder - needs SpaCy integration
            "cefr_level": cefr,
        }

        metrics["composite_score"] = calculate_composite_score(metrics)
        metrics["feedback"] = generate_feedback(metrics, scenario)
        metrics["id"] = item.get("id", "")
        metrics["scenario"] = scenario

        results.append(metrics)

    return results


if __name__ == "__main__":
    # Test the metrics
    test_response = "¡Hola, nen! ¿Qué tal? Mola mucho verte aquí."
    test_ground_truth = "¡Hola! ¿Qué tal, nen? ¿Cómo va todo?"

    print("Testing metrics module...")
    print(f"\nUser response: {test_response}")
    print(f"Ground truth: {test_ground_truth}")

    vocab = calculate_vocabulary_score(test_response)
    print(f"\nVocabulary score: {vocab['total_score']}")
    print(f"  Regional words: {vocab['regional']['words']}")

    slang = calculate_slang_rate(test_response)
    print(f"\nSlang rates:")
    print(f"  Spanish: {slang['spanish_slang_rate']:.2%}")
    print(f"  Catalan: {slang['catalan_slang_rate']:.2%}")
    print(f"  Found: {slang['spanish_slang_found'] + slang['catalan_slang_found']}")

    bleu = calculate_bleu_score(test_response, test_ground_truth)
    print(f"\nBLEU score: {bleu:.3f}")

    semantic = calculate_semantic_similarity(test_response, test_ground_truth)
    print(f"Semantic similarity: {semantic:.3f}")

    cefr = determine_cefr_level(vocab['total_score'])
    print(f"\nCEFR level: {cefr}")
