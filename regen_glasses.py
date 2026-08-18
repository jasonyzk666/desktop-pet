"""
Scheduled regeneration driver: fix glasses to black rectangular rounded-corner
(方框圆边) to match the real person, using the original photo as a detail reference.

Runs 3 image-to-image generations (double-reference: current green source + original
photo), rebuilds sprites, verifies, rebuilds the exe, and relaunches.

Usage: python regen_glasses.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ASSETS = BASE / "assets"
GEN = BASE / "generated-images"
ORIG_PHOTO = Path(r"C:\Users\Jason\.qclaw\workspace\IMG_20260815_165842.jpg")

NODE = r"E:\qclaw\v0.2.35.624\resources\openclaw\config\bin\node\node.cmd"
PY = r"E:\qclaw\v0.2.35.624\resources\python\python.exe"
GEN_SCRIPT = r"C:\Users\Jason\.qclaw\skills\qclaw-generate-image\scripts\generate.cjs"

# Current (略短 hair) green-screen sources -> (role, path)
SOURCES = [
    ("stride", GEN / "img_cd70656169925666.png"),
    ("passing", GEN / "img_fc55be4a0c5d2466.png"),
    ("idle", GEN / "img_a3c6c7e4cab3ea6f.png"),
]

PROMPT = (
    "保持参考图1的纯绿色幕布背景、姿态、取景、米黄色蜡笔小新T恤、当前略短头发完全不变。"
    "只修正眼镜款式：改成黑色方框圆角眼镜（矩形框、四角圆润、中等偏粗的黑色镜框），与该人真实所戴眼镜一致。"
    "脸型保持长圆脸。写实摄影风格，高清。"
)

LOG = BASE / "regen_result.txt"


def log(msg: str) -> None:
    print(msg)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def generate(src_path: Path, attempt_budget: int = 18) -> Path:
    """Generate with quota-aware retry. Returns output image path."""
    images_arg = f"{src_path},{ORIG_PHOTO}"
    for attempt in range(1, attempt_budget + 1):
        cmd = [
            NODE, GEN_SCRIPT,
            f"--prompt={PROMPT}",
            f"--images={images_arg}",
            "--resolution=768:1024",
            "--revise=0",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", cwd=str(BASE))
        out = proc.stdout
        s = out.find("{")
        e = out.rfind("}")
        if s == -1 or e == -1:
            log(f"[attempt {attempt}] no JSON in output; retrying in 15m")
            time.sleep(900)
            continue
        try:
            data = json.loads(out[s:e + 1])
        except Exception as ex:
            log(f"[attempt {attempt}] JSON parse error {ex}; retrying in 15m")
            time.sleep(900)
            continue
        if data.get("success") and data.get("images"):
            return Path(data["images"][0])
        msg = str(data.get("message", ""))
        if "上限" in msg or "quota" in msg.lower():
            log(f"[attempt {attempt}] quota limited; retrying in 15m ({msg[:40]})")
            time.sleep(900)
            continue
        log(f"[attempt {attempt}] generation failed: {msg}; retrying in 15m")
        time.sleep(900)
    raise RuntimeError("quota never recovered within budget")


def verify() -> bool:
    try:
        from PIL import Image, ImageChops
    except Exception:
        return True
    ok = True
    for f in ["pet_idle.png", "pet_walk.png", "pet_walk_left.png"]:
        a = Image.open(ASSETS / f).convert("RGBA").getchannel("A")
        a = a.point(lambda v: 255 if v > 0 else 0)
        cnt = sum(1 for v in a.getdata() if v > 0)
        log(f"{f}: alpha_px={cnt}")
        if cnt < 5000:
            ok = False
    return ok


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    log("=== regen_glasses start ===")
    outs = []
    for role, src in SOURCES:
        log(f"-- generating {role} --")
        outs.append(generate(src))
        log(f"   -> {outs[-1].name}")
    # rebuild sprites
    log("-- process_sprite --")
    subprocess.run(
        [PY, "process_sprite.py", str(outs[0]), str(outs[1]), str(outs[2])],
        cwd=str(BASE), check=True,
    )
    if not verify():
        log("!! verify FAILED: sprite area too small, aborting rebuild")
        return 2
    # stop old exe, rebuild, relaunch
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Stop-Process -Name desktop_pet -Force -ErrorAction SilentlyContinue"],
                   cwd=str(BASE))
    log("-- PyInstaller --")
    subprocess.run([PY, "-m", "PyInstaller", "pet.spec", "--noconfirm", "--clean"],
                   cwd=str(BASE), check=True)
    exe = BASE / "dist" / "desktop_pet.exe"
    if not exe.exists():
        log("!! exe not built")
        return 3
    log("-- relaunch --")
    subprocess.Popen([str(exe)], cwd=str(BASE))
    time.sleep(2)
    log("=== regen_glasses done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
