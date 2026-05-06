
from ultralytics import YOLO
from flask import Flask, request, jsonify, render_template ,redirect, url_for
from flask_cors import CORS
from firebase_admin import auth
import pandas as pd
from ml_models import train_health_classifier, classify_recipe_health, recommend_recipes, personalized_recommendations
from nlp_utils import process_ingredients, parse_user_food_demand
from nutrition_utils import analyze_recipe_nutrition, recommendation_reason
import datetime
import random
from firebase_config import database,datab
from google.api_core.exceptions import FailedPrecondition
import re
import numpy as np
import cv2
import ast
import os



app = Flask(__name__)
CORS(app)  

SINGLE_MODEL_PATH = r"E:\RecipeGenie\RecipeGenie\model\single.pt"
MULTIPLE_MODEL_PATH = r"E:\RecipeGenie\RecipeGenie\model\multimodel.pt"
LEGACY_MULTIPLE_MODEL_PATH = r"E:\RecipeGenie\RecipeGenie\model\best.pt"
FALLBACK_MODEL_PATH = r"E:\RecipeGenie\RecipeGenie\model\best.pt"

DETECTION_MODEL_PATHS = {
    "single": SINGLE_MODEL_PATH if os.path.exists(SINGLE_MODEL_PATH) else LEGACY_MULTIPLE_MODEL_PATH,
    "multiple": MULTIPLE_MODEL_PATH if os.path.exists(MULTIPLE_MODEL_PATH) else LEGACY_MULTIPLE_MODEL_PATH,
}

_detection_model_cache = {}


def normalize_detection_model_type(value):
    model_type = str(value or "single").strip().lower()
    if model_type in {"multi", "multiple", "multimodel", "multiple.pt", "multimodel.pt"}:
        return "multiple"
    return "single"


def get_detection_model(model_type):
    normalized_type = normalize_detection_model_type(model_type)
    model_path = DETECTION_MODEL_PATHS.get(normalized_type, DETECTION_MODEL_PATHS["single"])

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"YOLO model not found for {normalized_type}: {model_path}")

    if normalized_type not in _detection_model_cache:
        print(f"Loading YOLO {normalized_type} ingredient model: {model_path}")
        _detection_model_cache[normalized_type] = YOLO(model_path)
        print(f"YOLO {normalized_type} model loaded successfully!")

    return _detection_model_cache[normalized_type]


print("YOLO ingredient models will load on first detection request.")

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')


@app.route("/detect-ingredients", methods=["POST"])
def detect():

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    image_bytes = file.read()
    model_type = normalize_detection_model_type(
        request.form.get("model_type") or request.form.get("model") or request.args.get("model_type")
    )

    try:
        detected = detect_ingredients(image_bytes, model_type=model_type)
    except FileNotFoundError as e:
        return jsonify({"error": str(e), "ingredients": [], "model_type": model_type}), 500

    return jsonify({
        "ingredients": detected,
        "model_type": model_type
    })


def detect_ingredients(image_bytes, model_type="single"):

    # Convert bytes → image
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return []

    detector = get_detection_model(model_type)

    # Run YOLO
    results = detector(img)

    detected = []

    for r in results:
        for box in r.boxes:

            conf = float(box.conf[0])
            cls_id = int(box.cls[0])

            if conf > 0.4:
                label = detector.names[cls_id]
                detected.append(label)

    return list(dict.fromkeys(detected))  # remove duplicates




    
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/history-page')
def history_page():
    return render_template('history.html')

@app.route('/health')
def health_page():
    return render_template('health.html')

