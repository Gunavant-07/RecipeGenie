import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet")

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def process_ingredients(input_text):
    text = input_text.lower()
    tokens = text.split()
    processed = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    return processed


def parse_user_food_demand(input_text):
    processed_tokens = process_ingredients(input_text or "")
    token_set = set(processed_tokens)

    preferred_health = None
    if {"healthy", "light", "diet", "nutritious"} & token_set:
        preferred_health = "Healthy"
    elif {"moderate", "balanced"} & token_set:
        preferred_health = "Moderate"
    elif {"fast", "fried", "junk", "unhealthy"} & token_set:
        preferred_health = "Unhealthy"

    priorities = {
        "high_protein": bool({"protein", "gym", "muscle"} & token_set),
        "low_sugar": bool({"low", "sugar", "diabetes"} & token_set),
        "low_oil": bool({"low", "oil"} & token_set),
        "weight_loss": bool({"weight", "loss", "diet"} & token_set),
    }

    return {
        "tokens": processed_tokens,
        "preferred_health": preferred_health,
        "priorities": priorities,
    }
