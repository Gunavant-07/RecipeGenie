import json
import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile


DATA_PATH = Path(__file__).with_name("nutrition_data.json")
EXCEL_DATA_PATH = Path(__file__).with_name("nutritiondata.xlsx")
NAMESPACE = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
UNITS_PATTERN = re.compile(
    r"\b(cup|cups|tbsp|tsp|teaspoon|teaspoons|tablespoon|tablespoons|kg|g|gm|grams|gram|ml|l|liter|litre|pinch|pinches|clove|cloves|piece|pieces|slice|slices)\b",
    re.IGNORECASE,
)
QUANTITY_PATTERN = re.compile(r"[\d/.-]+")
CUSTOM_ALIASES = {
    "curd": ["yogurt", "dahi"],
    "dahi": ["yogurt", "curd"],
    "atta": ["wheat flour", "whole wheat flour"],
    "palak": ["spinach"],
    "dhania": ["coriander"],
    "besan": ["gram flour", "chickpea flour"],
    "green chilli": ["green chili", "chili"],
    "toor dal": ["lentils", "dal"],
    "moong dal": ["lentils", "dal"],
    "masoor dal": ["lentils", "dal"],
    "chana dal": ["lentils", "dal"],
}


def normalize_food_text(value):
    text = str(value or "").strip().lower()
    text = text.replace("&", " and ")
    text = QUANTITY_PATTERN.sub(" ", text)
    text = UNITS_PATTERN.sub(" ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def prettify_label(value):
    return " ".join(word.capitalize() for word in str(value or "").split())


@lru_cache(maxsize=1)
def load_nutrition_records():
    excel_records = load_nutrition_records_from_excel()
    if excel_records:
        return excel_records

    if not DATA_PATH.exists():
        return []

    with DATA_PATH.open("r", encoding="utf-8") as nutrition_file:
        raw_records = json.load(nutrition_file)

    records = []
    for record in raw_records:
        aliases = [normalize_food_text(record.get("ingredient", ""))]
        aliases.extend(normalize_food_text(alias) for alias in record.get("aliases", []))
        aliases = [alias for alias in aliases if alias]

        records.append({
            "ingredient": record.get("ingredient", ""),
            "aliases": sorted(set(aliases)),
            "serving_factor": float(record.get("serving_factor", 0.35)),
            "calories": float(record.get("calories", 0)),
            "protein": float(record.get("protein", 0)),
            "carbs": float(record.get("carbs", 0)),
            "fat": float(record.get("fat", 0)),
            "fiber": float(record.get("fiber", 0)),
            "sugar": float(record.get("sugar", 0)),
            "sodium": float(record.get("sodium", 0)),
            "water": float(record.get("water", 0)),
            "calcium": float(record.get("calcium", 0)),
            "iron": float(record.get("iron", 0)),
            "magnesium": float(record.get("magnesium", 0)),
            "phosphorus": float(record.get("phosphorus", 0)),
            "potassium": float(record.get("potassium", 0)),
            "vitamin_a": float(record.get("vitamin_a", 0)),
            "vitamin_c": float(record.get("vitamin_c", 0)),
            "vitamin_e": float(record.get("vitamin_e", 0)),
        })

    return records


def read_shared_strings(workbook_zip):
    if "xl/sharedStrings.xml" not in workbook_zip.namelist():
        return []

    root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
    shared = []
    for item in root.findall("a:si", NAMESPACE):
        parts = [node.text or "" for node in item.findall(".//a:t", NAMESPACE)]
        shared.append("".join(parts))
    return shared


def get_first_sheet_path(workbook_zip):
    workbook_root = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
    rel_root = ET.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rel_root
    }

    first_sheet = workbook_root.find("a:sheets/a:sheet", NAMESPACE)
    if first_sheet is None:
        return None

    rel_id = first_sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    target = rel_map.get(rel_id)
    if not target:
        return None

    if not target.startswith("xl/"):
        target = f"xl/{target}"
    return target


def get_cell_text(cell, shared_strings):
    cell_type = cell.attrib.get("t")
    value_node = cell.find("a:v", NAMESPACE)
    if value_node is None:
        return ""

    value = value_node.text or ""
    if cell_type == "s":
        return shared_strings[int(value)]
    return value


def normalize_header(value):
    return normalize_food_text(value).replace(" ", "_")


