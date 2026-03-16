# ml_models.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
import numpy as np
import joblib
import random
from firebase_config import datab  # only used in recommend functions

def train_health_classifier():
    print("=== Starting model training ===")
    
    # Read YOUR Excel file (not csv)
    try:
        df = pd.read_csv('E:/4th Semester/final project/Food recomandation web app/23-01-26/Recipe_Data/recipes.csv')
    except FileNotFoundError:
        print("ERROR: recipes.xlsx not found in the same folder!")
        return
    
    # Optional: filter only Gujarati if you want training only on them
    # df = df[df['Cuisine_name'].str.contains('Gujarati', case=False, na=False)]
    
    print(f"Loaded {len(df)} recipes for training.")
    
    # Infer missing columns needed for training
    df['oil_amount'] = df.apply(
        lambda row: 'high' if 'oil' in str(row.get('Ingredients_of_Dish', '')).lower() and 
                              str(row.get('Ingredients_of_Dish', '')).lower().count('oil') > 1 
                    else 'medium' if 'oil' in str(row.get('Ingredients_of_Dish', '')).lower() 
                    else 'low', axis=1
    )
    
    df['calories'] = df.apply(
        lambda row: random.randint(150, 600) if pd.isna(row.get('calories')) else row['calories'], axis=1
    )
    
    df['fried'] = df.apply(
        lambda row: 'yes' if 'fry' in ' '.join(str(row.get('Recipe_Instructions', ''))).lower() else 'no', axis=1
    )
    
    df['sugar'] = df.apply(
        lambda row: 'high' if 'sugar' in str(row.get('Ingredients_of_Dish', '')).lower() and 
                              str(row.get('Ingredients_of_Dish', '')).lower().count('sugar') > 1 
                    else 'medium' if 'sugar' in str(row.get('Ingredients_of_Dish', '')).lower() 
                    else 'low', axis=1
    )
    
    # For training we need a 'label' column (ground truth)
    # If you don't have it → we can use simple rule-based labels for now
    def assign_label(row):
        if row['fried'] == 'yes' or row['oil_amount'] == 'high':
            return 'Fast Food'
        elif row['oil_amount'] == 'low' and row['sugar'] == 'low':
            return 'Healthy'
        else:
            return 'Moderate'
    
    df['label'] = df.apply(assign_label, axis=1)
    
    # Now encode
    le_oil = LabelEncoder()
    le_fried = LabelEncoder()
    le_sugar = LabelEncoder()
    le_label = LabelEncoder()
    
    df['oil_amount_enc'] = le_oil.fit_transform(df['oil_amount'])
    df['fried_enc'] = le_fried.fit_transform(df['fried'])
    df['sugar_enc'] = le_sugar.fit_transform(df['sugar'])
    df['label_enc'] = le_label.fit_transform(df['label'])
    
    X = df[['oil_amount_enc', 'calories', 'fried_enc', 'sugar_enc']]
    y = df['label_enc']
    
    if len(X) < 2:
        print("ERROR: Not enough data to train model (need at least 2 rows)")
        return
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Save model and encoders
    joblib.dump(model, 'trained_model.joblib')
    joblib.dump(le_label, 'label_encoder.joblib')
    joblib.dump(le_oil, 'le_oil.joblib')      # optional - save all for consistency
    joblib.dump(le_fried, 'le_fried.joblib')
    joblib.dump(le_sugar, 'le_sugar.joblib')
    
    print("Model trained and saved successfully!")
    print(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")
    print("You can now safely run upload_recipes_to_firestore() in app.py")

# Other functions remain the same (classify_recipe_health, recommend_recipes, personalized_recommendations)
# ...
def classify_recipe_health(features):

    model = joblib.load('trained_model.joblib')
    le_label = joblib.load('label_encoder.joblib')

    oil_map = {"low":0,"medium":1,"high":2}
    fried_map = {"no":0,"yes":1}
    sugar_map = {"low":0,"medium":1,"high":2}

    df_input = pd.DataFrame([{
        "oil_amount_enc": oil_map[features["oil_amount"]],
        "calories": features["calories"],
        "fried_enc": fried_map[features["fried"]],
        "sugar_enc": sugar_map[features["sugar"]]
    }])

    pred = model.predict(df_input)[0]

    return le_label.inverse_transform([pred])[0]

def recommend_recipes(processed_ingredients):
    recipes = datab.collection('recipes').stream()
    recipe_data = []
    recipe_docs = []
    for recipe in recipes:
        data = recipe.to_dict()
        recipe_data.append(' '.join(data['ingredients']))
        recipe_docs.append(data)

    if not recipe_data:
        return []

    vectorizer = TfidfVectorizer()
    recipe_vectors = vectorizer.fit_transform(recipe_data)
    user_vector = vectorizer.transform([' '.join(processed_ingredients)])

    similarities = cosine_similarity(user_vector, recipe_vectors).flatten()
    top_indices = similarities.argsort()[-5:][::-1]

    recommendations = []
    for idx in top_indices:
        recipe_doc = recipe_docs[idx]
        matched = len(set(processed_ingredients) & set(recipe_doc['ingredients']))
        total = len(recipe_doc['ingredients'])
        matching_score = (matched / total) * 100 if total > 0 else 0

        status = 'recommend' if matching_score >= 70 else 'show_missing' if 40 <= matching_score < 70 else 'suggest_alternative'
        if status == 'show_missing':
            recipe_doc['missing'] = list(set(recipe_doc['ingredients']) - set(processed_ingredients))

        recipe_doc['matching_score'] = matching_score
        recipe_doc['status'] = status
        recommendations.append(recipe_doc)

    return recommendations

def personalized_recommendations(user_id):
    history = datab.collection('history').where('user_id', '==', user_id).stream()
    healthy, moderate, fast = 0, 0, 0
    for hist in history:
        recipe = datab.collection('recipes').document(hist.to_dict()['recipe_id']).get().to_dict()
        if recipe['category'] == 'Healthy':
            healthy += 1
        elif recipe['category'] == 'Moderate':
            moderate += 1
        else:
            fast += 1

    user_vec = np.array([[healthy, moderate, fast]])

    recipes_stream = datab.collection('recipes').stream()
    all_recipes = []
    recipe_ids = []
    for rec in recipes_stream:
        data = rec.to_dict()
        vec = [1 if data['category'] == 'Healthy' else 0,
               1 if data['category'] == 'Moderate' else 0,
               1 if data['category'] == 'Fast Food' else 0]
        all_recipes.append(vec)
        recipe_ids.append(rec.id)

    if not all_recipes:
        return []

    nn = NearestNeighbors(n_neighbors=5, metric='cosine')
    nn.fit(all_recipes)
    _, indices = nn.kneighbors(user_vec)

    recs = []
    for idx in indices[0]:
        rec_doc = datab.collection('recipes').document(recipe_ids[idx]).get().to_dict()
        recs.append(rec_doc)

    return recs

if __name__ == '__main__':
    train_health_classifier()