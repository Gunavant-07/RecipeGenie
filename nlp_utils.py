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