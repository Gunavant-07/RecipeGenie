from flask import Flask, request, jsonify, render_template ,redirect, url_for
from flask_cors import CORS
from firebase_admin import auth
import pandas as pd
from ml_models import train_health_classifier, classify_recipe_health, recommend_recipes, personalized_recommendations
from nlp_utils import process_ingredients
import datetime
import random
from firebase_config import database,datab
from google.api_core.exceptions import FailedPrecondition
import re
import urllib.parse
from image_detection import detect_ingredients_from_image

app = Flask(__name__)
CORS(app)  

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

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

#user authentication on register
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
            "moderate_count": 0,
            "health_score": 0
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
   

#....................................................................................
CSV_FILE = 'Recipe_Data/recipes.csv'                  # your file name
COLLECTION_NAME = 'recipes'                  # Firestore collection
CHECK_FOR_DUPLICATES = True                  # prevent re-uploading same recipe name

BASE_IMAGE_URL = "https://recipesimages.edgeone.app/"
FALLBACK_IMAGE = "https://recipesimages.edgeone.app/default.jpg"
# ==============================================

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
#....................................................................................   

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
 
@app.route('/detect-ingredients', methods=['POST'])
def detect_ingredients():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image = request.files['image']
    image_bytes = image.read()

    ingredients = detect_ingredients_from_image(image_bytes)

    return jsonify({
        'ingredients': ingredients
    }), 200
    
@app.route('/recipes-page')
def recipes_page():
    return render_template('recipes.html')

# API: Get filtered recipes (Firestore)
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
            data = doc.to_dict() or {}
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

            data['recipe_id'] = doc.id
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
        
# API: Add to favorites (Realtime DB)
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

# API: Remove from favorites
@app.route('/unlike-recipe', methods=['POST'])
def unlike_recipe():
    data = request.get_json()
    user_id = data.get('user_id')
    recipe_id = data.get('recipe_id')

    if not user_id or not recipe_id:
        return jsonify({'error': 'Missing parameters'}), 400

    database.child('users').child(user_id).child('favorites').child(recipe_id).remove()

    return jsonify({'message': 'Removed from favorites'}), 200

# API: Get user's favorites (Realtime DB IDs → Firestore full data)
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
                data = recipe_snap.to_dict()
                data['recipe_id'] = rid
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

# Recipe detail page
@app.route('/recipe-detail/<recipe_id>')
def recipe_detail(recipe_id):
    recipe = datab.collection('recipes').document(recipe_id).get().to_dict()
    if not recipe:
        return "Recipe not found", 404
    return render_template('recipe.html', recipe=recipe)


# Cooked
@app.route('/recipe', methods=['POST'])
def recipes_details():
    data = request.json
    user_id = data['user_id']
    recipe_id = data['recipe_id']
    
    recipe = datab.collection('recipes').document(recipe_id).get().to_dict()
    category = recipe['category']
    
    user_ref = datab.collection('users').document(user_id)
    user = user_ref.get().to_dict()
    
    if category == 'healthy':
        user['healthy_count'] += 1
    elif category == 'fast_food':
        user['fastfood_count'] += 1
    else:
        user['moderate_count'] += 1
    
    # Update health score
    user['health_score'] = (user['healthy_count'] * 2) - (user['fastfood_count'] * 2)
    user_ref.update(user)
    
    # Add to history
    datab.collection('history').add({
        'user_id': user_id,
        'recipe_id': recipe_id,
        'date': datetime.datetime.now()
    })
    
    # If score low, suggest healthy
    suggestions = []
    if user['health_score'] < 10:  # Threshold
        suggestions = recommend_recipes(['healthy ingredients'])  # Mock healthy query
    
    return jsonify({'message': 'Updated', 'suggestions': suggestions}), 200

## image detection 

@app.route('/detect-ingredients', methods=['POST'])
def detect_ingredients():

    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    image_bytes = file.read()

    detected = detect_ingredients_from_image(image_bytes)

    return jsonify({
        "ingredients": detected
    }), 200

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

    recipe_doc = datab.collection('recipes').document(recipe_id).get()
    if not recipe_doc.exists:
        return jsonify({'error': 'Recipe not found'}), 404

    recipe = recipe_doc.to_dict()
    category = recipe['category']

    user_ref = datab.collection('users').document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return jsonify({'error': 'User not found'}), 404

    user = user_doc.to_dict()

    if category == 'Healthy':
        user['healthy_count'] += 1
    elif category == 'Fast Food':
        user['fastfood_count'] += 1
    else:
        user['moderate_count'] += 1

    user['health_score'] = (user['healthy_count'] * 2) - (user['fastfood_count'] * 2)
    user_ref.update(user)

    datab.collection('history').add({
        'user_id': user_id,
        'recipe_id': recipe_id,
        'date': datetime.datetime.now().isoformat()
    })

    suggestions = []
    if user['health_score'] < 10:
        suggestions = recommend_recipes(['healthy', 'gujarat'])  # Suggest healthy

    return jsonify({'message': 'Updated', 'suggestions': suggestions}), 200

# Get History
@app.route('/history/<user_id>', methods=['GET'])
def get_history(user_id):
    history = datab.collection('history').where('user_id', '==', user_id).stream()
    hist_list = []
    for hist in history:
        data = hist.to_dict()
        recipe = datab.collection('recipes').document(data['recipe_id']).get().to_dict()
        data['recipe'] = recipe
        hist_list.append(data)
    return jsonify(hist_list), 200

if __name__ == '__main__':
    # upload_gujarati_recipes()
    app.run(debug=True, port=5000)
    