"""
Scenario Classifier Module
Classifies dialog entries into Personal & Social module scenarios.
Uses both keyword matching and semantic similarity.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging
import yaml
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional: sentence-transformers for semantic classification
try:
    from sentence_transformers import SentenceTransformer
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Using keyword-only classification.")


@dataclass
class ClassificationResult:
    """Result of scenario classification."""
    scenario: str
    confidence: float
    method: str  # 'keyword', 'semantic', or 'hybrid'
    matched_keywords: List[str]
    secondary_scenarios: List[Tuple[str, float]]  # Other possible scenarios


class KeywordClassifier:
    """Fast keyword-based scenario classifier."""

    def __init__(self, config_path: str = "config/settings.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.scenarios = self.config.get('personal_social_scenarios', {})

        # Build keyword index for fast lookup
        self.keyword_to_scenario = {}
        self.scenario_keywords = {}

        for scenario_name, scenario_data in self.scenarios.items():
            keywords = scenario_data.get('keywords', [])
            self.scenario_keywords[scenario_name] = set(k.lower() for k in keywords)

            for keyword in keywords:
                key = keyword.lower()
                if key not in self.keyword_to_scenario:
                    self.keyword_to_scenario[key] = []
                self.keyword_to_scenario[key].append(scenario_name)

    def classify(self, text: str) -> ClassificationResult:
        """
        Classify text using keyword matching.

        Returns ClassificationResult with scenario and confidence.
        """
        text_lower = text.lower()
        scenario_scores = defaultdict(float)
        matched_keywords = defaultdict(list)

        # Count keyword matches per scenario
        for keyword, scenarios in self.keyword_to_scenario.items():
            # Use word boundary matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = len(re.findall(pattern, text_lower))

            if matches > 0:
                for scenario in scenarios:
                    # Weight longer keywords more (more specific)
                    weight = len(keyword.split()) * matches
                    scenario_scores[scenario] += weight
                    matched_keywords[scenario].append(keyword)

        if not scenario_scores:
            return ClassificationResult(
                scenario="unclassified",
                confidence=0.0,
                method="keyword",
                matched_keywords=[],
                secondary_scenarios=[]
            )

        # Normalize scores to confidence values
        total_score = sum(scenario_scores.values())
        normalized_scores = {
            s: score / total_score
            for s, score in scenario_scores.items()
        }

        # Get top scenario
        sorted_scenarios = sorted(
            normalized_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_scenario = sorted_scenarios[0][0]
        top_confidence = sorted_scenarios[0][1]

        # Get secondary scenarios (confidence > 0.1)
        secondary = [
            (s, conf) for s, conf in sorted_scenarios[1:]
            if conf > 0.1
        ]

        return ClassificationResult(
            scenario=top_scenario,
            confidence=top_confidence,
            method="keyword",
            matched_keywords=matched_keywords[top_scenario],
            secondary_scenarios=secondary
        )


class SemanticClassifier:
    """
    Semantic similarity-based classifier using sentence embeddings.
    More accurate but slower than keyword matching.
    """

    # Representative examples for each scenario
    SCENARIO_EXAMPLES = {
        "greetings": [
            "¡Hola! ¿Cómo estás?",
            "Buenos días, ¿qué tal?",
            "Encantado de conocerte",
            "Mucho gusto, soy María",
            "¿Qué hay? ¿Todo bien?",
        ],
        "farewells": [
            "Adiós, hasta pronto",
            "Nos vemos mañana",
            "Cuídate mucho",
            "Que te vaya bien",
            "Hasta luego, fue un placer",
        ],
        "family": [
            "Mi madre está en casa",
            "Voy a visitar a mis abuelos",
            "Mi hermano estudia medicina",
            "Los niños están jugando",
            "Cena familiar este domingo",
        ],
        "emotions": [
            "Estoy muy feliz hoy",
            "Me siento un poco triste",
            "Te quiero mucho",
            "Estoy preocupado por el examen",
            "Me hace muy feliz verte",
        ],
        "opinions": [
            "Creo que tienes razón",
            "En mi opinión, es mejor esperar",
            "No estoy de acuerdo contigo",
            "Me parece una buena idea",
            "Pienso que deberíamos hacerlo",
        ],
        "plans": [
            "¿Quedamos el sábado?",
            "Vamos a cenar esta noche",
            "¿Te apetece ir al cine?",
            "Este fin de semana podemos salir",
            "¿Qué planes tienes para mañana?",
        ],
        "requests": [
            "¿Puedes ayudarme con esto?",
            "Necesito un favor",
            "¿Podrías pasarme la sal?",
            "Por favor, ayúdame",
            "¿Te importaría esperarme?",
        ],
        "apologies": [
            "Lo siento mucho",
            "Perdona por llegar tarde",
            "Fue mi culpa",
            "Disculpa las molestias",
            "No era mi intención ofenderte",
        ],
        "small_talk": [
            "¡Qué buen tiempo hace hoy!",
            "¿Qué tal el trabajo?",
            "Hace mucho calor últimamente",
            "¿Qué hay de nuevo?",
            "¿Cómo va todo por casa?",
        ],
    }

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        if not SEMANTIC_AVAILABLE:
            raise ImportError("sentence-transformers required for SemanticClassifier")

        logger.info(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # Pre-compute scenario embeddings
        self.scenario_embeddings = {}
        for scenario, examples in self.SCENARIO_EXAMPLES.items():
            embeddings = self.model.encode(examples)
            # Use mean embedding as scenario prototype
            self.scenario_embeddings[scenario] = np.mean(embeddings, axis=0)

        logger.info("Semantic classifier initialized")

    def classify(self, text: str) -> ClassificationResult:
        """
        Classify text using semantic similarity.
        """
        # Encode input text
        text_embedding = self.model.encode([text])[0]

        # Calculate similarity to each scenario
        similarities = {}
        for scenario, scenario_emb in self.scenario_embeddings.items():
            # Cosine similarity
            similarity = np.dot(text_embedding, scenario_emb) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(scenario_emb)
            )
            similarities[scenario] = float(similarity)

        # Sort by similarity
        sorted_scenarios = sorted(
            similarities.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_scenario = sorted_scenarios[0][0]
        top_similarity = sorted_scenarios[0][1]

        # Convert similarity to confidence (scale to 0-1)
        # Cosine similarity ranges from -1 to 1, typically 0.3-0.8 for related text
        confidence = max(0, min(1, (top_similarity - 0.3) / 0.5))

        secondary = [
            (s, max(0, min(1, (sim - 0.3) / 0.5)))
            for s, sim in sorted_scenarios[1:4]  # Top 3 alternatives
            if sim > 0.4
        ]

        return ClassificationResult(
            scenario=top_scenario,
            confidence=confidence,
            method="semantic",
            matched_keywords=[],
            secondary_scenarios=secondary
        )


class HybridClassifier:
    """
    Combines keyword and semantic classification for best results.
    """

    def __init__(
        self,
        config_path: str = "config/settings.yaml",
        use_semantic: bool = True,
        keyword_weight: float = 0.4,
        semantic_weight: float = 0.6
    ):
        self.config_path = config_path
        self.keyword_classifier = KeywordClassifier(config_path)

        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        if self.use_semantic:
            self.semantic_classifier = SemanticClassifier()
        else:
            self.semantic_classifier = None

        self.keyword_weight = keyword_weight
        self.semantic_weight = semantic_weight

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.min_confidence = self.config['processing']['min_classification_confidence']

    def classify(self, text: str) -> ClassificationResult:
        """
        Classify using hybrid approach.
        """
        # Always run keyword classification
        keyword_result = self.keyword_classifier.classify(text)

        if not self.use_semantic:
            return keyword_result

        # Run semantic classification
        semantic_result = self.semantic_classifier.classify(text)

        # Combine results
        if keyword_result.scenario == semantic_result.scenario:
            # Agreement - boost confidence
            combined_confidence = min(
                1.0,
                keyword_result.confidence * self.keyword_weight +
                semantic_result.confidence * self.semantic_weight + 0.1
            )
            return ClassificationResult(
                scenario=keyword_result.scenario,
                confidence=combined_confidence,
                method="hybrid",
                matched_keywords=keyword_result.matched_keywords,
                secondary_scenarios=keyword_result.secondary_scenarios
            )

        # Disagreement - use weighted combination
        keyword_score = keyword_result.confidence * self.keyword_weight
        semantic_score = semantic_result.confidence * self.semantic_weight

        if keyword_score >= semantic_score:
            # Keyword wins
            combined_confidence = keyword_result.confidence * 0.8  # Penalize disagreement
            return ClassificationResult(
                scenario=keyword_result.scenario,
                confidence=combined_confidence,
                method="hybrid-keyword",
                matched_keywords=keyword_result.matched_keywords,
                secondary_scenarios=[
                    (semantic_result.scenario, semantic_result.confidence)
                ] + keyword_result.secondary_scenarios
            )
        else:
            # Semantic wins
            combined_confidence = semantic_result.confidence * 0.8
            return ClassificationResult(
                scenario=semantic_result.scenario,
                confidence=combined_confidence,
                method="hybrid-semantic",
                matched_keywords=[],
                secondary_scenarios=[
                    (keyword_result.scenario, keyword_result.confidence)
                ] + semantic_result.secondary_scenarios
            )

    def classify_batch(
        self,
        texts: List[str],
        show_progress: bool = True
    ) -> List[ClassificationResult]:
        """
        Classify multiple texts efficiently.
        """
        results = []

        if show_progress:
            try:
                from tqdm import tqdm
                texts = tqdm(texts, desc="Classifying dialogs")
            except ImportError:
                pass

        for text in texts:
            result = self.classify(text)
            results.append(result)

        return results


def classify_dialogs(
    dialogs_file: str,
    output_file: str,
    config_path: str = "config/settings.yaml",
    use_semantic: bool = True
) -> Dict[str, int]:
    """
    Classify all dialogs from a JSON file.

    Args:
        dialogs_file: Path to JSON file with extracted dialogs
        output_file: Path to save classified dialogs
        config_path: Path to configuration file
        use_semantic: Whether to use semantic classification

    Returns:
        Dictionary with scenario counts
    """
    # Load dialogs
    with open(dialogs_file, 'r', encoding='utf-8') as f:
        dialogs = json.load(f)

    logger.info(f"Loaded {len(dialogs)} dialogs for classification")

    # Initialize classifier
    classifier = HybridClassifier(
        config_path=config_path,
        use_semantic=use_semantic
    )

    # Load config for min confidence
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    min_confidence = config['processing']['min_classification_confidence']

    # Classify each dialog
    classified_dialogs = []
    scenario_counts = defaultdict(int)

    for dialog in dialogs:
        text = dialog['text']
        result = classifier.classify(text)

        # Update dialog with classification
        dialog['scenario'] = result.scenario
        dialog['scenario_confidence'] = result.confidence
        dialog['classification_method'] = result.method
        dialog['matched_keywords'] = result.matched_keywords
        dialog['secondary_scenarios'] = [
            {"scenario": s, "confidence": c}
            for s, c in result.secondary_scenarios
        ]

        # Only include if confidence meets threshold
        if result.confidence >= min_confidence:
            classified_dialogs.append(dialog)
            scenario_counts[result.scenario] += 1
        else:
            scenario_counts['low_confidence'] += 1

    # Save classified dialogs
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(classified_dialogs, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(classified_dialogs)} classified dialogs to {output_file}")
    logger.info(f"Scenario distribution: {dict(scenario_counts)}")

    return dict(scenario_counts)


def print_classification_report(scenario_counts: Dict[str, int]):
    """Print a formatted classification report."""
    print("\n" + "=" * 50)
    print("CLASSIFICATION REPORT")
    print("=" * 50)

    total = sum(scenario_counts.values())
    for scenario, count in sorted(scenario_counts.items(), key=lambda x: -x[1]):
        percentage = (count / total) * 100 if total > 0 else 0
        bar = "█" * int(percentage / 2)
        print(f"{scenario:20} {count:6} ({percentage:5.1f}%) {bar}")

    print("=" * 50)
    print(f"{'TOTAL':20} {total:6}")
    print("=" * 50)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "data/processed/classified_dialogs.json"

        counts = classify_dialogs(
            input_file,
            output_file,
            use_semantic=SEMANTIC_AVAILABLE
        )
        print_classification_report(counts)
    else:
        print("Usage: python scenario_classifier.py <dialogs.json> [output.json]")
