from pathlib import Path

lines = Path("app.py").read_text(encoding="utf-8").splitlines()
for start, end in [(395, 450)]:
    for i in range(start - 1, min(end, len(lines))):
        safe_line = lines[i].encode("ascii", errors="replace").decode("ascii")
        print(f"{i+1}:{safe_line}")
