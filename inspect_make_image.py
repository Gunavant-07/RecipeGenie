from pathlib import Path

lines = Path("app.py").read_text(encoding="utf-8").splitlines()
for idx, line in enumerate(lines, start=1):
    if "make_image_url" in line:
        for i in range(max(0, idx - 3), min(len(lines), idx + 25)):
            safe_line = lines[i].encode("ascii", errors="replace").decode("ascii")
            print(f"{i+1}:{safe_line}")
