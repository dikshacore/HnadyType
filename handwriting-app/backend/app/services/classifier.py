"""
Confidence-check classifier: NOT the primary labeling mechanism (alignment
in segmentation.py already gives each crop its ground-truth label). This
model's only job is to sanity-check that crop and flag it for the review UI
when it disagrees with the expected label -- covering the "if not
recognised, use any other random letter" requirement without ever blocking
the enrollment flow.

Swap `predict()`'s body for a real trained model (a small CNN trained on
EMNIST + your own accumulating cross-user review-corrected data, per the
technical approach's "model trained through different users" point) --
the interface below is what the rest of the app depends on, so the
implementation can evolve independently.
"""
import numpy as np


CHARSET = list("abcdefghijklmnopqrstuvwxyz") + \
          list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + \
          list("0123456789") + \
          list(".,!?;:'\"-_()[]{}/@#$%&*+=")


class ConfidenceClassifier:
    def __init__(self, model_path: str | None = None):
        self.model = None
        if model_path:
            self.model = self._load_model(model_path)

    def _load_model(self, path: str):
        # e.g. torch.jit.load(path) or tf.keras.models.load_model(path)
        raise NotImplementedError("Wire up your trained model checkpoint here.")

    def predict(self, glyph_crop: np.ndarray) -> tuple[str, float]:
        """
        Returns (predicted_char, confidence). Until a real model is
        wired in, returns a neutral placeholder so the pipeline is
        runnable end-to-end during development.
        """
        if self.model is None:
            return "?", 0.0
        # predicted_index, confidence = self.model.predict(preprocess(glyph_crop))
        # return CHARSET[predicted_index], confidence
        raise NotImplementedError

    def check_against_expected(self, glyph_crop: np.ndarray, expected_char: str, threshold: float) -> dict:
        """Used by the enrollment pipeline right after alignment."""
        predicted_char, confidence = self.predict(glyph_crop)
        if self.model is None:
            # No model wired up yet -- trust the alignment's label but mark
            # everything as unreviewed rather than silently high-confidence.
            return {"needs_review": False, "confidence": None, "predicted_char": None}

        agrees = predicted_char == expected_char
        return {
            "needs_review": (not agrees) or confidence < threshold,
            "confidence": confidence,
            "predicted_char": predicted_char,
        }