@app.route('/generate-recipe-page')
def generate_recipe_page():
    return render_template('generateRecipe.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

# user authentication on register
@app.route('/save-user', methods=['POST'])
def save_user():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON received"}), 400

        print("Received:", data)

        uid = data.get("uid")
        name = data.get("name")
        email = data.get("email")

        if not uid:
            return jsonify({"error": "UID missing"}), 400

        database.child("users").child(uid).set({
            "name": name,
            "email": email,
            "healthy_count": 0,
            "fastfood_count": 0,
            "unhealthy_count": 0,
            "moderate_count": 0,
            "health_score": 0,
            "last_notification": ""
        })

        return jsonify({"message": "User saved"}), 200

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


# Login
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            user = auth.get_user_by_email(email)

            # (Important: Firebase Admin does NOT verify password)
            # For real production, use Firebase JS login.

            return redirect(url_for('dashboard'))

        except Exception as e:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')
   

# #....................................................................................
CSV_FILE = 'E:/RecipeGenie/RecipeGenie/archive/Recipe_Dataset.csv'

ALL_RECIPES_COLLECTION = 'all_recipes'
LEGACY_RECIPES_COLLECTION = 'recipes'
STATE_INDEX_COLLECTION = 'recipe_state_index'
CHECK_FOR_DUPLICATES = True                  # prevent re-uploading same recipe name

FALLBACK_IMAGE = "https://res.cloudinary.com/dvu9cofjk/image/upload/v1775146706/image_not_found_bmltnt.png"
# # ==============================================


def safe_image_url(value):
    image_url = str(value or "").strip()
    if re.match(r"^(https?://|/static/|/uploads/)", image_url, flags=re.IGNORECASE):
        return image_url
    return FALLBACK_IMAGE


def recipe_collection():
    return datab.collection(ALL_RECIPES_COLLECTION)


def legacy_recipe_collection():
    return datab.collection(LEGACY_RECIPES_COLLECTION)


def normalize_state_name(value):
    cleaned = re.sub(r"\s+", " ", str(value or "").replace("-", " ").replace("_", " ")).strip()
    if not cleaned:
        return "Unknown"
    return cleaned.title()


def state_slug(value):
    return re.sub(r"[^a-z0-9]+", "-", normalize_state_name(value).lower()).strip("-") or "unknown"


def extract_state_labels(raw_value):
    if raw_value is None:
        return ["Unknown"]

    if isinstance(raw_value, list):
        candidates = raw_value
    else:
        text = str(raw_value)
        candidates = re.split(r"[/,;|]+|\band\b", text, flags=re.IGNORECASE)

    labels = []
    seen = set()
    for candidate in candidates:
        label = normalize_state_name(candidate)
        if label and label not in seen:
            labels.append(label)
            seen.add(label)

    return labels or ["Unknown"]


def get_recipe_doc_ref(recipe_id):
    primary_ref = recipe_collection().document(recipe_id)
    primary_snapshot = primary_ref.get()
    if primary_snapshot.exists:
        return primary_ref, primary_snapshot

    legacy_ref = legacy_recipe_collection().document(recipe_id)
    legacy_snapshot = legacy_ref.get()
    if legacy_snapshot.exists:
        return legacy_ref, legacy_snapshot

    return primary_ref, primary_snapshot


def stream_recipe_docs():
    primary_docs = list(recipe_collection().stream())
    if primary_docs:
        return primary_docs
    return list(legacy_recipe_collection().stream())


RECIPE_CACHE_TTL_SECONDS = 300
_recipe_cache = {
    "recipes": None,
    "loaded_at": None,
}


def load_normalized_recipe_cache():
    recipes = []
    for recipe_doc in stream_recipe_docs():
        recipes.append(normalize_recipe_document(recipe_doc.id, recipe_doc.to_dict() or {}))
    _recipe_cache["recipes"] = recipes
    _recipe_cache["loaded_at"] = datetime.datetime.utcnow()
    return recipes


def get_cached_normalized_recipes(force_refresh=False):
    loaded_at = _recipe_cache.get("loaded_at")
    recipes = _recipe_cache.get("recipes")
    cache_expired = (
        loaded_at is None or
        (datetime.datetime.utcnow() - loaded_at).total_seconds() > RECIPE_CACHE_TTL_SECONDS
    )

    if force_refresh or recipes is None or cache_expired:
        return load_normalized_recipe_cache()

    return recipes


def fetch_recipe_by_id(recipe_id, ensure_health=True):
    _, recipe_snapshot = get_recipe_doc_ref(recipe_id)
    if not recipe_snapshot.exists:
        return None

    recipe_data = recipe_snapshot.to_dict() or {}
    if ensure_health:
        return ensure_recipe_health_data(recipe_id, recipe_data)
    return normalize_recipe_document(recipe_id, recipe_data)


def fetch_state_recipe_ids(state_name):
    normalized_state = normalize_state_name(state_name)
    state_index_doc = datab.collection(STATE_INDEX_COLLECTION).document(state_slug(normalized_state)).get()

    if state_index_doc.exists:
        state_data = state_index_doc.to_dict() or {}
        recipe_ids = state_data.get("recipe_ids", [])
        if isinstance(recipe_ids, list):
            return recipe_ids

    matched_ids = []
    for recipe_doc in stream_recipe_docs():
        recipe_data = recipe_doc.to_dict() or {}
        state_tags = [normalize_state_name(tag) for tag in recipe_data.get("state_tags", [])]
        primary_state = normalize_state_name(recipe_data.get("primary_state", ""))
        if normalized_state == primary_state or normalized_state in state_tags:
            matched_ids.append(recipe_doc.id)

    return matched_ids


def recipe_rating_value(recipe):
    try:
        return float(recipe.get("ratings") or 0)
    except (TypeError, ValueError):
        return 0.0


def first_present_value(data, keys, default=""):
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        if isinstance(value, float) and pd.isna(value):
            continue
        text = str(value).strip()
        if text and text.lower() != "nan":
            return value
    return default


def clean_cuisine_label(value):
    if value is None:
        return ""

    text = str(value).strip().replace("\ufeff", " ")

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple)) and parsed:
            text = str(parsed[0]).strip()
    except (ValueError, SyntaxError):
        pass

    text = re.sub(r"^\s*Cuisine\s*:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bRecipes?\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\[\]\(\)'\"{}:]", " ", text)
    text = re.sub(r"[^A-Za-z0-9 &-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_cuisine_text(value):
    return re.sub(r"\s+", " ", clean_cuisine_label(value).lower()).strip()


def cuisine_search_terms(cuisine):
    selected = normalize_cuisine_text(cuisine)
    if not selected or selected == "all":
        return []
    return [selected]


def recipe_matches_cuisine(recipe, cuisine):
    selected_terms = cuisine_search_terms(cuisine)
    if not selected_terms:
        return True

    direct_cuisine_values = [
        recipe.get("cuisine_key", ""),
        recipe.get("cuisine_name", ""),
        recipe.get("Cuisine_name", ""),
        recipe.get("cuisine", ""),
        recipe.get("Cuisine", ""),
        recipe.get("CuisineName", ""),
    ]
    direct_keys = {normalize_cuisine_text(value) for value in direct_cuisine_values if normalize_cuisine_text(value)}

    if direct_keys:
        return any(term in direct_keys for term in selected_terms)

    legacy_values = [
        recipe.get("primary_state", ""),
        " ".join(recipe.get("state_tags", [])) if isinstance(recipe.get("state_tags"), list) else recipe.get("state_tags", ""),
    ]
    legacy_keys = {normalize_cuisine_text(value) for value in legacy_values if normalize_cuisine_text(value)}
    return any(term in legacy_keys for term in selected_terms)


def filter_and_sort_recipes(recipes, search="", high_rated=False, cuisine="All"):
    filtered = []
    search_term = str(search or "").strip().lower()

    for recipe in recipes:
        name_lower = str(recipe.get("name", "")).lower()
        if search_term and search_term not in name_lower:
            continue
        if not recipe_matches_cuisine(recipe, cuisine):
            continue
        if high_rated and recipe_rating_value(recipe) < 4.5:
            continue
        filtered.append(recipe)

    filtered.sort(key=lambda recipe: (str(recipe.get("name", "")).lower(), recipe.get("recipe_id", "")))
    return filtered


def fetch_candidate_recipes_for_listing(state="All", cuisine="All"):
    if state and state != "All":
        candidate_recipes = []
        state_recipe_ids = fetch_state_recipe_ids(state)
        print(f"[DEBUG] Loaded {len(state_recipe_ids)} indexed recipe IDs for state={state}")
        for recipe_id in state_recipe_ids:
            recipe = fetch_recipe_by_id(recipe_id, ensure_health=False)
            if recipe:
                candidate_recipes.append(recipe)
        return candidate_recipes

    selected_cuisine = normalize_cuisine_text(cuisine)
    if selected_cuisine and selected_cuisine != "all":
        try:
            cuisine_docs = list(recipe_collection().where("cuisine_key", "==", selected_cuisine).stream())
            if cuisine_docs:
                print(f"[DEBUG] Loaded {len(cuisine_docs)} recipes using cuisine_key index for cuisine={selected_cuisine}")
                return [normalize_recipe_document(doc.id, doc.to_dict() or {}) for doc in cuisine_docs]
        except Exception as cuisine_query_error:
            print("[WARN] cuisine_key query failed, using cache fallback:", cuisine_query_error)

    return get_cached_normalized_recipes()


def paginate_recipe_list(recipes, limit, last_doc_id=None):
    start_index = 0

    if last_doc_id:
        for idx, recipe in enumerate(recipes):
            if recipe.get("recipe_id") == last_doc_id:
                start_index = idx + 1
                break

    page = recipes[start_index:start_index + limit]
    next_cursor = page[-1]["recipe_id"] if page else None
    has_more = start_index + limit < len(recipes)
    return page, next_cursor, has_more


def get_row_value(row, possible_columns, default=""):
    for column in possible_columns:
        if column in row and not pd.isna(row.get(column)):
            value = row.get(column)
            value = str(value).strip()
            if value and value.lower() != "nan":
                return value
    return default


def load_existing_recipe_name_map():
    if not CHECK_FOR_DUPLICATES:
        return {}

    print("Loading existing recipe names from Firestore once...")
    existing_by_name = {}
    for recipe_doc in recipe_collection().stream():
        recipe_data = recipe_doc.to_dict() or {}
        recipe_name = str(recipe_data.get("name", "")).strip().lower()
        if recipe_name:
            existing_by_name[recipe_name] = {
                "id": recipe_doc.id,
                "state_tags": recipe_data.get("state_tags", []),
            }

    print(f"Loaded {len(existing_by_name)} existing recipe names.")
    return existing_by_name


def commit_firestore_batch(batch, pending_writes):
    if pending_writes <= 0:
        return 0

    batch.commit()
    return 0


def upload_all_recipes():
    print("=== STARTING FIRESTORE UPLOAD SCRIPT ===")
    print(f"Reading CSV file: {CSV_FILE}")

    try:
        df = pd.read_csv(CSV_FILE)
        print(f"Total rows in CSV: {len(df)}")

        if df.empty:
            print("ERROR: CSV is empty.")
            return {
                "status": "error",
                "message": "CSV file is empty.",
                "uploaded_count": 0,
                "skipped_count": 0,
                "state_indexes_updated": 0,
            }

        uploaded_count = 0
        skipped_count = 0
        state_index_map = {}
        existing_by_name = load_existing_recipe_name_map()
        batch = datab.batch()
        pending_writes = 0

        for _, row in df.iterrows():
            original_name = get_row_value(row, ['name_of_Dish', 'TranslatedRecipeName', 'RecipeName', 'name', 'Name'], 'Unknown Recipe')
            recipe_name = clean_recipe_name(original_name)
            image_link = get_row_value(
                row,
                ['Image_Link', 'image_link', 'Image link', 'image', 'Image', 'image-url', 'Image URL', 'URL'],
                FALLBACK_IMAGE
            )
            cuisine_label = clean_cuisine_label(
                get_row_value(row, ['Cuisine_name', 'Cuisine', 'CuisineName', 'Region', 'State'], 'Unknown')
            ) or "Unknown"
            state_labels = extract_state_labels(cuisine_label)

            if CHECK_FOR_DUPLICATES:
                existing = existing_by_name.get(recipe_name.lower())
                if existing:
                    existing_states = existing.get("state_tags", [])
                    merged_states = sorted(set(existing_states + state_labels))

                    if merged_states != existing_states:
                        batch.update(recipe_collection().document(existing["id"]), {
                            "state_tags": merged_states,
                            "primary_state": merged_states[0] if merged_states else "Unknown",
                            "cuisine_name": cuisine_label,
                            "cuisine_key": normalize_cuisine_text(cuisine_label)
                        })
                        pending_writes += 1
                        existing["state_tags"] = merged_states

                    for label in merged_states:
                        slug = state_slug(label)
                        state_index_map.setdefault(slug, {"state_name": label, "recipe_ids": set()})
                        state_index_map[slug]["recipe_ids"].add(existing["id"])

                    skipped_count += 1
                    if pending_writes >= 400:
                        pending_writes = commit_firestore_batch(batch, pending_writes)
                        batch = datab.batch()
                        print(f"Processed {skipped_count} duplicate recipes so far...")
                    continue

            ingredients = normalize_text_list(get_row_value(row, ['Ingredients_of_Dish', 'TranslatedIngredients', 'Ingredients', 'ingredients'], ''))
            steps = normalize_text_list(get_row_value(row, ['Recipe_Instructions', 'TranslatedInstructions', 'Instructions', 'steps'], ''))
            ing_str = ' '.join(ingredients).lower()
            instructions_str = ' '.join(steps).lower()

            oil_amount = 'high' if ing_str.count('oil') > 1 else 'medium' if 'oil' in ing_str else 'low'
            calories = random.randint(150, 600) if pd.isna(row.get('calories')) else row.get('calories', random.randint(150, 600))
            fried = 'yes' if 'fry' in instructions_str else 'no'
            sugar = 'high' if ing_str.count('sugar') > 1 else 'medium' if 'sugar' in ing_str else 'low'

            features = {
                'oil_amount': oil_amount,
                'calories': calories,
                'fried': fried,
                'sugar': sugar
            }

            try:
                category = classify_recipe_health(features)
            except Exception as e:
                print(f"Classification fallback for {recipe_name}: {e}")
                category = 'Moderate'

            data = {
                'recipe_id': '',
                'name': recipe_name,
                'image_url': image_link,
                'ingredients': ingredients,
                'ingredient_tokens': build_recipe_ingredient_tokens(ingredients),
                'steps': steps,
                'category': category,
                'nutrition_type': get_row_value(row, ['Diet_Type', 'Diet', 'DietType'], 'Vegetarian'),
                'diet_type': get_row_value(row, ['Diet_Type', 'Diet', 'DietType'], 'Vegetarian'),
                'course': get_row_value(row, ['Course_name', 'Course'], ''),
                'description': get_row_value(row, ['Discription_of_Dish', 'Discrption_of_Dish', 'Description', 'TranslatedDescription'], ''),
                'ratings': get_row_value(row, ['Ratings_of_Dish', 'Rating', 'ratings'], 4.0),
                'prep_time': get_row_value(row, ['Preparation_time', 'Prepration_time', 'PrepTimeInMins'], ''),
                'cook_time': get_row_value(row, ['Cooking_time', 'CookTimeInMins'], ''),
                'total_time': get_row_value(row, ['Total_time', 'TotalTimeInMins'], ''),
                'servings': get_row_value(row, ['Makes', 'Servings'], ''),
                'cuisine_name': cuisine_label,
                'cuisine_key': normalize_cuisine_text(cuisine_label),
                'state_tags': state_labels,
                'primary_state': state_labels[0] if state_labels else 'Unknown',
                'uploaded_at': pd.Timestamp.now().isoformat()
            }

            data = enrich_recipe_with_health_data(data)

            doc_ref = recipe_collection().document()
            data['recipe_id'] = doc_ref.id
            batch.set(doc_ref, data)
            pending_writes += 1
            uploaded_count += 1
            existing_by_name[recipe_name.lower()] = {
                "id": doc_ref.id,
                "state_tags": state_labels,
            }

            for label in state_labels:
                slug = state_slug(label)
                state_index_map.setdefault(slug, {"state_name": label, "recipe_ids": set()})
                state_index_map[slug]["recipe_ids"].add(doc_ref.id)

            if pending_writes >= 400:
                pending_writes = commit_firestore_batch(batch, pending_writes)
                batch = datab.batch()
                print(f"Uploaded {uploaded_count} recipes so far...")

        pending_writes = commit_firestore_batch(batch, pending_writes)

        for slug, state_data in state_index_map.items():
            state_doc_ref = datab.collection(STATE_INDEX_COLLECTION).document(slug)
            existing_doc = state_doc_ref.get()
            existing_ids = []
            if existing_doc.exists:
                existing_ids = existing_doc.to_dict().get("recipe_ids", [])

            merged_ids = sorted(set(existing_ids) | state_data["recipe_ids"])
            state_doc_ref.set({
                "state_name": state_data["state_name"],
                "state_slug": slug,
                "recipe_count": len(merged_ids),
                "recipe_ids": merged_ids,
                "updated_at": pd.Timestamp.now().isoformat()
            })

        print(f"Upload complete. Uploaded: {uploaded_count}, Skipped duplicates: {skipped_count}")
        return {
            "status": "success",
            "message": "Recipes uploaded successfully.",
            "uploaded_count": uploaded_count,
            "skipped_count": skipped_count,
            "state_indexes_updated": len(state_index_map),
            "total_rows": len(df),
        }

    except FileNotFoundError:
        print(f"ERROR: File not found → {CSV_FILE}")
        return {
            "status": "error",
            "message": f"CSV file not found: {CSV_FILE}",
            "uploaded_count": 0,
            "skipped_count": 0,
            "state_indexes_updated": 0,
        }
    except Exception as e:
        print("Unexpected error during upload:")
        print(str(e))
        return {
            "status": "error",
            "message": str(e),
            "uploaded_count": 0,
            "skipped_count": 0,
            "state_indexes_updated": 0,
        }


def upload_gujarati_recipes():
    return upload_all_recipes()
# #....................................................................................   

def clean_recipe_name(name: str) -> str:
    if not isinstance(name, str):
        return "Unknown Recipe"

    cleaned = name.strip()

    # Replace unwanted characters with space
    cleaned = cleaned.replace("/", " ")
    cleaned = cleaned.replace("\\", " ")
    cleaned = cleaned.replace("_", " ")
    cleaned = cleaned.replace("|", " ")
    cleaned = cleaned.replace(":", " ")
    cleaned = cleaned.replace("?", " ")
    cleaned = cleaned.replace("*", " ")
    cleaned = cleaned.replace("\"", " ")
    cleaned = cleaned.replace("<", " ")
    cleaned = cleaned.replace(">", " ")

    # Remove extra spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned

def make_image_url(recipe_name: str) -> str:
    return FALLBACK_IMAGE


def enrich_recipe_with_health_data(recipe_data):
    nutrition_analysis = analyze_recipe_nutrition(recipe_data.get("ingredients", []))
    recipe_data["nutrition"] = nutrition_analysis["totals"]
    recipe_data["nutrition_coverage"] = nutrition_analysis["coverage_percent"]
    recipe_data["nutrition_notes"] = nutrition_analysis["notes"]
    recipe_data["health_label"] = nutrition_analysis["health_label"]
    recipe_data["health_score"] = nutrition_analysis["health_score"]
    recipe_data["nutrition_matched_ingredients"] = nutrition_analysis["matched_ingredients"]
    recipe_data["nutrition_unmatched_ingredients"] = nutrition_analysis["unmatched_ingredients"]
    return recipe_data


def normalize_text_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]

    text = str(value).strip()
    if not text:
        return []

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple)):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except (ValueError, SyntaxError):
        pass

    if "\n" in text:
        parts = [part.strip(" -•\t") for part in re.split(r"[\r\n]+", text) if part.strip(" -•\t")]
        if len(parts) > 1:
            return parts

    if "," in text:
        parts = [part.strip() for part in text.split(",") if part.strip()]
        if len(parts) > 1:
            return parts

    if ";" in text:
        parts = [part.strip() for part in text.split(";") if part.strip()]
        if len(parts) > 1:
            return parts

    return [text]


