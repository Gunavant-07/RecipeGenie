import tensorflow as tf
import numpy as np
from PIL import Image

# load trained model
model = tf.keras.models.load_model("model/ingredient_model.h5",
    compile=False)

# ingredient classes (must match training order)
class_names = [
    "almonds",
    "Amla (Gooseberry)",
    "apple",
    "Apricot",
    "Avocado",
    "baking_powder",
    "banana",
    "bay_leaf",
    "beans",
    "beetroot",
    "Black Beans",
    "Black Pepper",
    "Bottle Gourd",
    "Brinjal (Eggplant)",
    "broccoli",
    "Brown Sugar",
    "butter",
    "cabbage",
    "capsicum",
    "cardamom",
    "carrot",
    "cashew",
    "cauliflower",
    "chicken",
    "chili powder",
    "chilli",
    "cinnamon",
    "Cinnamon Powder",
    "cloves",
    "coconut",
    "Coriander Leaves",
    "Coriender seeds",
    "corn",
    "Corn Flour",
    "cream",
    "cucumber",
    "cumin",
    "Cumin Seeds",
    "Dates",
    "egg",
    "Fennel Seeds",
    "Garam Masala",
    "garlic",
    "ginger",
    "Grapes",
    "Green Chilli",
    "Honey",
    "jackfruit",
    "Kiwi",
    "lemon",
    "Lettuce",
    "Nutmeg",
    "oil",
    "onion",
    "orange",
    "Papaya",
    "Paprika",
    "peanuts",
    "peas",
    "pineapple",
    "Plum",
    "pomegranate",
    "potato",
    "pumpkin",
    "radish",
    "raisins",
    "Saffron",
    "salt",
    "Semolina (Sooji)",
    "Sesame Seeds",
    "spinach",
    "Star Anise",
    "strawberry",
    "sugar",
    "Sweet Corn",
    "Sweet Potato",
    "tamarind",
    "tomato",
    "turmeric",
    "Turnip",
    "Walnuts",
    "Watermelon",
    "wheat_flour",
    "zucchini",
]

detect_ingredients("static/uploads/6.jpg")

def detect_ingredients(image_file):

    # read image
    img = Image.open(image_file).convert("RGB")

    # resize to model input
    img = img.resize((224, 224))

    # convert to numpy
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    # predict
    predictions = model.predict(img_array)

    # get highest prediction
    predicted_index = np.argmax(predictions)
    confidence = float(np.max(predictions))

    ingredient = class_names[predicted_index]

    return [{
        "ingredient": ingredient,
        "confidence": confidence
    }]