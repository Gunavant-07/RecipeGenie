
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
import urllib.parse
import numpy as np
import cv2
import ast





app = Flask(__name__)
CORS(app)  

# UPLOAD_FOLDER = "static/uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MODEL_PATH = r"E:\RecipeGenie\RecipeGenie\runs\detect\train\weights\best.pt"

print("Loading YOLO model...")
model = YOLO(MODEL_PATH)
print("Model loaded successfully!")

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

    detected = detect_ingredients(image_bytes)

    return jsonify({
        "ingredients": detected
    })


def detect_ingredients(image_bytes):

    # Convert bytes → image
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return []

    # Run YOLO
    results = model(img)

    detected = []

    for r in results:
        for box in r.boxes:

            conf = float(box.conf[0])
            cls_id = int(box.cls[0])

            if conf > 0.4:
                label = model.names[cls_id]
                detected.append(label)

    return list(set(detected))  # remove duplicates




    
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/history-page')
def history_page():
    return render_template('history.html')

@app.route('/health')
def health_page():
    return render_template('health.html')

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
CSV_FILE = 'E:/4th Semester/final project/Food recomandation web app/23-01-26/Recipe_Data/recipes.csv'   # your file name

COLLECTION_NAME = 'recipes'                  # Firestore collection
CHECK_FOR_DUPLICATES = True                  # prevent re-uploading same recipe name

BASE_IMAGE_URL = "https://recipesimages.edgeone.app/"
FALLBACK_IMAGE = "https://recipesimages.edgeone.app/default.jpg"
# # ==============================================