def normalize_recipe_document(recipe_id, recipe_data):
    if recipe_data is None:
        return None

    normalized = dict(recipe_data)
    normalized["recipe_id"] = recipe_id
    normalized["image_url"] = safe_image_url(normalized.get("image_url") or normalized.get("image"))
    cuisine_label = clean_cuisine_label(first_present_value(normalized, [
        "cuisine_name",
        "Cuisine_name",
        "cuisine",
        "Cuisine",
        "CuisineName",
        "Region",
        "State",
        "primary_state",
        "state"
    ]))
    normalized["cuisine_name"] = cuisine_label or "Unknown"
    normalized["cuisine_key"] = normalize_cuisine_text(cuisine_label)
    normalized["ingredients"] = normalize_text_list(normalized.get("ingredients", []))
    normalized["ingredient_tokens"] = normalize_text_list(
        normalized.get("ingredient_tokens") or build_recipe_ingredient_tokens(normalized["ingredients"])
    )
    normalized["steps"] = normalize_text_list(normalized.get("steps", []))
    normalized["nutrition_notes"] = normalize_text_list(normalized.get("nutrition_notes", []))
    normalized["nutrition_matched_ingredients"] = normalize_text_list(normalized.get("nutrition_matched_ingredients", []))
    normalized["nutrition_unmatched_ingredients"] = normalize_text_list(normalized.get("nutrition_unmatched_ingredients", []))
    return normalized


