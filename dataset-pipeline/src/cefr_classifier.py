#!/usr/bin/env python3
"""
CEFR-Aligned Dialogue Classifier

Classifies Spanish dialogues according to the Common European Framework of Reference
for Languages (CEFR) using a mixed approach:
1. Rule-based pre-filtering with spaCy for linguistic feature extraction
2. LLM-based classification using Claude API for nuanced assessment

CEFR Levels:
- A1-A2: Beginner (present tense, simple sentences, high-frequency vocabulary)
- B1: Intermediate (multiple tenses, compound sentences, opinion expressions)
- B2: Upper-Intermediate (subjunctive, complex clauses, abstract vocabulary)
- C1-C2: Advanced/Mastery (literary constructions, sophisticated discourse)
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

# Optional dependencies
try:
    import spacy
    SPACY_AVAILABLE = True
except (ImportError, Exception) as e:
    SPACY_AVAILABLE = False
    logging.warning(f"spaCy not available: {e}")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CEFRClassification:
    """Result of CEFR classification."""
    cefr_level: str  # A1, A2, B1, B2, C1, C2
    simplified_level: str  # beginner, intermediate, advanced, mastery
    confidence: float
    reasoning: str
    linguistic_features: Dict
    method: str  # rule_based, llm, hybrid


# CEFR Level Criteria
CEFR_CRITERIA = {
    "A1": {
        "description": "Complete beginner",
        "verb_tenses": ["present indicative"],
        "sentence_complexity": "simple",
        "vocabulary": "basic, high-frequency",
        "examples": [
            "Hola, ¿cómo estás?",
            "Me llamo María.",
            "Sí, gracias.",
        ]
    },
    "A2": {
        "description": "Elementary",
        "verb_tenses": ["present", "basic past (preterite)"],
        "sentence_complexity": "simple with basic conjunctions",
        "vocabulary": "everyday situations",
        "examples": [
            "Ayer fui al cine.",
            "¿Dónde está la estación?",
            "Me gusta mucho este restaurante.",
        ]
    },
    "B1": {
        "description": "Intermediate",
        "verb_tenses": ["present", "preterite", "imperfect", "future", "conditional"],
        "sentence_complexity": "compound sentences, basic subordination",
        "vocabulary": "opinions, plans, experiences",
        "examples": [
            "Creo que deberíamos ir mañana.",
            "Cuando era niño, vivía en Barcelona.",
            "Si tengo tiempo, te llamaré.",
        ]
    },
    "B2": {
        "description": "Upper-intermediate",
        "verb_tenses": ["all indicative", "present subjunctive", "conditional perfect"],
        "sentence_complexity": "complex clauses, relative clauses, conditionals",
        "vocabulary": "abstract concepts, idiomatic expressions",
        "examples": [
            "Si hubiera sabido que venías, habría preparado algo.",
            "Es importante que todos participen.",
            "Por mucho que lo intente, no consigo entenderlo.",
        ]
    },
    "C1": {
        "description": "Advanced",
        "verb_tenses": ["all tenses including imperfect subjunctive", "pluperfect subjunctive"],
        "sentence_complexity": "nested subordination, sophisticated discourse markers",
        "vocabulary": "nuanced, technical, literary",
        "examples": [
            "Por mucho que insistas, dudo que consiga convencerle.",
            "No obstante, habría que considerar otras alternativas.",
            "De haber tenido la oportunidad, me hubiera quedado más tiempo.",
        ]
    },
    "C2": {
        "description": "Mastery",
        "verb_tenses": ["complete mastery including archaic forms"],
        "sentence_complexity": "native-like complexity, literary style",
        "vocabulary": "full range including colloquial, literary, archaic",
        "examples": [
            "Habría sido menester que lo supiéramos de antemano.",
            "Sea como fuere, la decisión ya está tomada.",
            "Cuanto más lo pienso, menos sentido le encuentro.",
        ]
    }
}

LEVEL_MAPPING = {
    "A1": "beginner",
    "A2": "beginner",
    "B1": "intermediate",
    "B2": "advanced",
    "C1": "mastery",
    "C2": "mastery",
}

# Spanish verb patterns for rule-based detection
SUBJUNCTIVE_MARKERS = [
    r'\b(que|aunque|para que|sin que|antes de que|hasta que|con tal de que)\b.*\b(sea|esté|tenga|haga|pueda|quiera|sepa|vaya|dé|diga)\b',
    r'\b(quisiera|pudiera|tuviera|fuera|hubiera|hiciera|supiera|dijera)\b',
    r'\bsi\s+\w+ra\b',  # si tuviera, si pudiera
]

PAST_TENSE_MARKERS = [
    r'\b(fue|fui|fuiste|fuimos|fueron)\b',
    r'\b(estuvo|estuve|estuviste|estuvimos|estuvieron)\b',
    r'\b(tuvo|tuve|tuviste|tuvimos|tuvieron)\b',
    r'\b(hizo|hice|hiciste|hicimos|hicieron)\b',
    r'\b\w+(ó|amos|aron|ió|ieron|í|iste|imos|ísteis)\b',  # Regular preterite
]

IMPERFECT_MARKERS = [
    r'\b(era|eras|éramos|eran)\b',
    r'\b(estaba|estabas|estábamos|estaban)\b',
    r'\b(tenía|tenías|teníamos|tenían)\b',
    r'\b\w+(aba|abas|ábamos|aban|ía|ías|íamos|ían)\b',
]

CONDITIONAL_MARKERS = [
    r'\b(sería|serías|seríamos|serían)\b',
    r'\b(estaría|estarías|estaríamos|estarían)\b',
    r'\b(tendría|tendrías|tendríamos|tendrían)\b',
    r'\b\w+(ría|rías|ríamos|rían)\b',
]

FUTURE_MARKERS = [
    r'\b(será|serás|seremos|serán)\b',
    r'\b(estará|estarás|estaremos|estarán)\b',
    r'\b\w+(ré|rás|rá|remos|réis|rán)\b',
]

ADVANCED_DISCOURSE_MARKERS = [
    "no obstante", "con todo", "por más que", "aun así", "sin embargo",
    "ahora bien", "en cualquier caso", "sea como fuere", "de ahí que",
    "dado que", "puesto que", "a pesar de que", "si bien",
]


class RuleBasedAnalyzer:
    """
    Analyzes linguistic features of Spanish text for CEFR classification.
    Uses spaCy for POS tagging and pattern matching for verb tense detection.
    """

    def __init__(self):
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("es_core_news_sm")
                logger.info("Loaded spaCy Spanish model")
            except OSError:
                logger.warning("Spanish spaCy model not found. Run: python -m spacy download es_core_news_sm")

    def analyze(self, text: str) -> Dict:
        """
        Extract linguistic features from text.

        Returns dict with:
        - word_count: number of words
        - sentence_count: number of sentences
        - avg_sentence_length: average words per sentence
        - verb_tenses: detected tenses
        - has_subjunctive: boolean
        - has_conditional: boolean
        - complexity_score: 0-100 score
        """
        text_lower = text.lower()
        features = {
            "word_count": len(text.split()),
            "sentence_count": max(1, text.count('.') + text.count('?') + text.count('!')),
            "avg_sentence_length": 0,
            "verb_tenses": [],
            "has_subjunctive": False,
            "has_conditional": False,
            "has_past_tense": False,
            "has_imperfect": False,
            "has_future": False,
            "advanced_discourse_markers": [],
            "complexity_score": 0,
        }

        features["avg_sentence_length"] = features["word_count"] / features["sentence_count"]

        # Check for verb tenses using patterns
        for pattern in SUBJUNCTIVE_MARKERS:
            if re.search(pattern, text_lower):
                features["has_subjunctive"] = True
                features["verb_tenses"].append("subjunctive")
                break

        for pattern in CONDITIONAL_MARKERS:
            if re.search(pattern, text_lower):
                features["has_conditional"] = True
                features["verb_tenses"].append("conditional")
                break

        for pattern in PAST_TENSE_MARKERS:
            if re.search(pattern, text_lower):
                features["has_past_tense"] = True
                features["verb_tenses"].append("preterite")
                break

        for pattern in IMPERFECT_MARKERS:
            if re.search(pattern, text_lower):
                features["has_imperfect"] = True
                features["verb_tenses"].append("imperfect")
                break

        for pattern in FUTURE_MARKERS:
            if re.search(pattern, text_lower):
                features["verb_tenses"].append("future")
                break

        # Check for advanced discourse markers
        for marker in ADVANCED_DISCOURSE_MARKERS:
            if marker in text_lower:
                features["advanced_discourse_markers"].append(marker)

        # Calculate complexity score (0-100)
        score = 0
        score += min(20, features["word_count"] * 2)  # Length factor
        score += min(15, features["avg_sentence_length"] * 2)  # Sentence complexity
        score += 15 if features["has_subjunctive"] else 0
        score += 10 if features["has_conditional"] else 0
        score += 5 if features["has_past_tense"] else 0
        score += 5 if features["has_imperfect"] else 0
        score += len(features["advanced_discourse_markers"]) * 10

        features["complexity_score"] = min(100, score)
        features["verb_tenses"] = list(set(features["verb_tenses"]))

        return features

    def estimate_cefr(self, features: Dict) -> Tuple[str, float]:
        """
        Estimate CEFR level based on linguistic features.
        Returns (level, confidence).
        """
        score = features["complexity_score"]

        # Rule-based estimation
        if features["has_subjunctive"] and features["advanced_discourse_markers"]:
            return ("C1", 0.7)
        elif features["has_subjunctive"]:
            return ("B2", 0.7)
        elif features["has_conditional"] or (features["has_past_tense"] and features["has_imperfect"]):
            return ("B1", 0.6)
        elif features["has_past_tense"]:
            return ("A2", 0.6)
        elif features["word_count"] <= 10 and not features["verb_tenses"]:
            return ("A1", 0.7)
        else:
            # Default based on complexity score
            if score >= 70:
                return ("B2", 0.5)
            elif score >= 50:
                return ("B1", 0.5)
            elif score >= 30:
                return ("A2", 0.5)
            else:
                return ("A1", 0.5)


class LLMClassifier:
    """
    Uses Claude API to classify dialogues according to CEFR levels.
    """

    SYSTEM_PROMPT = """You are an expert in the Common European Framework of Reference for Languages (CEFR)
