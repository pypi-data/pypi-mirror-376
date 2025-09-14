# record_svg.py — capture an animated SVG to a looping GIF
# Usage:
#   python record_svg.py --in ~/Downloads/gunfire.svg \
#                        --out ~/Downloads/gunfire.gif \
#                        --dur 4 --fps 15 --w 1600 --h 600 --outw 600

import argparse, asyncio, os, tempfile, subprocess
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="infile", default="~/Downloads/gunfire.svg")
    parser.add_argument("--out", dest="outfile", default="~/Downloads/gunfire.gif")
    parser.add_argument("--dur", type=float, default=4.0)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--w", type=int, default=1600)
    parser.add_argument("--h", type=int, default=600)
    parser.add_argument("--outw", type=int, default=600)
    args = parser.parse_args()

    infile = Path(os.path.expanduser(args.infile))
    outfile = Path(os.path.expanduser(args.outfile))
    if not infile.exists():
        raise FileNotFoundError(f"Input SVG not found: {infile}")

    total_frames = max(1, round(args.dur * args.fps))
    interval_ms = 1000 / args.fps

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-gpu"])
            page = await browser.new_page(viewport={"width": args.w, "height": args.h, "deviceScaleFactor": 1})
            await page.goto(infile.resolve().as_uri())
            await page.wait_for_selector("svg", timeout=5000)

            # Transparent background
            await page.evaluate("""
                () => {
                    const html = document.documentElement;
                    const svg = document.querySelector('svg');
                    if (html) html.style.background = 'rgba(0,0,0,0)';
                    if (svg) {
                        svg.style.background = 'rgba(0,0,0,0)';
                        svg.style.margin = '0';
                        if (!svg.getAttribute('preserveAspectRatio')) {
                            svg.setAttribute('preserveAspectRatio','xMidYMid meet');
                        }
                    }
                }
            """)

            await page.wait_for_timeout(300)  # let animations start

            for i in range(total_frames):
                frame_file = tmpdir / f"frame-{i:04d}.png"
                await page.screenshot(path=str(frame_file), omit_background=True)
                await page.wait_for_timeout(interval_ms)

            await browser.close()

        # ffmpeg palette
        palette = tmpdir / "pal.png"
        subprocess.run([
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-i", str(tmpdir / "frame-%04d.png"),
            "-vf", f"scale={args.outw}:-1:flags=lanczos,palettegen",
            str(palette)
        ], check=True)

        # ffmpeg final gif
        subprocess.run([
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-i", str(tmpdir / "frame-%04d.png"),
            "-i", str(palette),
            "-lavfi", "paletteuse",
            "-loop", "0",
            str(outfile)
        ], check=True)

    print(f"✅ GIF written -> {outfile}")

if __name__ == "__main__":
    asyncio.run(main())

