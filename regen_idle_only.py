"""Finish the glasses fix using the stride/passing images that already
generated successfully before the image service went down (error 9002).

Only the idle frame still needs to be (re)generated; stride/passing are reused
from disk so we don't burn extra generations while the service is flaky.
"""
import subprocess
import sys
from pathlib import Path

import regen_glasses as rg

GEN = rg.GEN
# Already-generated, glasses-correct stride/passing from the earlier successful run
STRIDE = GEN / "img_2cc015415e33767b.png"
PASSING = GEN / "img_91bec430983b8d0c.png"
IDLE_SRC = GEN / "img_a3c6c7e4cab3ea6f.png"  # current idle green-screen source


def main() -> int:
    rg.LOG.write_text("", encoding="utf-8")
    rg.log("=== regen_idle_only start ===")
    if not (STRIDE.exists() and PASSING.exists()):
        rg.log("!! stride/passing sources missing; abort")
        return 1
    rg.log("-- regenerating idle --")
    idle = rg.generate(IDLE_SRC, attempt_budget=40)  # ~10h of 15m retries
    rg.log(f"   -> {idle.name}")
    rg.log("-- process_sprite --")
    subprocess.run([rg.PY, "process_sprite.py", str(STRIDE), str(PASSING), str(idle)],
                   cwd=rg.BASE, check=True)
    if not rg.verify():
        rg.log("!! verify FAILED: sprite area too small, aborting rebuild")
        return 2
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Stop-Process -Name desktop_pet -Force -ErrorAction SilentlyContinue"],
                   cwd=rg.BASE)
    rg.log("-- PyInstaller --")
    subprocess.run([rg.PY, "-m", "PyInstaller", "pet.spec", "--noconfirm", "--clean"],
                   cwd=rg.BASE, check=True)
    exe = rg.BASE / "dist" / "desktop_pet.exe"
    if not exe.exists():
        rg.log("!! exe not built")
        return 3
    rg.log("-- relaunch --")
    subprocess.Popen([str(exe)], cwd=rg.BASE)
    rg.log("=== regen_idle_only done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
