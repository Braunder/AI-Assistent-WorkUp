import base64
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import mss
import mss.tools

from assistant.config import settings


@dataclass(frozen=True)
class ScreenCaptureResult:
    mime_type: str
    image_base64: str
    saved_path: str
    width: int
    height: int


def capture_screen() -> ScreenCaptureResult:
    """Capture the primary monitor as PNG and return base64 payload for multimodal input."""
    out_dir: Path = settings.workspace_root / "captures"
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"screen_{stamp}.png"

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        png_bytes = mss.tools.to_png(shot.rgb, shot.size)

    out_path.write_bytes(png_bytes)

    return ScreenCaptureResult(
        mime_type="image/png",
        image_base64=base64.b64encode(png_bytes).decode("ascii"),
        saved_path=str(out_path),
        width=shot.width,
        height=shot.height,
    )
