from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True, slots=True)
class Region:
    """Simple rectangular screen region."""
    x: int
    y: int
    width: int
    height: int

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height


class VisionError(RuntimeError):
    pass


class ScreenCapture:
    """Screenshot backend abstraction.

    This is intentionally minimal so you can later switch between:
    - pyautogui
    - mss
    - PIL.ImageGrab
    - window-specific capture

    For now it only defines the interface.
    """

    def capture_fullscreen(self):
        raise NotImplementedError("Implement fullscreen capture with your preferred backend.")

    def capture_region(self, region: Region):
        raise NotImplementedError("Implement regional capture with your preferred backend.")


class ImageIO:
    """Helpers for saving debug outputs.

    The exact image type depends on the backend you use later (PIL image, numpy array, etc.).
    """

    @staticmethod
    def save_image(image, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if hasattr(image, "save"):
            image.save(path)
            return

        raise VisionError(
            "Unsupported image object for save_image(). "
            "Use a backend that returns save()-compatible images or extend this helper."
        )


def crop_image(image, region: Region):
    """Crop helper for PIL-like images."""
    if hasattr(image, "crop"):
        return image.crop((region.left, region.top, region.right, region.bottom))

    raise VisionError(
        "Unsupported image object for crop_image(). "
        "Use a backend that returns crop()-compatible images or extend this helper."
    )


def ensure_region_within_bounds(region: Region, image_width: int, image_height: int) -> None:
    if region.x < 0 or region.y < 0:
        raise VisionError("Region starts outside image bounds.")
    if region.right > image_width or region.bottom > image_height:
        raise VisionError("Region exceeds image bounds.")