for Spanish language assessment. Your task is to classify Spanish dialogue excerpts according to
their linguistic complexity level.

CEFR Level Criteria for Spanish:

A1-A2 (Beginner):
- Present tense only (or basic past)
- Simple sentences with 1-2 clauses
- High-frequency, concrete vocabulary
- Short responses (typically 1-10 words)
- Example: "Hola, ¿cómo estás?" "Bien, gracias."

B1 (Intermediate):
- Multiple tenses (preterite, imperfect, future)
- Compound sentences with conjunctions (pero, porque, aunque)
- Opinion expressions (creo que, pienso que)
- Can discuss plans and experiences
- Moderate length (10-25 words)
- Example: "¿Qué hiciste ayer?" "Fui al cine con mis amigos."

B2 (Upper-Intermediate):
- Subjunctive mood present
- Complex clause structures (relative clauses, conditionals)
- Abstract vocabulary and idiomatic expressions
- Nuanced opinions and hypotheticals
- Example: "Si hubiera sabido que venías, habría preparado algo especial."

C1-C2 (Advanced/Mastery):
- All subjunctive tenses including pluperfect subjunctive
- Literary and sophisticated constructions
- Discourse markers (no obstante, con todo, por más que)
- Complex nested subordination
- Native-like idiomatic mastery
- Example: "Por mucho que insistas, dudo que consiga convencerle de que reconsidere su postura."

