from pathlib import Path
import sys


def main() -> None:
    lines = Path("app.py").read_text(encoding="utf-8").splitlines()
    ranges = [
        (120, 360),
        (430, 860),
        (860, 1085),
        (1180, 1225),
    ]
    for start, end in ranges:
        print(f"\n--- {start}-{end} ---")
        for i in range(start - 1, min(end, len(lines))):
            safe_line = lines[i].encode("ascii", errors="replace").decode("ascii")
            print(f"{i+1}:{safe_line}")


if __name__ == "__main__":
    main()