def parse_excel_rows():
    if not EXCEL_DATA_PATH.exists():
        return []

    with ZipFile(EXCEL_DATA_PATH) as workbook_zip:
        sheet_path = get_first_sheet_path(workbook_zip)
        if not sheet_path:
            return []

        shared_strings = read_shared_strings(workbook_zip)
        sheet_root = ET.fromstring(workbook_zip.read(sheet_path))
        row_nodes = sheet_root.findall(".//a:sheetData/a:row", NAMESPACE)
        if not row_nodes:
            return []

        header_cells = row_nodes[0].findall("a:c", NAMESPACE)
        headers = [normalize_header(get_cell_text(cell, shared_strings)) for cell in header_cells]
        rows = []

        for row in row_nodes[1:]:
            values = [get_cell_text(cell, shared_strings) for cell in row.findall("a:c", NAMESPACE)]
            if not any(str(value).strip() for value in values):
                continue

            padded_values = values + [""] * (len(headers) - len(values))
            rows.append(dict(zip(headers, padded_values)))

        return rows


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_aliases(food_name):
    normalized = normalize_food_text(food_name)
    aliases = {normalized} if normalized else set()

    for source, mapped_values in CUSTOM_ALIASES.items():
        if normalized == source or normalized in mapped_values:
            aliases.add(source)
            aliases.update(normalize_food_text(item) for item in mapped_values)

    aliases.add(normalized.replace(" chilli", " chili"))
    aliases.add(normalized.replace(" chili", " chilli"))

    aliases = {alias for alias in aliases if alias}
    return sorted(aliases)


def load_nutrition_records_from_excel():
    raw_rows = parse_excel_rows()
    if not raw_rows:
        return []

    records = []
    for row in raw_rows:
        ingredient_name = row.get("name", "")
        if not ingredient_name:
            continue

        records.append({
            "ingredient": ingredient_name,
            "aliases": build_aliases(ingredient_name),
            "serving_factor": 0.35,
            "calories": safe_float(row.get("energy")),
            "protein": safe_float(row.get("protein")),
            "carbs": safe_float(row.get("carbs")),
            "fat": safe_float(row.get("fat")),
            "fiber": safe_float(row.get("fiber")),
            "sugar": safe_float(row.get("sugar")),
            "sodium": safe_float(row.get("sodium")),
            "water": safe_float(row.get("water")),
            "calcium": safe_float(row.get("calcium")),
            "iron": safe_float(row.get("iron")),
            "magnesium": safe_float(row.get("magnesium")),
            "phosphorus": safe_float(row.get("phosphorus")),
            "potassium": safe_float(row.get("potassium")),
            "vitamin_a": safe_float(row.get("vit_a")),
            "vitamin_c": safe_float(row.get("vit_c")),
            "vitamin_e": safe_float(row.get("vit_e")),
        })

    return records


def find_nutrition_match(ingredient_line):
    normalized = normalize_food_text(ingredient_line)
    if not normalized:
        return None, normalized

    records = load_nutrition_records()

    for record in records:
        if normalized in record["aliases"]:
            return record, normalized

    normalized_tokens = set(normalized.split())
    for record in records:
        for alias in record["aliases"]:
            alias_tokens = set(alias.split())
            if normalized == alias or normalized in alias or alias in normalized:
                return record, normalized
            if normalized_tokens and normalized_tokens.issubset(alias_tokens):
                return record, normalized

    return None, normalized


def keyword_risk_adjustment(normalized_ingredient):
    if not normalized_ingredient:
        return 0

    unhealthy_keywords = {"fried", "oil", "ghee", "butter", "cream", "sugar", "salt"}
    healthy_keywords = {"spinach", "methi", "lentils", "dal", "tomato", "onion", "yogurt", "paneer"}

    if any(keyword in normalized_ingredient for keyword in unhealthy_keywords):
        return -6

    if any(keyword in normalized_ingredient for keyword in healthy_keywords):
        return 4

    return 0


def classify_health_label(totals, ingredient_count):
    calories = totals["calories"]
    fat = totals["fat"]
    sugar = totals["sugar"]
    sodium = totals["sodium"]
    fiber = totals["fiber"]
    protein = totals["protein"]
    potassium = totals["potassium"]
    vitamin_c = totals["vitamin_c"]

    if calories >= 700 or fat >= 28 or sugar >= 22 or sodium >= 900:
        return "Unhealthy"

    if calories >= 460 or fat >= 16 or sugar >= 10 or sodium >= 450:
        return "Moderate"

    if fiber >= 8 or protein >= 16 or potassium >= 600 or vitamin_c >= 20 or ingredient_count >= 4:
        return "Healthy"

    return "Moderate"


