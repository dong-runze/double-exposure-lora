import argparse
import re
from pathlib import Path

from PIL import Image


IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".webp", ".bmp"]


def find_left_images(input_dir: Path) -> list[tuple[int, Path]]:
    pairs: list[tuple[int, Path]] = []
    for path in input_dir.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_EXTS:
            continue
        match = re.fullmatch(r"(\d+)", path.stem)
        if not match:
            continue
        pairs.append((int(match.group(1)), path))
    pairs.sort(key=lambda item: item[0])
    return pairs


def find_right_image(input_dir: Path, index: int) -> Path | None:
    base_name = f"new_flow{index}"
    for ext in IMAGE_EXTS:
        candidate = input_dir / f"{base_name}{ext}"
        if candidate.exists():
            return candidate
    return None


def merge_pair(left_path: Path, right_path: Path, output_path: Path, gap: int) -> tuple[int, int]:
    with Image.open(left_path) as left_img, Image.open(right_path) as right_img:
        left = left_img.convert("RGB")
        right = right_img.convert("RGB")

        width = left.width + gap + right.width
        height = max(left.height, right.height)
        canvas = Image.new("RGB", (width, height), (255, 255, 255))

        left_y = (height - left.height) // 2
        right_y = (height - right.height) // 2
        canvas.paste(left, (0, left_y))
        canvas.paste(right, (left.width + gap, right_y))
        canvas.save(output_path, format="PNG")
        return width, height


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge image pairs side by side.")
    parser.add_argument("--input-dir", default=".", help="Directory that contains source images.")
    parser.add_argument("--output-dir", default="merged", help="Directory for merged images.")
    parser.add_argument("--gap", type=int, default=16, help="Gap in pixels between left and right images.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    left_images = find_left_images(input_dir)
    if not left_images:
        raise FileNotFoundError(f"No left images like '1.png' found in: {input_dir}")

    generated = 0
    skipped: list[int] = []
    for index, left_path in left_images:
        right_path = find_right_image(input_dir, index)
        if right_path is None:
            skipped.append(index)
            continue

        output_path = output_dir / f"merged_{index}.png"
        width, height = merge_pair(left_path, right_path, output_path, args.gap)
        generated += 1
        print(
            f"[OK] {left_path.name} + {right_path.name} -> "
            f"{output_path.name} ({width}x{height})"
        )

    print(f"\nDone. Generated {generated} image(s) in: {output_dir}")
    if skipped:
        skipped_text = ", ".join(str(x) for x in skipped)
        print(f"Skipped (missing right image 'new_flowN.*'): {skipped_text}")


if __name__ == "__main__":
    main()