def ensure_recipe_health_data(recipe_id, recipe_data):
    if recipe_data is None:
        return None

    normalized_recipe = normalize_recipe_document(recipe_id, recipe_data)

    if normalized_recipe.get("nutrition") and normalized_recipe.get("health_label") and normalized_recipe.get("health_score") is not None:
        return normalized_recipe

    enriched = enrich_recipe_with_health_data(dict(normalized_recipe))
    enriched["recipe_id"] = recipe_id
    recipe_ref, _ = get_recipe_doc_ref(recipe_id)
    recipe_ref.update({
        "nutrition": enriched["nutrition"],
        "nutrition_coverage": enriched["nutrition_coverage"],
        "nutrition_notes": enriched["nutrition_notes"],
        "health_label": enriched["health_label"],
        "health_score": enriched["health_score"],
        "nutrition_matched_ingredients": enriched["nutrition_matched_ingredients"],
        "nutrition_unmatched_ingredients": enriched["nutrition_unmatched_ingredients"],
    })
    return normalize_recipe_document(recipe_id, enriched)


def count_key_for_label(label):
    normalized = str(label or "").strip().lower()
    if normalized == "healthy":
        return "healthy_count"
    if normalized == "moderate":
        return "moderate_count"
    return "unhealthy_count"


def fetch_user_profile(user_id):
    user_ref = database.child("users").child(user_id)
    user_data = user_ref.get() or {}

    defaults = {
        "healthy_count": 0,
        "moderate_count": 0,
        "unhealthy_count": 0,
        "fastfood_count": 0,
        "health_score": 0,
        "last_notification": "",
    }

    for key, value in defaults.items():
        user_data.setdefault(key, value)

    return user_ref, user_data