def calculate_health_score(totals, ingredient_count, matched_count, unmatched_count):
    base_score = 60
    base_score += min(totals["protein"] * 1.2, 18)
    base_score += min(totals["fiber"] * 1.5, 18)
    base_score += min(totals["potassium"] / 100, 10)
    base_score += min(totals["vitamin_c"] / 5, 8)
    base_score += min(totals["iron"] * 1.5, 6)
    base_score -= min(totals["fat"] * 0.8, 20)
    base_score -= min(totals["sugar"] * 1.2, 20)
    base_score -= min(totals["sodium"] / 80, 20)
    base_score += min(ingredient_count * 1.8, 10)
    base_score += matched_count * 1.5
    base_score -= unmatched_count * 1.2
    return max(0, min(100, round(base_score, 2)))


def analyze_recipe_nutrition(ingredients):
    ingredients = ingredients or []
    totals = {
        "calories": 0.0,
        "water": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
        "fiber": 0.0,
        "sugar": 0.0,
        "sodium": 0.0,
        "calcium": 0.0,
        "iron": 0.0,
        "magnesium": 0.0,
        "phosphorus": 0.0,
        "potassium": 0.0,
        "vitamin_a": 0.0,
        "vitamin_c": 0.0,
        "vitamin_e": 0.0,
    }
    matched_ingredients = []
    unmatched_ingredients = []
    match_details = []
    heuristic_adjustment = 0

    for raw_ingredient in ingredients:
        record, normalized = find_nutrition_match(raw_ingredient)

        if record:
            factor = record["serving_factor"]
            matched_ingredients.append(raw_ingredient)
            match_details.append({
                "input": raw_ingredient,
                "matched_ingredient": record["ingredient"],
                "serving_factor": factor,
            })
            for nutrient in totals:
                totals[nutrient] += record[nutrient] * factor
        else:
            unmatched_ingredients.append(raw_ingredient)
            heuristic_adjustment += keyword_risk_adjustment(normalized)

    rounded_totals = {key: round(value, 2) for key, value in totals.items()}
    health_label = classify_health_label(rounded_totals, len(ingredients))
    health_score = calculate_health_score(
        rounded_totals,
        len(ingredients),
        len(matched_ingredients),
        len(unmatched_ingredients),
    ) + heuristic_adjustment
    health_score = max(0, min(100, round(health_score, 2)))

    if health_score >= 75:
        health_label = "Healthy"
    elif health_score <= 40:
        health_label = "Unhealthy"
    elif health_label == "Healthy" and health_score < 60:
        health_label = "Moderate"

    notes = []
    if rounded_totals["fiber"] >= 8:
        notes.append("Good fiber support")
    if rounded_totals["protein"] >= 16:
        notes.append("Good protein support")
    if rounded_totals["potassium"] >= 700:
        notes.append("Good potassium support")
    if rounded_totals["vitamin_c"] >= 20:
        notes.append("Good vitamin C support")
    if rounded_totals["iron"] >= 4:
        notes.append("Good iron support")
    if rounded_totals["sodium"] >= 700:
        notes.append("High sodium estimate")
    if rounded_totals["sugar"] >= 18:
        notes.append("High sugar estimate")
    if rounded_totals["fat"] >= 24:
        notes.append("High fat estimate")
    if not notes:
        notes.append("Estimated from ingredient nutrition matches")

    coverage = round((len(matched_ingredients) / len(ingredients)) * 100, 2) if ingredients else 0

    return {
        "health_label": health_label,
        "health_score": health_score,
        "coverage_percent": coverage,
        "matched_ingredients": matched_ingredients,
        "unmatched_ingredients": unmatched_ingredients,
        "match_details": match_details,
        "totals": rounded_totals,
        "notes": notes,
        "ingredient_count": len(ingredients),
    }


def recommendation_reason(recipe):
    label = recipe.get("health_label") or recipe.get("category") or "Moderate"
    score = recipe.get("health_score", 0)
    return f"{label} recipe with health score {score}"
