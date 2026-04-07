"""Detect game state by matching against reference screenshots.

Instead of button detection, we match the current screenshot against
the 5 reference game states in screens/ folder to determine which
round/phase we're in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import cv2
import numpy as np
from PIL import Image

from detector import LiveUIState


class GameStateDetector:
    """Match current screenshot against reference game states.
    
    The 5 states are:
    1. WAIT_READY - "Ready" state, blue Ready button visible
    2. WAIT_COLOR_DECISION - Red/Black buttons visible
    3. WAIT_HIGHER_LOWER_DECISION - Higher/Lower buttons visible
    4. WAIT_INSIDE_OUTSIDE_DECISION - Inside/Outside buttons visible
    5. WAIT_SUIT_DECISION - Suit buttons visible
    """

    def __init__(self, screens_dir: str | Path = "screens") -> None:
        self.screens_dir = Path(screens_dir)
        self.reference_states: dict[LiveUIState, np.ndarray] = {}
        self._load_reference_states()

    def _load_reference_states(self) -> None:
        """Load the 5 reference game state images and convert to grayscale numpy arrays."""
        state_files = {
            "1rdy.jpg": LiveUIState.WAIT_READY,
            "2red_black.jpg": LiveUIState.WAIT_COLOR_DECISION,
            "3higher_lower.jpg": LiveUIState.WAIT_HIGHER_LOWER_DECISION,
            "4inside_outside.jpg": LiveUIState.WAIT_INSIDE_OUTSIDE_DECISION,
            "5color.jpg": LiveUIState.WAIT_SUIT_DECISION,
        }

        for filename, state in state_files.items():
            path = self.screens_dir / filename
            if not path.exists():
                raise FileNotFoundError(f"Reference state image not found: {path}")

            # Load as grayscale for comparison
            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError(f"Failed to load image: {path}")

            self.reference_states[state] = image

    def detect_state(self, screenshot: Image.Image) -> tuple[LiveUIState, float]:
        """Detect the current game state from a screenshot.
        
        Returns:
            tuple of (detected_state, match_confidence)
            
        The confidence is the maximum template match score across all states.
        """
        # Convert PIL Image to OpenCV format (BGR)
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screenshot_gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)

        best_state = LiveUIState.WAIT_READY
        best_score = -1.0

        # Match against each reference state
        for state, reference_img in self.reference_states.items():
            score = self._match_score(screenshot_gray, reference_img)

            if score > best_score:
                best_score = score
                best_state = state

        return best_state, best_score

    def _match_score(self, screenshot: np.ndarray, reference: np.ndarray) -> float:
        """Calculate how well the screenshot matches a reference image.
        
        Uses SIFT feature matching for robustness to camera angle/lighting changes.
        Returns a score from 0 to 1 where 1 is perfect match.
        """
        # Initialize SIFT detector
        sift = cv2.SIFT_create()

        # Find keypoints and descriptors
        kp1, des1 = sift.detectAndCompute(reference, None)
        kp2, des2 = sift.detectAndCompute(screenshot, None)

        if des1 is None or des2 is None:
            return 0.0

        # Use BFMatcher to find matches
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)

        if not matches:
            return 0.0

        # Apply Lowe's ratio test to filter good matches
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)

        # Score is number of good matches normalized by reference keypoints
        # (more is better, but scale by reference size)
        if len(kp1) == 0:
            return 0.0

        match_ratio = len(good_matches) / len(kp1)
        # Clamp to [0, 1]
        return min(1.0, match_ratio * 2)  # *2 to be more generous with threshold


class SimpleGameStateDetector:
    """Fallback detector using histogram comparison (faster, less robust).
    
    Use this if SIFT is too slow. Less accurate but much faster.
    """

    def __init__(self, screens_dir: str | Path = "screens") -> None:
        self.screens_dir = Path(screens_dir)
        self.reference_states: dict[LiveUIState, np.ndarray] = {}
        self._load_reference_states()

    def _load_reference_states(self) -> None:
        """Load the 5 reference game state images."""
        state_files = {
            "1rdy.jpg": LiveUIState.WAIT_READY,
            "2red_black.jpg": LiveUIState.WAIT_COLOR_DECISION,
            "3higher_lower.jpg": LiveUIState.WAIT_HIGHER_LOWER_DECISION,
            "4inside_outside.jpg": LiveUIState.WAIT_INSIDE_OUTSIDE_DECISION,
            "5color.jpg": LiveUIState.WAIT_SUIT_DECISION,
        }

        for filename, state in state_files.items():
            path = self.screens_dir / filename
            if not path.exists():
                raise FileNotFoundError(f"Reference state image not found: {path}")

            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError(f"Failed to load image: {path}")

            self.reference_states[state] = image

    def detect_state(self, screenshot: Image.Image) -> tuple[LiveUIState, float]:
        """Detect game state using histogram comparison."""
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screenshot_gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)

        best_state = LiveUIState.WAIT_READY
        best_score = -1.0

        for state, reference_img in self.reference_states.items():
            # Compute histograms
            hist_ref = cv2.calcHist([reference_img], [0], None, [256], [0, 256])
            hist_screenshot = cv2.calcHist([screenshot_gray], [0], None, [256], [0, 256])

            # Normalize
            hist_ref = cv2.normalize(hist_ref, hist_ref).flatten()
            hist_screenshot = cv2.normalize(hist_screenshot, hist_screenshot).flatten()

            # Compare using correlation
            score = cv2.compareHist(hist_ref, hist_screenshot, cv2.HISTCMP_CORREL)

            if score > best_score:
                best_score = score
                best_state = state

        return best_state, best_score