Respond ONLY with valid JSON in this exact format:
{
    "cefr_level": "A1|A2|B1|B2|C1|C2",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this level was chosen"
}"""

    def __init__(self, api_key: Optional[str] = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package required. Run: pip install anthropic")

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key parameter required")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info("Initialized Claude API client")

    def classify(self, text: str, context_before: List[str] = None, context_after: List[str] = None) -> Dict:
        """
        Classify a dialogue using Claude API.

        Args:
            text: The main dialogue text to classify
            context_before: Optional preceding dialogue lines
            context_after: Optional following dialogue lines

        Returns:
            Dict with cefr_level, confidence, and reasoning
        """
        # Build the prompt with context
        prompt_parts = []

        if context_before:
            prompt_parts.append("Context before:\n" + "\n".join(context_before[-2:]))

        prompt_parts.append(f"Dialogue to classify:\n\"{text}\"")

        if context_after:
            prompt_parts.append("Context after:\n" + "\n".join(context_after[:2]))

        user_prompt = "\n\n".join(prompt_parts)
        user_prompt += "\n\nClassify this dialogue according to CEFR level. Respond with JSON only."

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                system=self.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Parse the JSON response
            response_text = response.content[0].text.strip()

            # Handle markdown code blocks
            if response_text.startswith("```"):
                response_text = re.sub(r'^```json?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            result = json.loads(response_text)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {
                "cefr_level": "B1",
                "confidence": 0.3,
                "reasoning": "Failed to parse LLM response, defaulting to B1"
            }
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {
                "cefr_level": "B1",
                "confidence": 0.3,
                "reasoning": f"API error: {str(e)}"
            }


class CEFRPipeline:
    """
    Combined pipeline using rule-based pre-filtering and LLM classification.
    """

    def __init__(self, api_key: Optional[str] = None, use_llm: bool = True):
        self.rule_analyzer = RuleBasedAnalyzer()
        self.llm_classifier = None
        self.use_llm = use_llm

        if use_llm and ANTHROPIC_AVAILABLE:
            try:
                self.llm_classifier = LLMClassifier(api_key)
            except (ValueError, ImportError) as e:
                logger.warning(f"LLM classifier not available: {e}")
                self.use_llm = False

    def classify(
        self,
        text: str,
        context_before: List[str] = None,
        context_after: List[str] = None,
        force_llm: bool = False
    ) -> CEFRClassification:
        """
        Classify a dialogue using the hybrid pipeline.

        Args:
            text: The dialogue text to classify
            context_before: Optional preceding lines
            context_after: Optional following lines
            force_llm: Always use LLM regardless of rule-based confidence

        Returns:
            CEFRClassification with level, confidence, and reasoning
        """
        # Step 1: Rule-based analysis
        features = self.rule_analyzer.analyze(text)
        rule_level, rule_confidence = self.rule_analyzer.estimate_cefr(features)

        # Step 2: Decide if LLM is needed
        use_llm_for_this = force_llm or (
            self.use_llm and
            self.llm_classifier is not None and
            rule_confidence < 0.8
        )

        if use_llm_for_this:
            # Use LLM classification
            llm_result = self.llm_classifier.classify(text, context_before, context_after)
            final_level = llm_result.get("cefr_level", rule_level)
            final_confidence = llm_result.get("confidence", 0.5)
            reasoning = llm_result.get("reasoning", "LLM classification")
            method = "llm"
        else:
            # Use rule-based only
            final_level = rule_level
            final_confidence = rule_confidence
            reasoning = f"Rule-based: {len(features['verb_tenses'])} tenses detected, complexity score {features['complexity_score']}"
            method = "rule_based"

        return CEFRClassification(
            cefr_level=final_level,
            simplified_level=LEVEL_MAPPING.get(final_level, "intermediate"),
            confidence=final_confidence,
            reasoning=reasoning,
            linguistic_features=features,
            method=method
        )

    def classify_batch(
        self,
        dialogues: List[Dict],
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Classify a batch of dialogues.

        Args:
            dialogues: List of dialogue dicts with 'ground_truth', 'context_before', 'context_after'
            show_progress: Whether to show progress bar

        Returns:
            List of dialogue dicts with added classification fields
        """
        results = []

        if show_progress:
            try:
                from tqdm import tqdm
                dialogues_iter = tqdm(dialogues, desc="Classifying dialogues")
            except ImportError:
                dialogues_iter = dialogues
        else:
            dialogues_iter = dialogues

        for dialogue in dialogues_iter:
            text = dialogue.get("ground_truth", "")
            context_before = dialogue.get("context_before", [])
            context_after = dialogue.get("context_after", [])

            classification = self.classify(text, context_before, context_after)

            # Add classification to dialogue
            result = dialogue.copy()
            result["cefr_level"] = classification.cefr_level
            result["cefr_simplified"] = classification.simplified_level
            result["cefr_confidence"] = classification.confidence
            result["cefr_reasoning"] = classification.reasoning
            result["cefr_method"] = classification.method
            result["linguistic_features"] = classification.linguistic_features

            results.append(result)

        return results