def get_healthy_recommendations(limit=5, exclude_recipe_id=None):
    recommendations = []
    seen_ids = set()

    healthy_query = recipe_collection().where("health_label", "==", "Healthy").limit(limit * 3).stream()

    for doc in healthy_query:
        if doc.id == exclude_recipe_id or doc.id in seen_ids:
            continue

        recipe = doc.to_dict() or {}
        recipe["recipe_id"] = doc.id
        recommendations.append({
            "recipe_id": doc.id,
            "name": recipe.get("name", "Recipe"),
            "health_label": recipe.get("health_label", "Healthy"),
            "health_score": recipe.get("health_score", 0),
            "reason": recommendation_reason(recipe)
        })
        seen_ids.add(doc.id)

        if len(recommendations) >= limit:
            return recommendations

    if len(recommendations) < limit:
        fallback_docs = stream_recipe_docs()
        for doc in fallback_docs:
            if doc.id == exclude_recipe_id or doc.id in seen_ids:
                continue

            recipe = ensure_recipe_health_data(doc.id, doc.to_dict() or {})
            if recipe.get("health_label") != "Healthy":
                continue

            recommendations.append({
                "recipe_id": doc.id,
                "name": recipe.get("name", "Recipe"),
                "health_label": recipe.get("health_label", "Healthy"),
                "health_score": recipe.get("health_score", 0),
                "reason": recommendation_reason(recipe)
            })
            seen_ids.add(doc.id)

            if len(recommendations) >= limit:
                break

    return recommendations


def build_user_health_summary(user_profile, cook_events):
    healthy = int(user_profile.get("healthy_count", 0))
    moderate = int(user_profile.get("moderate_count", 0))
    unhealthy = int(user_profile.get("unhealthy_count", 0) or user_profile.get("fastfood_count", 0))
    total_meals = healthy + moderate + unhealthy

    recent_events = sorted(
        cook_events,
        key=lambda event: event.get("cooked_at", ""),
        reverse=True
    )[:7]

    warning = ""
    if total_meals and unhealthy / total_meals >= 0.5:
        warning = "You are eating too many unhealthy meals recently. Try a healthy recipe next."
    elif len(recent_events) >= 3 and all(event.get("health_label") == "Unhealthy" for event in recent_events[:3]):
        warning = "Your last three meals were unhealthy. Please add a balanced or healthy meal next."

    return {
        "healthy": healthy,
        "moderate": moderate,
        "unhealthy": unhealthy,
        "total_meals": total_meals,
        "health_score": int(user_profile.get("health_score", 0)),
        "warning": warning,
        "recent_events": recent_events,
    }


def build_dashboard_summary(user_id):
    user_ref, user_profile = fetch_user_profile(user_id)
    cook_events_snapshot = user_ref.child("cook_events").get() or {}
    cook_events = list(cook_events_snapshot.values()) if isinstance(cook_events_snapshot, dict) else []
    summary = build_user_health_summary(user_profile, cook_events)

    favorite_snapshot = user_ref.child("favorites").get() or {}
    favorite_count = len(favorite_snapshot.keys()) if isinstance(favorite_snapshot, dict) else 0

    latest_meals = []
    for meal in summary["recent_events"][:3]:
        latest_meals.append({
            "recipe_name": meal.get("recipe_name", "Recipe"),
            "health_label": meal.get("health_label", "Moderate"),
            "health_score": meal.get("health_score", 0),
            "cooked_at": meal.get("cooked_at", "")
        })

    smart_tip = summary["warning"] or "Keep balancing healthy, moderate, and treat meals through the week."

    return {
        "total_recipes_cooked": summary["total_meals"],
        "healthy": summary["healthy"],
        "moderate": summary["moderate"],
        "unhealthy": summary["unhealthy"],
        "favorite_count": favorite_count,
        "health_score": summary["health_score"],
        "warning": summary["warning"],
        "smart_tip": smart_tip,
        "recent_meals": latest_meals,
    }


def store_cooked_recipe(user_id, recipe_id):
    recipe = fetch_recipe_by_id(recipe_id, ensure_health=True)
    if not recipe:
        return None, {"error": "Recipe not found"}

    user_ref, user_profile = fetch_user_profile(user_id)

    label = recipe.get("health_label", "Moderate")
    counter_key = count_key_for_label(label)
    user_profile[counter_key] = int(user_profile.get(counter_key, 0)) + 1

    if counter_key == "unhealthy_count":
        user_profile["fastfood_count"] = user_profile[counter_key]

    user_profile["health_score"] = (
        int(user_profile.get("healthy_count", 0)) * 2
        + int(user_profile.get("moderate_count", 0))
        - int(user_profile.get("unhealthy_count", 0)) * 2
    )

    cooked_entry = {
        "recipe_id": recipe_id,
        "recipe_name": recipe.get("name", "Recipe"),
        "health_label": label,
        "health_score": recipe.get("health_score", 0),
        "nutrition": recipe.get("nutrition", {}),
        "nutrition_notes": recipe.get("nutrition_notes", []),
        "cooked_at": datetime.datetime.now().isoformat(),
    }

    cooked_recipe_ref = user_ref.child("cooked_recipes").child(recipe_id)
    existing_cooked_recipe = cooked_recipe_ref.get() or {}
    cooked_entry["cook_count"] = int(existing_cooked_recipe.get("cook_count", 0)) + 1
    cooked_recipe_ref.update(cooked_entry)

    user_ref.child("cook_events").push(cooked_entry)

    datab.collection("history").add({
        "user_id": user_id,
        "recipe_id": recipe_id,
        "health_label": label,
        "nutrition": recipe.get("nutrition", {}),
        "date": datetime.datetime.now()
    })

    cook_events_snapshot = user_ref.child("cook_events").get() or {}
    cook_events = list(cook_events_snapshot.values()) if isinstance(cook_events_snapshot, dict) else []
    summary = build_user_health_summary(user_profile, cook_events)
    notification = summary["warning"]

    if notification:
        user_profile["last_notification"] = notification

    user_ref.update({
        "healthy_count": int(user_profile.get("healthy_count", 0)),
        "moderate_count": int(user_profile.get("moderate_count", 0)),
        "unhealthy_count": int(user_profile.get("unhealthy_count", 0)),
        "fastfood_count": int(user_profile.get("fastfood_count", 0)),
        "health_score": int(user_profile.get("health_score", 0)),
        "last_notification": user_profile.get("last_notification", ""),
    })

    recommendations = get_healthy_recommendations(limit=5, exclude_recipe_id=recipe_id)

    return recipe, {
        "message": f"{recipe.get('name', 'Recipe')} saved to your cooked history.",
        "health_label": label,
        "health_score": recipe.get("health_score", 0),
        "nutrition": recipe.get("nutrition", {}),
        "nutrition_notes": recipe.get("nutrition_notes", []),
        "notification": notification,
        "recommendations": recommendations,
    }


def backfill_recipe_health_data(limit=None):
    updated = 0
    for recipe_doc in stream_recipe_docs():
        recipe_data = recipe_doc.to_dict() or {}
        ensure_recipe_health_data(recipe_doc.id, recipe_data)
        updated += 1
        if limit and updated >= limit:
            break

    return updated
 

@app.route('/recipes-page')
def recipes_page():
    return render_template('recipes.html')


