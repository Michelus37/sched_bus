from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from PIL import Image, ImageGrab


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


class PILScreenCapture(ScreenCapture):
    """Screenshot capture using PIL.ImageGrab (works on Windows)."""

    def __init__(self, monitor_region: Optional[Region] = None) -> None:
        """Initialize with optional monitor bounding box.
        
        monitor_region: If provided, ImageGrab will only capture this rectangle.
                       Otherwise captures entire primary monitor.
        """
        self.monitor_region = monitor_region

    def capture_fullscreen(self) -> Image.Image:
        """Capture full screen (or monitor_region if specified)."""
        if self.monitor_region:
            bbox = (
                self.monitor_region.left,
                self.monitor_region.top,
                self.monitor_region.right,
                self.monitor_region.bottom,
            )
            return ImageGrab.grab(bbox=bbox)
        else:
            return ImageGrab.grab()

    def capture_region(self, region: Region) -> Image.Image:
        """Capture a specific region of the screen."""
        # If monitor region is set, adjust coordinates relative to monitor
        if self.monitor_region:
            adjusted = Region(
                x=self.monitor_region.x + region.x,
                y=self.monitor_region.y + region.y,
                width=region.width,
                height=region.height,
            )
        else:
            adjusted = region

        bbox = (adjusted.left, adjusted.top, adjusted.right, adjusted.bottom)
        return ImageGrab.grab(bbox=bbox)


def find_game_window(title: str) -> Region:
    """Find an open window by title and return its client-area screen region.

    Uses ctypes on Windows to get the exact game content area, excluding
    the title bar and invisible resize borders that inflate the window rect.
    """
    import ctypes
    import ctypes.wintypes

    hwnd = ctypes.windll.user32.FindWindowW(None, title)
    if not hwnd:
        raise VisionError(f"No window found with title '{title}'. Is the game running?")

    # Client rect is relative to the window — gives the render area size
    client_rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(client_rect))

    # ClientToScreen converts the top-left (0, 0) of the client area to screen coords
    pt = ctypes.wintypes.POINT(0, 0)
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))

    return Region(
        x=pt.x,
        y=pt.y,
        width=client_rect.right,
        height=client_rect.bottom,
    )