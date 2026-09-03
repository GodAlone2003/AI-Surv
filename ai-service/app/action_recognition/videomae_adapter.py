from datetime import datetime
from typing import List, Optional, Tuple
import cv2
import numpy as np
import torch
from app.action_recognition.base import ActionObservation, ActionRecognitionAdapter
from app.common.logger import get_logger
from app.schemas import DetectionResult

logger = get_logger(__name__)
MODEL_NAME = "MCG-NJU/videomae-base-finetuned-kinetics"
NUM_FRAMES = 16


class VideoMAEActionRecognizer(ActionRecognitionAdapter):
    mode = "REAL"

    def __init__(self) -> None:
        from transformers import VideoMAEForVideoClassification, VideoMAEImageProcessor
        logger.info("Loading VideoMAE model, first call only")
        self.processor = VideoMAEImageProcessor.from_pretrained(MODEL_NAME)
        self.model = VideoMAEForVideoClassification.from_pretrained(MODEL_NAME)
        self.model.eval()
        logger.info("VideoMAE model loaded")


    def recognize(self, window, frames=None) -> ActionObservation:
        if not frames or len(frames) < NUM_FRAMES:
            return ActionObservation(label="no_activity", confidence=0.5, mode="REAL", metrics={})
        rgb_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames[:NUM_FRAMES]]
        inputs = self.processor(rgb_frames, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
        probs = outputs.logits.softmax(dim=-1)[0]
        top_idx = int(probs.argmax())
        label = self.model.config.id2label[top_idx]
        confidence = float(probs[top_idx])
        return ActionObservation(label=label, confidence=confidence, mode="REAL", metrics={"kinetics_class_index": float(top_idx)})
