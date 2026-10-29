"""Turn a rendered Story frame into an MP4 by playing a real clip inside its video panel.

Usage: python compose_video.py <frame.png> <videos-dir> <out.mp4>

render_frames.js writes <frame>.video.json next to the PNG for every panel marked
data-video="<name>"; <videos-dir>/<name>.mp4 is the clip. The clip is scaled to FIT
the panel (never cropped, so no hair is cut off), centred over a blurred, darkened
copy of itself that fills the rest of the panel, with the panel's rounded corners.
<frame>.overlay.png (the frame's text on a transparent background) goes on top, so a
panel can be the whole 1080x1920 frame with text cards over the video.
The MP4 lasts as long as the clip and keeps its sound.
"""
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw


def rounded_mask(w, h, r, path):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=int(r), fill=255)
    m.save(path)


def main():
    frame, videos_dir, out = sys.argv[1:4]
    slots = json.load(open(frame.replace(".png", ".video.json")))
    if len(slots) != 1:
        sys.exit("expected exactly one video panel per frame")
    s = slots[0]
    clip = os.path.join(videos_dir, s["video"] + ".mp4")
    w, h = s["w"] - s["w"] % 2, s["h"] - s["h"] % 2
    if s["radius"] == 0:
        s["radius"] = 0.01
    with tempfile.TemporaryDirectory() as tmp:
        mask = os.path.join(tmp, "mask.png")
        rounded_mask(w, h, s["radius"], mask)
        graph = (
            f"[1:v]split[a][b];"
            f"[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=30:2,eq=brightness=-0.12[bg];"
            f"[b]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=rgba[panel];"
            f"[2:v]format=gray[m];[panel][m]alphamerge[rounded];"
            f"[0:v][rounded]overlay={s['x']}:{s['y']}:shortest=1[base];"
            f"[base][3:v]overlay=0:0:shortest=1,format=yuv420p[v]"
        )
        cmd = [
            "ffmpeg", "-v", "error", "-y",
            "-loop", "1", "-i", frame,
            "-i", clip,
            "-loop", "1", "-i", mask,
            "-loop", "1", "-i", frame.replace(".png", ".overlay.png"),
            "-filter_complex", graph, "-map", "[v]", "-map", "1:a?",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-r", "30",
            "-c:a", "aac", "-shortest", "-movflags", "+faststart", out,
        ]
        subprocess.run(cmd, check=True)
    print(out)


if __name__ == "__main__":
    main()
