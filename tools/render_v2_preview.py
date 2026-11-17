#!/usr/bin/env python3
"""Render exact offline C++ V2 pixels; requires Pillow and the host demo binary."""
import argparse
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ric_rle32 import encode_bgra, decode_bgra, swap_red_blue


def render(demo, output):
    cases = [('650 RPM / boost unavailable', '650', None),
             ('4,250 RPM / boost unavailable', '4250', None),
             ('4,250 RPM / +12.4 PSI - simulated boost', '4250', '12.4'),
             ('6,200 RPM / +18.0 PSI - simulated boost', '6200', '18.0'),
             ('6,500 RPM / +18.0 PSI - simulated boost', '6500', '18.0')]
    scale = 6
    sheet = Image.new('RGB', (960, 90 + len(cases) * 270), '#101217')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=19)
    draw.text((30, 20), 'V2 candidate - exact 150 x 36 pixels, enlarged 6x', fill='white', font=font)
    draw.text((30, 49), 'Offline simulation. No vehicle deployment or larger surface assumed.', fill='#aeb9c7', font=font)
    with tempfile.TemporaryDirectory() as scratch:
        for i, (label, rpm, psi) in enumerate(cases):
            rawfile = Path(scratch) / f'{i}.bgra'
            cmd = [str(demo.resolve()), rpm, str(rawfile), 'v2']
            if psi is not None:
                cmd.append(psi)
            subprocess.run(cmd, check=True, capture_output=True)
            raw = rawfile.read_bytes()
            assert len(raw) == 150 * 36 * 4
            corrected = swap_red_blue(raw)
            assert decode_bgra(encode_bgra(corrected), 150 * 36) == corrected
            frame = Image.frombytes('RGBA', (150, 36), raw, 'raw', 'BGRA').convert('RGB')
            y = 90 + i * 270
            draw.text((30, y), label, fill='#d2dce8', font=font)
            sheet.paste(frame.resize((150 * scale, 36 * scale), Image.Resampling.NEAREST), (30, y + 30))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    print(f'Saved {output}; five frames and corrected RLE32 round-trips verified.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('demo', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    render(args.demo, args.output)
