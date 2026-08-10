from pathlib import Path

from PIL import Image, ImageDraw


W, H = 160, 120
OUT = Path(__file__).with_name("avatar_demo_layered.rgb565")


def rgb565le(r: int, g: int, b: int) -> bytes:
    value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return bytes((value & 0xFF, (value >> 8) & 0xFF))


def frame(kind: str, index: int) -> Image.Image:
    palettes = {
        "face": [(18, 32, 64), (26, 64, 94), (50, 35, 85), (76, 34, 62), (25, 78, 72), (86, 58, 25)],
        "eyes": [(10, 25, 49), (26, 70, 92), (42, 26, 73)],
        "mouth": [(20, 45, 68), (56, 35, 73), (30, 70, 58), (72, 40, 26), (24, 56, 84)],
    }
    image = Image.new("RGB", (W, H), palettes[kind][index])
    draw = ImageDraw.Draw(image)
    # A deliberately simple original face: large enough to be visible on the
    # 320x240 StackChan display, and distinct across all 14 uploaded frames.
    draw.rounded_rectangle((18, 12, 142, 108), radius=20, fill=(235, 186, 124), outline=(255, 235, 185), width=2)
    eye_y = 45 if kind != "eyes" or index == 0 else (49 if index == 1 else 53)
    if kind == "eyes" and index == 2:
        draw.line((39, eye_y, 59, eye_y), fill=(28, 28, 38), width=5)
        draw.line((101, eye_y, 121, eye_y), fill=(28, 28, 38), width=5)
    else:
        draw.ellipse((34, eye_y - 9, 64, eye_y + 12), fill=(28, 28, 38))
        draw.ellipse((96, eye_y - 9, 126, eye_y + 12), fill=(28, 28, 38))
        draw.ellipse((43, eye_y - 5, 52, eye_y + 4), fill=(255, 255, 255))
        draw.ellipse((105, eye_y - 5, 114, eye_y + 4), fill=(255, 255, 255))
    mouth_y = 78
    if kind == "mouth":
        shapes = [
            ((65, mouth_y, 95, mouth_y + 5), (80, 50, 60)),
            ((62, mouth_y, 98, mouth_y + 11), (80, 50, 60)),
            ((59, mouth_y - 3, 101, mouth_y + 16), (80, 35, 62)),
            ((59, mouth_y + 3, 101, mouth_y + 11), (230, 80, 96)),
            ((67, mouth_y - 2, 93, mouth_y + 16), (230, 80, 96)),
        ]
        box, color = shapes[index]
        draw.rounded_rectangle(box, radius=6, fill=color)
    elif kind == "face":
        mouths = [(66, 78, 94, 83), (60, 74, 100, 88), (69, 77, 91, 94), (63, 81, 97, 87), (66, 74, 94, 90), (64, 78, 96, 85)]
        draw.rounded_rectangle(mouths[index], radius=6, fill=(80, 35, 62))
    else:
        draw.rounded_rectangle((66, 78, 94, 84), radius=6, fill=(80, 35, 62))
    draw.text((7, 3), f"{kind}:{index}", fill=(255, 255, 255))
    return image


payload = bytearray()
for kind, count in (("face", 6), ("eyes", 3), ("mouth", 5)):
    for index in range(count):
        image = frame(kind, index)
        for r, g, b in image.getdata():
            payload.extend(rgb565le(r, g, b))

assert len(payload) == 14 * W * H * 2
OUT.write_bytes(payload)
print(f"{OUT} {len(payload)} bytes")