def upload_gujarati_recipes():
    print("=== STARTING FIRESTORE UPLOAD SCRIPT ===")
    print(f"Reading Excel file: {CSV_FILE}")

    try:
        # Read Excel
        df = pd.read_csv(CSV_FILE)
        print(f"Total rows in Excel: {len(df)}")

        # Filter only Gujarati recipes
        df_guj = df[df['Cuisine_name'].str.contains('Gujarati', case=False, na=False)]
        print(f"Found {len(df_guj)} Gujarati recipes after filtering.")

        if df_guj.empty:
            print("ERROR: No Gujarati recipes found. Check 'Cuisine_name' column.")
            return

        uploaded_count = 0
        skipped_count = 0

        for idx, row in df_guj.iterrows():
            original_name = row.get('name_of_Dish', 'Unknown Recipe')
            
            recipe_name = clean_recipe_name(original_name)
            image_link = make_image_url(recipe_name)
            
            # print(f"\nProcessing: {recipe_name}")
            # print(f"\nProcessing1111: {uploaded_count}")

            # Optional: skip if already exists (safety)
            if CHECK_FOR_DUPLICATES:
                existing = datab.collection(COLLECTION_NAME)\
                               .where('name', '==', recipe_name)\
                               .limit(1)\
                               .get()
                if existing:
                    print(f"  → Already exists in Firestore. Skipping.")
                    skipped_count += 1
                    continue

            # Infer ML features (same logic as before)
            ing_str = ' '.join(row.get('Ingredients_of_Dish', [])).lower()
            instructions_str = ' '.join(row.get('Recipe_Instructions', [])).lower()

            oil_amount = 'high' if ing_str.count('oil') > 1 else 'medium' if 'oil' in ing_str else 'low'
            calories = random.randint(150, 600) if pd.isna(row.get('calories')) else row['calories']
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
                print(f"  → Classification failed: {e}")
                category = 'Moderate'  # fallback

            # Prepare data for Firestore
            data = {
                'recipe_id': '',  # will be auto-generated
                'state': 'Gujarat',
                'name': recipe_name,
                'image_url': image_link,
                'ingredients': row.get('Ingredients_of_Dish', []),
                'steps': row.get('Recipe_Instructions', []),
                'category': category,
                'nutrition_type': row.get('Diet_Type', 'Vegetarian'),
                'diet_type': row.get('Diet_Type', 'Vegetarian'),
                'course': row.get('Course_name', ''),
                'description': row.get('Discription_of_Dish', ''),
                'ratings': row.get('Ratings_of_Dish', 4.0),
                'prep_time': row.get('Preparation_time', ''),
                'cook_time': row.get('Cooking_time', ''),
                'total_time': row.get('Total_time', ''),
                'servings': row.get('Makes', ''),
                'uploaded_at': pd.Timestamp.now().isoformat()
            }

            data = enrich_recipe_with_health_data(data)

            # Upload
            doc_ref = datab.collection(COLLECTION_NAME).document()
            data['recipe_id'] = doc_ref.id  # set the auto ID

            doc_ref.set(data)
            # print(f"  → Uploaded successfully (ID: {doc_ref.id})")
            uploaded_count += 1

        # print("\n=== UPLOAD SUMMARY ===")
        # print(f"Total Gujarati recipes processed: {len(df_guj)}")
        # print(f"Successfully uploaded: {uploaded_count}")
        # print(f"Skipped (already exists): {skipped_count}")
        print("Done.")

    except FileNotFoundError:
        print(f"ERROR: File not found → {CSV_FILE}")
        print("Make sure the Excel file is in the same folder as this script.")
    except Exception as e:
        print("Unexpected error during upload:")
        print(str(e))
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
    if not isinstance(recipe_name, str) or not recipe_name.strip():
        return ""

    name = recipe_name.strip()

    # ---- CLEANING RULES (keeps meaning intact) ----
    name = name.replace("/", " ")      # remove slashes
    name = name.replace("\\", " ")     # remove backslashes
    name = name.replace("_", " ")      # remove underscores
    name = re.sub(r"\s+", " ", name)   # collapse multiple spaces

    # KEEP DASH "-" EXACTLY AS IS (your image also has it)
    # Now safely encode spaces -> %20 etc.
    print(f"image names ${name}")
    safe_name = urllib.parse.quote(name)
    print(f"new11111 image names ${safe_name}")

    return f"{BASE_IMAGE_URL}{safe_name}.jpg"


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
    normalized["ingredients"] = normalize_text_list(normalized.get("ingredients", []))
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
    datab.collection("recipes").document(recipe_id).update({
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

    healthy_query = datab.collection("recipes").where("health_label", "==", "Healthy").limit(limit * 3).stream()

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
        fallback_docs = datab.collection("recipes").stream()
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
    recipe_snapshot = datab.collection("recipes").document(recipe_id).get()
    if not recipe_snapshot.exists:
        return None, {"error": "Recipe not found"}

    recipe = ensure_recipe_health_data(recipe_id, recipe_snapshot.to_dict() or {})
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
    for recipe_doc in datab.collection("recipes").stream():
        recipe_data = recipe_doc.to_dict() or {}
        ensure_recipe_health_data(recipe_doc.id, recipe_data)
        updated += 1
        if limit and updated >= limit:
            break

    return updated
 

@app.route('/recipes-page')
def recipes_page():
    return render_template('recipes.html')


@app.route('/admin/backfill-health-data', methods=['POST'])
def admin_backfill_health_data():
    limit = request.args.get('limit', type=int)
    updated = backfill_recipe_health_data(limit=limit)
    return jsonify({
        "message": "Recipe health data backfilled successfully.",
        "updated_recipes": updated
    }), 200

# # API: Get filtered recipes (Firestore)
@app.route('/get-recipes', methods=['GET'])
def get_recipes():
    print("[DEBUG] /get-recipes called with params:", dict(request.args))

    try:
        state = request.args.get('state', 'Gujarat')
        search = request.args.get('search', '').strip().lower()
        high_rated = request.args.get('high_rated', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 20))
        last_doc_id = request.args.get('last_doc_id')

        print(f"[DEBUG] Filters  state={state}, search='{search}', high_rated={high_rated}, limit={limit}, last_doc_id={last_doc_id}")

        query = datab.collection('recipes')

        if state and state != 'All':
            print(f"[DEBUG] Adding where state == {state}")
            query = query.where('state', '==', state)

        print("[DEBUG] Adding order_by('name')")
        query = query.order_by('name')

        if last_doc_id:
            print(f"[DEBUG] Starting after document: {last_doc_id}")
            last_doc_ref = datab.collection('recipes').document(last_doc_id)
            last_doc = last_doc_ref.get()
            if last_doc.exists:
                query = query.start_after(last_doc)
            else:
                print(f"[WARN] last_doc_id {last_doc_id} does not exist - starting from beginning")

        print(f"[DEBUG] Applying limit({limit})")
        query = query.limit(limit)

        print("[DEBUG] Executing query.stream()...")
        docs = query.stream()

        recipe_list = []
        last_returned_id = None
        count = 0

        for doc in docs:
            count += 1
            data = normalize_recipe_document(doc.id, doc.to_dict() or {})
            print(f"[DEBUG] Processing doc {count}: ID={doc.id}")

            name_lower = str(data.get('name', '')).lower()
            if search and search not in name_lower:
                continue

            if high_rated:
                try:
                    rating = float(data.get('ratings') or 0)
                    if rating < 4.5:
                        continue
                except (ValueError, TypeError):
                    print(f"[WARN] Invalid ratings in doc {doc.id} - skipping")
                    continue
            recipe_list.append(data)
            last_returned_id = doc.id

        print(f"[DEBUG] Query finished. Returned {len(recipe_list)} recipes. Last ID: {last_returned_id}")

        return jsonify({
            'recipes': recipe_list,
            'last_doc_id': last_returned_id,
            'has_more': len(recipe_list) == limit and last_returned_id is not None,
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


def normalize_ingredient_text(value):
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


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

    if requested == available:
        return True

    if requested in available or available in requested:
        return True

    requested_tokens = set(requested.split())
    available_tokens = set(available.split())

    if requested_tokens and requested_tokens.issubset(available_tokens):
        return True

    if len(requested_tokens) == 1 and requested_tokens.intersection(available_tokens):
        return True

    return False


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


@app.route('/recommend', methods=['POST'])
def recommend():
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

    recipes = datab.collection('recipes').stream()
    results = []

    for recipe in recipes:
        data = ensure_recipe_health_data(recipe.id, recipe.to_dict() or {})
        recipe_ingredients = data.get('ingredients', [])

        matched, missing = find_recipe_matches(recipe_ingredients, requested_ingredients)

        if not matched:
            continue

        preferred_health = user_demand.get("preferred_health")
        health_preference_bonus = 1 if preferred_health and data.get("health_label") == preferred_health else 0

        requested_count = len(requested_ingredients)
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
            -recipe.get('matched_count', 0),
            -recipe.get('matching_score', 0),
            -recipe.get('_sort_rating', 0),
            recipe.get('name', '')
        )
    )

    for recipe in results:
        recipe.pop('_health_preference_bonus', None)
        recipe.pop('_sort_rating', None)

    return jsonify({
        "recipes": results[:20],
        "requested_ingredients": requested_ingredients,
        "total_found": len(results),
        "demand_profile": user_demand
    })


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
            recipe_snap = datab.collection('recipes').document(rid).get()
            if recipe_snap.exists:
                data = normalize_recipe_document(rid, recipe_snap.to_dict() or {})
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
    recipe_snapshot = datab.collection('recipes').document(recipe_id).get()
    recipe = ensure_recipe_health_data(recipe_id, recipe_snapshot.to_dict() or {})
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
        recipe_snap = datab.collection('recipes').document(data['recipe_id']).get()
        recipe = normalize_recipe_document(data['recipe_id'], recipe_snap.to_dict() or {})
        data['recipe'] = recipe
        hist_list.append(data)
    return jsonify(hist_list), 200

if __name__ == '__main__':
    # upload_gujarati_recipes()
    print("Starting Flask server...")
    app.run(debug=True, port=5000)
    