def load_dialogues(filepath: str) -> Dict[str, List[Dict]]:
    """Load dialogues from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_dialogues(dialogues: Dict[str, List[Dict]], filepath: str):
    """Save dialogues to JSON file."""
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(dialogues, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {sum(len(v) for v in dialogues.values())} dialogues to {filepath}")


def reclassify_dialogues(
    input_file: str,
    output_file: str,
    api_key: Optional[str] = None,
    use_llm: bool = True
) -> Dict[str, int]:
    """
    Reclassify all dialogues from the input file using CEFR criteria.

    Args:
        input_file: Path to dialogues_by_complexity.json
        output_file: Path for output file
        api_key: Optional Anthropic API key
        use_llm: Whether to use LLM classification

    Returns:
        Dictionary with level counts
    """
    # Load dialogues
    data = load_dialogues(input_file)

    # Flatten all dialogues
    all_dialogues = []
    for level, dialogues in data.items():
        for d in dialogues:
            d["original_level"] = level
            all_dialogues.append(d)

    logger.info(f"Loaded {len(all_dialogues)} dialogues for reclassification")

    # Initialize pipeline
    pipeline = CEFRPipeline(api_key=api_key, use_llm=use_llm)

    # Classify all dialogues
    classified = pipeline.classify_batch(all_dialogues, show_progress=True)

    # Group by new simplified level
    by_level = defaultdict(list)
    level_counts = defaultdict(int)

    for dialogue in classified:
        new_level = dialogue["cefr_simplified"]
        by_level[new_level].append(dialogue)
        level_counts[new_level] += 1

    # Save results
    save_dialogues(dict(by_level), output_file)

    # Print summary
    print("\n" + "=" * 60)
    print("CEFR RECLASSIFICATION SUMMARY")
    print("=" * 60)

    for level in ["beginner", "intermediate", "advanced", "mastery"]:
        count = level_counts.get(level, 0)
        print(f"  {level:15} {count:4} dialogues")

    print("=" * 60)
    print(f"  {'TOTAL':15} {sum(level_counts.values()):4} dialogues")
    print("=" * 60)

    # Show level changes
    print("\nLevel changes from original classification:")
    changes = defaultdict(int)
    for dialogue in classified:
        orig = dialogue.get("original_level", "unknown")
        new = dialogue["cefr_simplified"]
        if orig != new:
            changes[f"{orig} -> {new}"] += 1

    for change, count in sorted(changes.items(), key=lambda x: -x[1]):
        print(f"  {change}: {count}")

    return dict(level_counts)


def generate_audio_prompts(
    classified_file: str,
    output_dir: str,
    prompts_per_level: int = 20
):
    """
    Generate audio recording prompt markdown files from classified dialogues.

    Args:
        classified_file: Path to classified dialogues JSON
        output_dir: Directory for output markdown files
        prompts_per_level: Number of prompts per scenario per level
    """
    data = load_dialogues(classified_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    level_configs = {
        "beginner": {
            "filename": "audio_recording_prompts_beginner_v2.md",
            "title": "BEGINNER Level (A1-A2)",
            "target": "All newbie speakers (4 people)",
            "cefr_levels": ["A1", "A2"],
        },
        "intermediate": {
            "filename": "audio_recording_prompts_intermediate_v2.md",
            "title": "INTERMEDIATE Level (B1)",
            "target": "Comfortable newbies + Good speakers",
            "cefr_levels": ["B1"],
        },
        "advanced": {
            "filename": "audio_recording_prompts_advanced_v2.md",
            "title": "ADVANCED Level (B2)",
            "target": "Good speakers (2 people)",
            "cefr_levels": ["B2"],
        },
        "mastery": {
            "filename": "audio_recording_prompts_mastery_v2.md",
            "title": "MASTERY Level (C1-C2)",
            "target": "Fluent/Native speakers",
            "cefr_levels": ["C1", "C2"],
        },
    }

    for level, config in level_configs.items():
        dialogues = data.get(level, [])

        if not dialogues:
            logger.info(f"No dialogues for {level} level, skipping")
            continue

        # Group by scenario
        by_scenario = defaultdict(list)
        for d in dialogues:
            scenario = d.get("scenario", "unknown")
            by_scenario[scenario].append(d)

        # Generate markdown
        md_content = generate_prompt_markdown(
            level=level,
            title=config["title"],
            target=config["target"],
            dialogues_by_scenario=dict(by_scenario),
            prompts_per_scenario=prompts_per_level
        )

        # Write file
        filepath = output_path / config["filename"]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"Generated {filepath} with {len(dialogues)} dialogues")


def generate_prompt_markdown(
    level: str,
    title: str,
    target: str,
    dialogues_by_scenario: Dict[str, List[Dict]],
    prompts_per_scenario: int = 20
) -> str:
    """Generate markdown content for audio recording prompts."""

    lines = [
        f"# Audio Recording Prompts - {title}",
        "## From Movie Dialogues (Ground Truth Reference)",
        "",
        "**Project:** SpeakEasy - Catalan Spanish Language Learning App  ",
        "**Purpose:** Gold standard recordings with CEFR-aligned complexity  ",
        f"**Target Speakers:** {target}  ",
        "**Estimated Time:** ~25 minutes",
        "",
        "---",
        "",
        "## Recording Instructions",
        "",
        "1. **Read the context first** - Understand the situation",
        "2. **Record both speakers** - Natural conversation flow",
        "3. **Speak at the target level** - Match the complexity shown",
        "",
        "---",
        "",
        f"## File Naming: `{{name}}_{{scenario}}_{{number}}_{level}.wav`",
        "",
        "---",
        "",
    ]

    scenario_titles = {
        "greetings": "GREETINGS (Hellos and introductions)",
        "farewells": "FAREWELLS (Saying goodbye)",
        "family": "FAMILY (Family conversations)",
        "emotions": "EMOTIONS (Expressing feelings)",
        "opinions": "OPINIONS (Sharing opinions)",
        "plans": "PLANS (Making plans)",
        "requests": "REQUESTS (Asking for help)",
        "apologies": "APOLOGIES (Apologizing)",
        "small_talk": "SMALL_TALK (Casual conversation)",
    }

    for scenario, title_text in scenario_titles.items():
        if scenario not in dialogues_by_scenario:
            continue

        dialogues = dialogues_by_scenario[scenario][:prompts_per_scenario]

        if not dialogues:
            continue

        lines.append(f"## {title_text}")
        lines.append("")

        for i, d in enumerate(dialogues, 1):
            lines.append(f"### {scenario.title()} {i:02d}")
            lines.append(f"**Source:** {d.get('source_film', 'Unknown')} ({d.get('timestamp', '')})")
            lines.append(f"**ID:** `{d.get('id', '')}`")
            lines.append(f"**CEFR:** {d.get('cefr_level', 'N/A')} (confidence: {d.get('cefr_confidence', 0):.0%})")
            lines.append("")

            # Context before
            if d.get("context_before"):
                lines.append("| Speaker | Line |")
                lines.append("|---------|------|")
                for j, line in enumerate(d["context_before"][-2:]):
                    speaker = "A" if j % 2 == 0 else "B"
                    lines.append(f"| {speaker} | \"{line}\" |")

            # Ground truth
            lines.append(f"| **Response** | \"{d.get('ground_truth', '')}\" |")
            lines.append("")

            # CEFR reasoning
            if d.get("cefr_reasoning"):
                lines.append(f"**CEFR Reasoning:** {d['cefr_reasoning']}")
                lines.append("")

            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="CEFR-aligned dialogue classifier")
    parser.add_argument(
        "--input", "-i",
        default="data/eval/dialogues_by_complexity.json",
        help="Input JSON file with dialogues"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/eval/dialogues_by_complexity_cefr.json",
        help="Output JSON file for classified dialogues"
    )
    parser.add_argument(
        "--prompts-dir", "-p",
        default="data",
        help="Directory for generated prompt markdown files"
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM classification (rule-based only)"
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("CEFR DIALOGUE RECLASSIFICATION")
    print("=" * 60)

    # Reclassify dialogues
    level_counts = reclassify_dialogues(
        input_file=args.input,
        output_file=args.output,
        api_key=args.api_key,
        use_llm=not args.no_llm
    )

    # Generate audio prompts
    print("\nGenerating audio recording prompts...")
    generate_audio_prompts(
        classified_file=args.output,
        output_dir=args.prompts_dir
    )

    print("\nDone!")


if __name__ == "__main__":
    main()