@app.route('/admin/upload-all-recipes', methods=['POST'])
def admin_upload_all_recipes():
    result = upload_all_recipes()
    status_code = 200 if result.get("status") == "success" else 500
    return jsonify(result), status_code


@app.route('/admin/backfill-health-data', methods=['POST'])
def admin_backfill_health_data():
    limit = request.args.get('limit', type=int)
    updated = backfill_recipe_health_data(limit=limit)
    return jsonify({
        "message": "Recipe health data backfilled successfully.",
        "updated_recipes": updated
    }), 200


@app.route('/admin/backfill-ingredient-index', methods=['POST'])
def admin_backfill_ingredient_index():
    limit = request.args.get('limit', type=int)
    updated = 0
    batch = datab.batch()
    pending_writes = 0

    for recipe_doc in stream_recipe_docs():
        recipe_data = normalize_recipe_document(recipe_doc.id, recipe_doc.to_dict() or {})
        tokens = build_recipe_ingredient_tokens(recipe_data.get("ingredients", []))
        batch.update(recipe_doc.reference, {"ingredient_tokens": tokens})
        pending_writes += 1
        updated += 1

        if pending_writes >= 400:
            pending_writes = commit_firestore_batch(batch, pending_writes)
            batch = datab.batch()

        if limit and updated >= limit:
            break

    commit_firestore_batch(batch, pending_writes)

    return jsonify({
        "message": "Ingredient search index backfilled successfully.",
        "updated_recipes": updated
    }), 200

# # API: Get filtered recipes (Firestore)
@app.route('/get-recipes', methods=['GET'])
def get_recipes():
    print("[DEBUG] /get-recipes called with params:", dict(request.args))

    try:
        state = request.args.get('state', 'All')
        cuisine = request.args.get('cuisine', 'All')
        search = request.args.get('search', '').strip().lower()
        high_rated = request.args.get('high_rated', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 20))
        last_doc_id = request.args.get('last_doc_id')

        print(f"[DEBUG] Filters  state={state}, cuisine={cuisine}, search='{search}', high_rated={high_rated}, limit={limit}, last_doc_id={last_doc_id}")

        candidate_recipes = fetch_candidate_recipes_for_listing(state=state, cuisine=cuisine)

        filtered_recipes = filter_and_sort_recipes(candidate_recipes, search=search, high_rated=high_rated, cuisine=cuisine)
        recipe_list, last_returned_id, has_more = paginate_recipe_list(
            filtered_recipes,
            limit=limit,
            last_doc_id=last_doc_id
        )

        print(
            f"[DEBUG] Query finished. Matched {len(filtered_recipes)} recipes. "
            f"Returned {len(recipe_list)} recipes. Last ID: {last_returned_id}"
        )

        return jsonify({
            'recipes': recipe_list,
            'last_doc_id': last_returned_id,
            'has_more': has_more,
            'total_returned': len(recipe_list)
        }), 200

    except FailedPrecondition as index_err:
        print("[INDEX ERROR] Missing Firestore composite index!")
        print("Create it here →", str(index_err).split('here: ')[-1] if 'here: ' in str(index_err) else str(index_err))
        return jsonify({
            'error': 'Missing Firestore index (state + name)',
            'fix': 'Go to Firebase Console → Firestore → Indexes → Add composite index: state (asc) + name (asc)',
            'details': str(index_err)
        }), 400

    except Exception as e:
        import traceback
        full_trace = traceback.format_exc()
        print("[CRITICAL] /get-recipes crashed:\n" + full_trace)
        return jsonify({
            'error': 'Server error fetching recipes',
            'message': str(e)
        }), 500


@app.route('/generate-recipe', methods=['POST'])
def generate_recipe_api():
    try:
        data = request.get_json(silent=True) or {}
        ingredients = parse_requested_ingredients(data.get("ingredients", []))

        if not ingredients:
            return jsonify({"error": "No ingredients provided"}), 400

        display_ingredients = [ingredient.title() for ingredient in ingredients]
        primary = display_ingredients[0]
        nutrition_analysis = analyze_recipe_nutrition(display_ingredients)
        cooking_time = f"{15 + min(len(display_ingredients) * 3, 18)} minutes"

        recipe = {
            "name": f"{primary} Smart Recipe",
            "ingredients": display_ingredients,
            "steps": [
                f"Wash and prep {', '.join(display_ingredients)} so everything is ready before heating the pan.",
                "Warm a non-stick pan on medium heat and add one teaspoon oil, ghee, or water for a lighter version.",
                f"Add {primary} first, then add the remaining ingredients and cook while stirring for 4 to 6 minutes.",
                "Season with salt, turmeric, cumin, chilli, or your preferred masala and mix until the ingredients are coated.",
                "Cover and cook on low heat until the ingredients turn tender, adding a splash of water only if needed.",
                "Taste, adjust seasoning, garnish with coriander or lemon, and serve warm with roti, rice, or salad."
            ],
            "cooking_time": cooking_time,
            "health_label": nutrition_analysis.get("health_label", "Moderate"),
            "health_score": nutrition_analysis.get("health_score", 0),
            "nutrition": nutrition_analysis.get("totals", {}),
            "nutrition_notes": nutrition_analysis.get("notes", []),
        }

        return jsonify(recipe)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Server error occurred"}), 500


@app.route('/generate-recipe-legacy', methods=['POST'])
def generate_recipe():
    try:
        data = request.get_json()
        ingredients = data.get("ingredients", [])

        if not ingredients:
            return jsonify({"error": "No ingredients provided"}), 400

        prompt = f"""
        You are a professional chef.

        Create a detailed recipe using: {', '.join(ingredients)}

        Include:
        Recipe Name
        Ingredients
        Step-by-step instructions (minimum 5 steps)
        Cooking time
        """

        result = generator(
            prompt,
            max_length=300,
            temperature=0.7
        )

        text = result[0]['generated_text']

        # 🔥 FORCE CLEAN OUTPUT (no JSON dependency)
        recipe = {
            "name": f"{ingredients[0].capitalize()} Recipe",
            "ingredients": ingredients,
            "steps": [],
            "cooking_time": "15-20 minutes"
        }

        lines = text.split("\n")

        steps = []
        for line in lines:
            line = line.strip()
            if len(line) > 25:
                steps.append(line)

        # fallback if model fails
        if len(steps) < 3:
            steps = [
                f"Wash and cut {', '.join(ingredients)} into small pieces",
                "Heat oil in a pan on medium flame",
                "Add ingredients and sauté for 5 minutes",
                "Add salt and spices, mix well",
                "Cook for 10 minutes and stir occasionally",
                "Serve hot"
            ]

        recipe["steps"] = steps[:6]

        return jsonify(recipe)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Server error occurred"}), 500

def normalize_ingredient_text(value):
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


