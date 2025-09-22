import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ExifTags


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add shooting date watermark (YYYY-MM-DD) from EXIF to images."
    )
    parser.add_argument(
        "path",
        help="Image file or directory path. If file is given, its directory will be used as the source directory.",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=36,
        help="Font size in pixels (default: 36)",
    )
    parser.add_argument(
        "--color",
        default="#FFFFFF",
        help="Text color (hex like #RRGGBB or named color, default: #FFFFFF)",
    )
    parser.add_argument(
        "--position",
        choices=[
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
            "center",
        ],
        default="bottom-right",
        help="Watermark position on the image (default: bottom-right)",
    )
    parser.add_argument(
        "--margin",
        type=int,
        default=20,
        help="Margin from edges in pixels (default: 20)",
    )
    parser.add_argument(
        "--font-path",
        default=None,
        help="Optional path to a .ttf/.otf font file. If not provided, a default font will be used.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively process subdirectories (only when path is a directory).",
    )
    return parser.parse_args()


def resolve_source_and_output(path_str: str) -> Tuple[Path, Path]:
    path = Path(path_str)
    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        sys.exit(1)

    if path.is_file():
        source_dir = path.parent
    else:
        source_dir = path

    output_dir = source_dir / "_watermark"
    output_dir.mkdir(parents=True, exist_ok=True)
    return source_dir, output_dir


def iter_images(root: Path, recursive: bool) -> Iterable[Path]:
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif", ".webp"}
    if recursive:
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in image_exts and "_watermark" not in p.parts:
                yield p
    else:
        for p in root.iterdir():
            if p.is_file() and p.suffix.lower() in image_exts and p.parent.name != "_watermark":
                yield p


def load_font(font_path: Optional[str], font_size: int) -> ImageFont.ImageFont:
    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception as exc:
            print(f"Warning: Failed to load font at '{font_path}': {exc}. Fallback to default font.")
    # Try common system fonts on Windows as a nicety
    for candidate in [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try:
            if Path(candidate).exists():
                return ImageFont.truetype(candidate, font_size)
        except Exception:
            pass
    return ImageFont.load_default()


def extract_shoot_date(image: Image.Image, fallback_path: Path) -> Optional[str]:
    exif = getattr(image, "_getexif", lambda: None)()
    exif_dict = {}
    if exif:
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            exif_dict[tag] = value

    # Prefer DateTimeOriginal, fall back to DateTime
    for key in ("DateTimeOriginal", "DateTime"):
        if key in exif_dict and isinstance(exif_dict[key], str):
            dt_str = exif_dict[key]
            # Typical format: "YYYY:MM:DD HH:MM:SS"
            try:
                dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                return dt.strftime("%Y-%m-%d")
            except Exception:
                # Try other common formats if present
                for fmt in [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y/%m/%d %H:%M:%S",
                    "%Y:%m:%d",
                    "%Y-%m-%d",
                    "%Y/%m/%d",
                ]:
                    try:
                        dt = datetime.strptime(dt_str, fmt)
                        return dt.strftime("%Y-%m-%d")
                    except Exception:
                        continue

    # Fallback: use file's modified time
    try:
        mtime = datetime.fromtimestamp(fallback_path.stat().st_mtime)
        return mtime.strftime("%Y-%m-%d")
    except Exception:
        return None


def compute_position(
    img_size: Tuple[int, int], text_size: Tuple[int, int], position: str, margin: int
) -> Tuple[int, int]:
    img_w, img_h = img_size
    text_w, text_h = text_size

    if position == "top-left":
        return margin, margin
    if position == "top-right":
        return img_w - text_w - margin, margin
    if position == "bottom-left":
        return margin, img_h - text_h - margin
    if position == "bottom-right":
        return img_w - text_w - margin, img_h - text_h - margin
    # center
    return (img_w - text_w) // 2, (img_h - text_h) // 2


def draw_watermark(
    image_path: Path,
    output_dir: Path,
    font: ImageFont.ImageFont,
    color: str,
    position: str,
    margin: int,
) -> Optional[Path]:
    try:
        with Image.open(image_path).convert("RGBA") as im:
            date_text = extract_shoot_date(im, image_path)
            if not date_text:
                print(f"Skip (no date): {image_path}")
                return None

            # Render text size
            dummy_draw = ImageDraw.Draw(im)
            text_bbox = dummy_draw.textbbox((0, 0), date_text, font=font, stroke_width=2)
            text_w = text_bbox[2] - text_bbox[0]
            text_h = text_bbox[3] - text_bbox[1]
            x, y = compute_position(im.size, (text_w, text_h), position, margin)

            # Draw on a new layer for alpha blending
            txt_layer = Image.new("RGBA", im.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)

            # Add a subtle shadow/stroke for visibility
            draw.text(
                (x, y),
                date_text,
                font=font,
                fill=color,
                stroke_width=2,
                stroke_fill="black",
            )

            combined = Image.alpha_composite(im, txt_layer).convert("RGB")

            out_path = output_dir / image_path.name
            combined.save(out_path)
            return out_path
    except Exception as exc:
        print(f"Error processing {image_path}: {exc}")
        return None


def main() -> None:
    args = parse_args()
    source_dir, output_dir = resolve_source_and_output(args.path)

    font = load_font(args.font_path, args.font_size)

    images = list(iter_images(source_dir, args.recursive))
    if not images:
        print("No images found to process.")
        return

    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print(f"Found {len(images)} image(s). Processing...")

    processed = 0
    for img_path in images:
        result = draw_watermark(
            image_path=img_path,
            output_dir=output_dir,
            font=font,
            color=args.color,
            position=args.position,
            margin=args.margin,
        )
        if result:
            processed += 1

    print(f"Done. Watermarked {processed}/{len(images)} image(s).")


if __name__ == "__main__":
    main()





