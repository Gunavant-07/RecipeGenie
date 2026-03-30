from pathlib import Path
import ast


for file_name in ["app.py", "nutrition_utils.py", "nlp_utils.py"]:
    source = Path(file_name).read_text(encoding="utf-8")
    ast.parse(source, filename=file_name)
    print(f"OK: {file_name}")
