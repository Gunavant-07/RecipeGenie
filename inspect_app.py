from pathlib import Path


def main() -> None:
    text = Path("app.py").read_text(encoding="utf-8")
    lines = text.splitlines()
    patterns = [
        "collection('recipes')",
        'collection("recipes")',
        "upload_all_recipes",
        "upload_gujarati_recipes",
        "def get_recipes",
        "def recommend",
        "def recipe_detail",
        "def get_favorites",
        "def get_history",
        "backfill_recipe_health_data",
        "def admin_backfill_health_data",
        "def get_healthy_recommendations",
        "def store_cooked_recipe",
    ]
    for needle in patterns:
        for idx, line in enumerate(lines, start=1):
            if needle in line:
                print(f"{idx}:{line}")


if __name__ == "__main__":
    main()
