from transformers import pipeline
import numpy as np
import torch

class ZeroShotClassifier:
    def __init__(self, model_name="facebook/bart-large-mnli"):
        device = 0 if torch.cuda.is_available() else -1
        self.classifier = pipeline(
            "zero-shot-classification",
            model=model_name,
            device=device
        )

    def predict(self, text, labels):
        result = self.classifier(text, labels)
        best_label = result['labels'][0]
        return best_label
