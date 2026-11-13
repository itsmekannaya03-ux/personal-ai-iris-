import logging
from typing import Optional

logger = logging.getLogger("iris.vision.image_analyzer")


class ImageAnalyzer:
    """
    Analyzes images and describes their content.
    Uses CLIP or a lightweight model for image understanding.
    """

    def __init__(self):
        self._model = None
        self._processor = None
        self._init_model()

    def _init_model(self):
        try:
            from transformers import CLIPProcessor, CLIPModel
            self._model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self._processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            logger.info("CLIP image model initialized")
        except ImportError:
            logger.warning("transformers not installed — image analysis unavailable")
        except Exception as e:
            logger.warning(f"CLIP init failed: {e}")

    def describe(self, image_path: str, candidates: list[str] = None) -> Optional[dict]:
        if not self._model or not self._processor:
            return None
        try:
            from PIL import Image
            image = Image.open(image_path)
            candidates = candidates or [
                "a person", "a landscape", "a building", "food", "an animal",
                "a document", "a screenshot", "a computer screen", "text",
                "a vehicle", "electronics", "art", "a diagram",
            ]
            inputs = self._processor(text=candidates, images=image, return_tensors="pt", padding=True)
            outputs = self._model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
            best_idx = probs.argmax().item()
            return {
                "label": candidates[best_idx],
                "confidence": round(probs[0][best_idx].item(), 3),
            }
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return None

    def is_available(self) -> bool:
        return self._model is not None

    def get_status(self) -> dict:
        return {"available": self.is_available()}