INGREDIENT_MATCH_STOPWORDS = {
    "and", "or", "with", "without", "fresh", "chopped", "finely", "roughly",
    "sliced", "diced", "minced", "grated", "crushed", "small", "medium",
    "large", "cup", "cups", "tbsp", "tablespoon", "tablespoons", "tsp",
    "teaspoon", "teaspoons", "gram", "grams", "g", "kg", "ml", "liter",
    "litre", "pinch", "taste", "as", "required", "optional", "for",
    "to", "of", "in", "the", "a", "an", "pieces", "piece", "powder"
}


def ingredient_tokens(value):
    normalized = normalize_ingredient_text(value)
    base_tokens = {
        token
        for token in normalized.split()
        if token and token not in INGREDIENT_MATCH_STOPWORDS and not token.isdigit()
    }

    expanded_tokens = set(base_tokens)
    for token in base_tokens:
        if token.endswith("ies") and len(token) > 3:
            expanded_tokens.add(f"{token[:-3]}y")
        if token.endswith("es") and len(token) > 3:
            expanded_tokens.add(token[:-2])
        if token.endswith("s") and len(token) > 3:
            expanded_tokens.add(token[:-1])

    return expanded_tokens


def build_recipe_ingredient_tokens(ingredients):
    tokens = set()
    for ingredient in normalize_text_list(ingredients):
        tokens.update(ingredient_tokens(ingredient))
    return sorted(tokens)


def parse_requested_ingredients(payload):
    if payload is None:
        return []

    raw_items = []

    if isinstance(payload, list):
        raw_items = payload
    elif isinstance(payload, str):
        text = payload.strip()
        if not text:
            return []

        if any(separator in text for separator in [",", "\n", ";"]):
            raw_items = re.split(r"[,;\n]+", text)
        else:
            raw_items = text.split()
    else:
        raw_items = [payload]

    parsed = []
    seen = set()

    for item in raw_items:
        cleaned = normalize_ingredient_text(item)
        if cleaned and cleaned not in seen:
            parsed.append(cleaned)
            seen.add(cleaned)

    return parsed


def recipe_contains_ingredient(requested_ingredient, recipe_ingredient):
    requested = normalize_ingredient_text(requested_ingredient)
    available = normalize_ingredient_text(recipe_ingredient)

    if not requested or not available:
        return False

    requested_tokens = ingredient_tokens(requested)
    available_tokens = ingredient_tokens(available)

    if not requested_tokens or not available_tokens:
        return False

    if requested_tokens.issubset(available_tokens):
        return True

    if len(requested_tokens) == 1:
        requested_word = next(iter(requested_tokens))
        return requested_word in available_tokens

    overlap = requested_tokens.intersection(available_tokens)
    return len(overlap) >= max(2, len(requested_tokens) - 1)


def find_recipe_matches(recipe_ingredients, requested_ingredients):
    if isinstance(recipe_ingredients, list):
        available_ingredients = [str(item) for item in recipe_ingredients if str(item).strip()]
    elif isinstance(recipe_ingredients, str):
        available_ingredients = [segment.strip() for segment in re.split(r"[,;\n]+", recipe_ingredients) if segment.strip()]
    else:
        available_ingredients = []

    matched = []

    for requested in requested_ingredients:
        if any(recipe_contains_ingredient(requested, available) for available in available_ingredients):
            matched.append(requested)

    missing = [ingredient for ingredient in requested_ingredients if ingredient not in matched]

    return matched, missing


