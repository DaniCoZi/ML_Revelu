# app/services/moderation.py
from __future__ import annotations
import threading
from typing import Dict, Any

_analyzers_lock = threading.Lock()
ANALYZERS: Dict[str, Any] = {"sentiment": None, "toxicity": None, "hate": None}

def _load_analyzers():
    """Carga perezosa los analizadores de pysentimiento (ES)."""
    with _analyzers_lock:
        if ANALYZERS["sentiment"] is None:
            from pysentimiento import create_analyzer
            ANALYZERS["sentiment"] = create_analyzer(task="sentiment",   lang="es")
            ANALYZERS["toxicity"]  = create_analyzer(task="toxicity",    lang="es")
            ANALYZERS["hate"]      = create_analyzer(task="hate_speech", lang="es")

def analyze_text(text: str) -> dict:
    """
    Devuelve {
      label: 'positive'|'negative',
      score: float [-1..1],
      sentiment: {...}, toxicity: 'TOXIC'|'NOT_TOXIC', hate: 'HATE'|'NOT_HATE',
      reasons: [str], suggestions: [str]
    }
    """
    t = (text or "").strip()
    if not t:
        return {
            "label":"negative", "score":-1.0,
            "reasons":["Mensaje vacío"],
            "suggestions":["Escribe un mensaje con contexto y una propuesta concreta."]
        }

    try:
        _load_analyzers()
        sa   = ANALYZERS["sentiment"].predict(t)  # .output: POS/NEG/NEU ; .probas: dict
        tox  = ANALYZERS["toxicity"].predict(t)   # .output: TOXIC/NOT_TOXIC
        hate = ANALYZERS["hate"].predict(t)       # .output: HATE/NOT_HATE

        base = sa.probas.get("POS", 0) - sa.probas.get("NEG", 0)  # aprox [-1..1]

        penalty = 0.0
        reasons = []
        if tox.output == "TOXIC":
            penalty -= 0.6
            reasons.append("Se detectó toxicidad.")
        if hate.output == "HATE":
            penalty -= 0.8
            reasons.append("Se detectó discurso de odio.")

        score = max(-1.0, min(1.0, base + penalty))
        positive = (score >= 0.15) and tox.output != "TOXIC" and hate.output != "HATE"

        if sa.output == "NEG":
            reasons.append("Sentimiento negativo predominante.")
        elif sa.output == "NEU" and not reasons:
            reasons.append("Tono neutral.")

        suggestions = []
        if not positive:
            if tox.output == "TOXIC" or hate.output == "HATE":
                suggestions.append("Evita lenguaje ofensivo o ataques personales; describe el problema sin descalificar.")
            if sa.output == "NEG":
                suggestions.append("Cambia adjetivos negativos por descripciones objetivas y propone una solución.")
            suggestions.append("Estructura en positivo: “Observé ___; propongo ___ porque ___”.")
            suggestions.append("Agradece el esfuerzo si aplica y enfoca en el objetivo: “Gracias por ___; ¿podemos ajustar ___ para mejorar ___?”")

        return {
            "label": "positive" if positive else "negative",
            "score": float(score),
            "sentiment": {"label": sa.output, "probas": sa.probas},
            "toxicity": tox.output,
            "hate": hate.output,
            "reasons": reasons,
            "suggestions": suggestions,
        }
    except Exception as e:
        # Fallback seguro si el modelo no carga
        return {
            "label":"negative", "score":-1.0,
            "reasons":[f"Moderador no disponible: {e}"],
            "suggestions":["Temporalmente no se puede moderar. Intenta con un tono constructivo y vuelve a enviar."]
        }
