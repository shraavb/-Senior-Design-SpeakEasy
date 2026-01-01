"""
Feedback generator for fluency evaluation.

Generates human-readable, actionable feedback based on metric scores.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..api.models import FeedbackResult


def generate_feedback(
    metrics: Any,  # MetricsBreakdown
    fluency_score: float,
    scenario: Optional[str] = None,
) -> FeedbackResult:
    """
    Generate comprehensive feedback from fluency metrics.

    Args:
        metrics: MetricsBreakdown with all analyzer results
        fluency_score: Overall composite score
        scenario: Optional scenario for context-specific feedback

    Returns:
        FeedbackResult with summary, strengths, improvements, suggestions
    """
    summary = _generate_summary(fluency_score)
    strengths = _identify_strengths(metrics)
    improvements = _identify_improvements(metrics)
    suggestions = _generate_practice_suggestions(metrics, scenario)

    return FeedbackResult(
        summary=summary,
        strengths=strengths[:3],  # Top 3 strengths
        improvements=improvements[:3],  # Top 3 improvements
        practice_suggestions=suggestions[:3],  # Top 3 suggestions
    )


def _generate_summary(score: float) -> str:
    """Generate overall summary based on score."""
    if score >= 90:
        return "Excellent fluency! Your speech sounds natural and native-like."
    elif score >= 75:
        return "Good conversational fluency with natural expression."
    elif score >= 60:
        return "Developing fluency - keep practicing for more natural flow."
    else:
        return "Focus on the fundamentals to build stronger fluency."


def _identify_strengths(metrics: Any) -> List[str]:
    """Identify top performing areas."""
    strengths = []

    # Check pronunciation
    if hasattr(metrics, 'pronunciation_accuracy'):
        pron = metrics.pronunciation_accuracy
        if pron.score >= 80:
            strengths.append(("Clear pronunciation and articulation", pron.score))
        if pron.catalan_marker_score >= 80:
            strengths.append(("Excellent use of Catalan expressions", pron.catalan_marker_score))

    # Check temporal
    if hasattr(metrics, 'temporal_metrics'):
        temp = metrics.temporal_metrics
        if temp.score >= 80:
            strengths.append(("Natural speaking pace and rhythm", temp.score))
        if temp.speaking_rate_wpm >= 120 and temp.speaking_rate_wpm <= 180:
            strengths.append(("Appropriate speaking speed", temp.score))

    # Check lexical
    if hasattr(metrics, 'lexical_accuracy'):
        lex = metrics.lexical_accuracy
        if lex.score >= 80:
            strengths.append(("Accurate vocabulary usage", lex.score))
        if lex.catalan_expressions_used:
            strengths.append(("Good integration of regional vocabulary", lex.score))

    # Check disfluency (lower is better)
    if hasattr(metrics, 'disfluency_detection'):
        dis = metrics.disfluency_detection
        if dis.score <= 20:  # Few disfluencies
            strengths.append(("Smooth speech with minimal hesitation", 100 - dis.score))

    # Check prosodic
    if hasattr(metrics, 'prosodic_quality'):
        pros = metrics.prosodic_quality
        if pros.score >= 80:
            strengths.append(("Expressive intonation and rhythm", pros.score))

    # Check communicative
    if hasattr(metrics, 'communicative_competence'):
        comm = metrics.communicative_competence
        if comm.score >= 80:
            strengths.append(("Appropriate register and discourse", comm.score))
        if comm.discourse_markers_used:
            strengths.append(("Natural use of discourse markers", comm.score))

    # Sort by score and return descriptions
    strengths.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in strengths]


def _identify_improvements(metrics: Any) -> List[str]:
    """Identify areas needing improvement."""
    improvements = []

    # Check pronunciation
    if hasattr(metrics, 'pronunciation_accuracy'):
        pron = metrics.pronunciation_accuracy
        if pron.score < 70:
            improvements.append(("Work on clearer pronunciation", pron.score))
        if pron.phoneme_errors:
            error_types = set(e.get('type', '') for e in pron.phoneme_errors if e.get('type'))
            if 'rolled_r' in error_types:
                improvements.append(("Practice the rolled 'rr' sound", pron.score))
            if 'jota' in error_types:
                improvements.append(("Work on the Spanish 'j' sound", pron.score))
        if pron.intonation_score < 70:
            improvements.append(("Pay attention to question and statement intonation", pron.intonation_score))

    # Check temporal
    if hasattr(metrics, 'temporal_metrics'):
        temp = metrics.temporal_metrics
        if temp.speaking_rate_wpm < 100:
            improvements.append(("Try to speak at a more natural pace", temp.score))
        elif temp.speaking_rate_wpm > 200:
            improvements.append(("Slow down slightly for clarity", temp.score))
        if temp.pause_analysis and temp.pause_analysis.get('very_long_pauses', 0) > 2:
            improvements.append(("Reduce long pauses to maintain flow", temp.score))

    # Check lexical
    if hasattr(metrics, 'lexical_accuracy'):
        lex = metrics.lexical_accuracy
        if lex.wer > 0.3:
            improvements.append(("Focus on vocabulary accuracy", lex.score))

    # Check disfluency
    if hasattr(metrics, 'disfluency_detection'):
        dis = metrics.disfluency_detection
        if dis.filled_pause_count > 3:
            improvements.append(("Reduce filler words like 'um' and 'eh'", 100 - dis.score))
        if dis.repetitions > 2:
            improvements.append(("Work on avoiding word repetitions", 100 - dis.score))

    # Check prosodic
    if hasattr(metrics, 'prosodic_quality'):
        pros = metrics.prosodic_quality
        if pros.score < 70:
            if pros.pitch_std_hz < 20:
                improvements.append(("Add more expression to avoid monotone speech", pros.score))

    # Check communicative
    if hasattr(metrics, 'communicative_competence'):
        comm = metrics.communicative_competence
        if comm.register_appropriateness < 0.7:
            improvements.append(("Match your language register to the context", comm.score))

    # Sort by score (lower scores = higher priority) and return descriptions
    improvements.sort(key=lambda x: x[1])
    return [i[0] for i in improvements]


def _generate_practice_suggestions(
    metrics: Any,
    scenario: Optional[str] = None,
) -> List[str]:
    """Generate specific practice suggestions."""
    suggestions = []

    # Pronunciation practice
    if hasattr(metrics, 'pronunciation_accuracy'):
        pron = metrics.pronunciation_accuracy
        if pron.score < 80:
            suggestions.append("Record yourself and compare to native speakers")
        if pron.phoneme_errors:
            suggestions.append("Practice minimal pairs for sounds you find difficult")

    # Temporal practice
    if hasattr(metrics, 'temporal_metrics'):
        temp = metrics.temporal_metrics
        if temp.score < 80:
            suggestions.append("Practice with a metronome to develop consistent rhythm")

    # Disfluency reduction
    if hasattr(metrics, 'disfluency_detection'):
        dis = metrics.disfluency_detection
        if dis.score > 30:
            suggestions.append("Practice pausing silently instead of using filler words")
            suggestions.append("Prepare key phrases before speaking")

    # Prosodic practice
    if hasattr(metrics, 'prosodic_quality'):
        pros = metrics.prosodic_quality
        if pros.rhythm_score < 70:
            suggestions.append("Listen to Spanish podcasts and shadow the speakers")

    # Scenario-specific
    if scenario:
        scenario_suggestions = {
            "greetings": "Practice common greeting exchanges with a partner",
            "farewells": "Learn different farewell phrases for various situations",
            "family": "Practice describing your family in detail",
            "emotions": "Practice expressing different emotions with appropriate intonation",
            "plans": "Practice using future tenses in conversation",
            "requests": "Learn polite request formulas",
        }
        if scenario in scenario_suggestions:
            suggestions.append(scenario_suggestions[scenario])

    # General suggestions
    if len(suggestions) < 3:
        suggestions.extend([
            "Practice speaking aloud daily for at least 10 minutes",
            "Watch Spanish films and repeat dialogue",
            "Find a conversation partner for regular practice",
        ])

    return list(dict.fromkeys(suggestions))  # Remove duplicates while preserving order


def format_feedback_for_display(feedback: FeedbackResult) -> str:
    """Format feedback for text display."""
    lines = []

    lines.append(f"Summary: {feedback.summary}")
    lines.append("")

    if feedback.strengths:
        lines.append("Strengths:")
        for s in feedback.strengths:
            lines.append(f"  + {s}")
        lines.append("")

    if feedback.improvements:
        lines.append("Areas for improvement:")
        for i in feedback.improvements:
            lines.append(f"  - {i}")
        lines.append("")

    if feedback.practice_suggestions:
        lines.append("Practice suggestions:")
        for idx, s in enumerate(feedback.practice_suggestions, 1):
            lines.append(f"  {idx}. {s}")

    return "\n".join(lines)
