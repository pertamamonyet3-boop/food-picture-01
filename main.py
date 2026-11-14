"""Copy the bundled food image to the competition output path."""

import os
from pathlib import Path

MAX_IMAGE_BYTES = 1_048_576
MAX_DIMENSION = 1024


def image_dimensions(data: bytes, kind: str) -> tuple[int, int]:
    """Read dimensions from a PNG IHDR or the first JPEG frame header."""
    if kind == "png":
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
            raise ValueError("food.png does not have a valid PNG header")
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")

    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError("food.jpg does not have a valid JPEG header")
    offset = 2
    frame_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while offset < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7 or marker == 0x01:
            continue
        if offset + 2 > len(data):
            break
        segment_length = int.from_bytes(data[offset:offset + 2], "big")
        if segment_length < 2 or offset + segment_length > len(data):
            break
        if marker in frame_markers:
            if segment_length < 7:
                break
            height = int.from_bytes(data[offset + 3:offset + 5], "big")
            width = int.from_bytes(data[offset + 5:offset + 7], "big")
            return width, height
        offset += segment_length
    raise ValueError("food.jpg has no readable JPEG frame dimensions")


def validate_image(source: Path, data: bytes) -> None:
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"{source.name} exceeds the 1 MiB image limit")
    kind = "jpg" if source.suffix.lower() == ".jpg" else "png"
    width, height = image_dimensions(data, kind)
    if not 1 <= width <= MAX_DIMENSION or not 1 <= height <= MAX_DIMENSION:
        raise ValueError(f"image dimensions must be between 1 and {MAX_DIMENSION} pixels per side")


def output_directory() -> Path:
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")


def main() -> None:
    source_dir = Path(__file__).resolve().parent
    source = next((source_dir / name for name in ("food.jpg", "food.png") if (source_dir / name).is_file()), None)
    if source is None:
        raise FileNotFoundError("Place the generated artwork in food.jpg or food.png beside main.py")

    data = source.read_bytes()
    validate_image(source, data)
    output_dir = output_directory()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "entry.png").write_bytes(data)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit(f"food-picture entry: {error}") from error