def required_ingredient_match_count(requested_count):
    if requested_count <= 1:
        return 1
    if requested_count <= 3:
        return 1
    return max(2, requested_count // 2)


def recommendation_candidate_docs(requested_ingredients):
    requested_tokens = sorted({
        token
        for ingredient in requested_ingredients
        for token in ingredient_tokens(ingredient)
    })

    if requested_tokens:
        try:
            indexed_docs = list(
                recipe_collection()
                .where("ingredient_tokens", "array_contains_any", requested_tokens[:10])
                .limit(160)
                .stream()
            )
            if indexed_docs:
                return indexed_docs, "ingredient_index"
        except Exception as index_error:
            print("[WARN] ingredient token index search failed:", index_error)

    return stream_recipe_docs(), "full_scan"


@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        payload = request.get_json(silent=True) or {}
        ingredients_from_json = payload.get("ingredients")
        ingredients_from_form = request.form.get("ingredients", "")
        user_query = payload.get("query") or request.form.get("query", "")
        user_demand = parse_user_food_demand(user_query)

        requested_ingredients = parse_requested_ingredients(
            ingredients_from_json if ingredients_from_json is not None else ingredients_from_form
        )

        if not requested_ingredients:
            return jsonify({
                "recipes": [],
                "requested_ingredients": [],
                "message": "Add at least one ingredient to search recipes."
            }), 200

        recipes, search_mode = recommendation_candidate_docs(requested_ingredients)
        results = []
        requested_count = len(requested_ingredients)
        minimum_required_matches = required_ingredient_match_count(requested_count)

        for recipe in recipes:
            data = normalize_recipe_document(recipe.id, recipe.to_dict() or {})
            recipe_ingredients = data.get('ingredients', [])

            matched, missing = find_recipe_matches(recipe_ingredients, requested_ingredients)

            if len(matched) < minimum_required_matches:
                continue

            preferred_health = user_demand.get("preferred_health")
            health_preference_bonus = 1 if preferred_health and data.get("health_label") == preferred_health else 0

            matched_count = len(matched)
            matching_score = round((matched_count / requested_count) * 100, 2) if requested_count else 0

            try:
                rating_value = float(data.get('ratings') or 0)
            except (TypeError, ValueError):
                rating_value = 0

            data['recipe_id'] = recipe.id
            data['matched_ingredients'] = matched
            data['missing_ingredients'] = missing
            data['matched_count'] = matched_count
            data['requested_count'] = requested_count
            data['matching_score'] = matching_score
            data['_health_preference_bonus'] = health_preference_bonus
            data['_sort_rating'] = rating_value

            results.append(data)

        results.sort(
            key=lambda recipe: (
                -recipe.get('_health_preference_bonus', 0),
                -recipe.get('matching_score', 0),
                -recipe.get('matched_count', 0),
                -recipe.get('_sort_rating', 0),
                recipe.get('name', '')
            )
        )

        for recipe in results:
            recipe.pop('_health_preference_bonus', None)
            recipe.pop('_sort_rating', None)

        return jsonify({
            "recipes": results[:24],
            "requested_ingredients": requested_ingredients,
            "total_found": len(results),
            "demand_profile": user_demand,
            "search_mode": search_mode
        }), 200

    except Exception as e:
        import traceback
        print("[ERROR] /recommend failed:\n" + traceback.format_exc())
        return jsonify({
            "recipes": [],
            "requested_ingredients": [],
            "error": "Recommendation search failed",
            "message": str(e)
        }), 500


@app.route('/parse-food-demand', methods=['POST'])
def parse_food_demand():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    return jsonify(parse_user_food_demand(text)), 200

# # API: Add to favorites (Realtime DB)
@app.route('/like-recipe', methods=['POST'])
def like_recipe():
    data = request.get_json()
    user_id = data.get('user_id')
    recipe_id = data.get('recipe_id')

    if not user_id or not recipe_id:
        return jsonify({'error': 'Missing user_id or recipe_id'}), 400

    # Store in Realtime Database - simple key = true
    database.child('users').child(user_id).child('favorites').child(recipe_id).set(True)

    return jsonify({'message': 'Added to favorites'}), 200

# # API: Remove from favorites
@app.route('/unlike-recipe', methods=['POST'])
def unlike_recipe():
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        recipe_id = data.get('recipe_id')

        if not user_id or not recipe_id:
            return jsonify({'error': 'Missing parameters'}), 400

        # Firebase Admin SDK uses delete(), not remove()
        database.child('users').child(user_id).child('favorites').child(recipe_id).delete()

        return jsonify({'message': 'Removed from favorites'}), 200

    except Exception as e:
        import traceback
        print("[ERROR] unlike_recipe failed:\n" + traceback.format_exc())
        return jsonify({
            'error': 'Failed to remove favorite',
            'message': str(e)
        }), 500

# # API: Get user's favorites (Realtime DB IDs → Firestore full data)
@app.route('/favorites/<user_id>', methods=['GET'])
def get_favorites(user_id):
    try:
        # Get the favorites node
        favs_ref = database.child('users').child(user_id).child('favorites').get()

        # Handle both possible return types safely
        if favs_ref is None:
            favorite_ids = []
        else:
            # Case 1: Modern SDK → returns dict directly
            if isinstance(favs_ref, dict):
                favorite_ids = list(favs_ref.keys())
            # Case 2: Older SDK → returns snapshot with .val()
            elif hasattr(favs_ref, 'val'):
                val = favs_ref.val()
                favorite_ids = list(val.keys()) if val else []
            else:
                favorite_ids = []

        print(f"[DEBUG] User {user_id} has {len(favorite_ids)} favorite IDs: {favorite_ids}")

        if not favorite_ids:
            return jsonify([]), 200

        # Fetch full recipes from Firestore
        fav_recipes = []
        for rid in favorite_ids:
            data = fetch_recipe_by_id(rid, ensure_health=False)
            if data:
                fav_recipes.append(data)
            else:
                print(f"[WARN] Favorite recipe ID {rid} not found in Firestore")

        return jsonify(fav_recipes), 200

    except Exception as e:
        import traceback
        print("[ERROR] get_favorites failed:\n" + traceback.format_exc())
        return jsonify({
            'error': 'Failed to load favorites',
            'message': str(e)
        }), 500

# # Recipe detail page
@app.route('/recipe-detail/<recipe_id>')
def recipe_detail(recipe_id):
    recipe = fetch_recipe_by_id(recipe_id, ensure_health=True)
    if not recipe:
        return render_template('recipe.html', recipe=None), 404
    return render_template('recipe.html', recipe=recipe)


# # Cooked
@app.route('/recipe', methods=['POST'])
def recipes_details():
    data = request.json
    user_id = data['user_id']
    recipe_id = data['recipe_id']

    _, response_payload = store_cooked_recipe(user_id, recipe_id)
    if response_payload.get("error"):
        return jsonify(response_payload), 404

    return jsonify(response_payload), 200




# # recommend REcipes

# # @app.route('/recommend', methods=['POST'])
# # def recommend():

# #     ingredients_text = request.form.get("ingredients","")

# #     processed = process_ingredients(ingredients_text)

# #     recipes = recommend_recipes(processed)

# #     return jsonify(recipes),200

# def recommend_recipes(processed_ingredients):

#     recipes = datab.collection('recipes').stream()

#     results = []

#     for recipe in recipes:

#         data = recipe.to_dict()

#         recipe_ingredients = [i.lower() for i in data.get('ingredients',[])]

#         matched = list(set(processed_ingredients) & set(recipe_ingredients))

#         total = len(recipe_ingredients)

#         if total == 0:
#             continue

#         score = (len(matched) / total) * 100

#         data['matching_score'] = score
#         data['recipe_id'] = recipe.id

#         results.append(data)

#     results = sorted(results, key=lambda x: x['matching_score'], reverse=True)

#     return results[:10]


@app.route('/health-report/<user_id>')
def health_report(user_id):
    user_ref, user_profile = fetch_user_profile(user_id)
    cook_events_snapshot = user_ref.child("cook_events").get() or {}
    cook_events = list(cook_events_snapshot.values()) if isinstance(cook_events_snapshot, dict) else []
    summary = build_user_health_summary(user_profile, cook_events)

    score = summary["health_score"]
    if score < 0:
        status = "Poor"
    elif score < 10:
        status = "Moderate"
    else:
        status = "Healthy Lifestyle"

    return jsonify({
        "healthy": summary["healthy"],
        "moderate": summary["moderate"],
        "fastfood": summary["unhealthy"],
        "health_score": score,
        "status": status,
        "warning": summary["warning"],
        "last_notification": user_profile.get("last_notification", ""),
        "healthy_recommendations": get_healthy_recommendations(limit=5),
        "recent_meals": summary["recent_events"]
    })


@app.route('/dashboard-report/<user_id>')
def dashboard_report(user_id):
    return jsonify(build_dashboard_summary(user_id)), 200
# # Recommend endpoint (NLP, Image, ML)
# @app.route('/recommend', methods=['POST'])
# def recommend():
#     data = request.form
#     user_id = data.get('user_id')
#     input_text = data.get('ingredients', '')
#     image = request.files.get('image')

#     processed = process_ingredients(input_text)

#     if image:
#         image_bytes = image.read()
#         detected = detect_ingredients_from_image(image_bytes)
#         processed.extend(detected)

#     recs = recommend_recipes(processed)

#     if user_id:
#         personalized = personalized_recommendations(user_id)
#         recs.extend(personalized)

#     return jsonify(recs), 200

# Cooked endpoint (Health tracking, History)

@app.route('/cooked', methods=['POST'])
def cooked():

    data = request.json
    user_id = data['user_id']
    recipe_id = data['recipe_id']
    _, response_payload = store_cooked_recipe(user_id, recipe_id)
    if response_payload.get("error"):
        return jsonify(response_payload), 404

    return jsonify(response_payload), 200

# # Get History
@app.route('/history/<user_id>', methods=['GET'])
def get_history(user_id):
    history = datab.collection('history').where('user_id', '==', user_id).stream()
    hist_list = []
    for hist in history:
        data = hist.to_dict()
        recipe = fetch_recipe_by_id(data['recipe_id'], ensure_health=False)
        data['recipe'] = recipe
        hist_list.append(data)
    return jsonify(hist_list), 200

if __name__ == '__main__':
    # if '--upload-recipes' in sys.argv:
    #     print("Uploading all recipes from CSV to Firestore...")
    #     print(upload_all_recipes())
    #     sys.exit(0)
    # upload_all_recipes()
    print("Starting Flask server...")
    # app.run(debug=True, port=5500)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
