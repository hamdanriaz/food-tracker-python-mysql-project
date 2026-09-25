import csv
import numpy as np
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense

category_map = {
    "fried": ["samosa", "puffs", "roll", "fries", "nuggets"],
    "sugary_drinks": ["soda", "cola", "sweet tea", "energy drink"],
    "sweet_desserts": ["ice cream", "cake", "chocolate", "donut"],
    "salty_snacks": ["chips", "crisps", "pretzel"],
    "leafy_greens": ["spinach", "kale", "lettuce", "cabbage", "broccoli"],
    "lean_protein": ["chicken", "turkey", "fish", "tofu", "egg"],
    "complex_carbs": ["brown rice", "quinoa", "sweet potato", "oats"],
    "fruits": ["apple", "banana", "grape", "orange", "watermelon"],
    "junk_food": ["burger", "mac", "pizza", "hotdog", "shawarma",],
    "noodles": ["ramen", "noodle", "maggi", "spaghetti"],
    "beverage": ["juice", "coffee", "milk", "smoothie"],
    "tea": ["tea", "green tea"]
}

advice_map = {
    "fried": "Fried foods are calorie-dense and often low in nutrients. Try grilling or baking instead.",
    "sugary_drinks": "Sugary drinks spike insulin and offer no nutrition. Water or unsweetened drinks are better.",
    "sweet_desserts": "Ice cream and sweets are fine occasionally, but portion control is key.",
    "salty_snacks": "Salty snacks can cause water retention and add empty calories. Try nuts or roasted chickpeas.",
    "leafy_greens": "Leafy greens are nutrient-dense and low in calories. Excellent choice!",
    "lean_protein": "Lean proteins help build muscle and keep you full. Keep them as a meal staple.",
    "complex_carbs": "Complex carbs give long-lasting energy. Whole grains > white bread.",
    "fruits": "Fruits are sweet but natural. Pair with protein to avoid sugar crashes.",
    "junk_food": "Fast foods are tasty but high in saturated fat. Limit frequency.",
    "noodles": "Instant noodles are high in sodium and low in fiber. Balance them with veggies.",
    "beverage": "Sweet beverages add up fast. Water is always a better bet.",
    "tea": "Unsweetened tea is perfect—hydrating and low in calories."
}

def classify_food(name):
    name = name.lower()
    for category, keywords in category_map.items():
        if any(keyword in name for keyword in keywords):
            return category
    return None

training_meals = []
training_advice = []

try:
    with open("foods.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            food = row["Meal"]
            calories = row["Calories"]
            category = classify_food(food)

            if category:
                training_meal = f"{calories} calories from {food.lower()}"
                advice = advice_map[category]
                training_meals.append(training_meal)
                training_advice.append(advice)
except FileNotFoundError:
    print("foods.csv not found! Make sure it's in the same directory.")
    exit()

unique_data = list(dict.fromkeys(zip(training_meals, training_advice)))
training_meals, training_advice = zip(*unique_data)

tokenizer = Tokenizer()
tokenizer.fit_on_texts(training_meals + training_advice)
vocab_size = len(tokenizer.word_index) + 1

input_seq = tokenizer.texts_to_sequences(training_meals)
output_seq = tokenizer.texts_to_sequences(training_advice)

max_len = max(max(len(seq) for seq in input_seq), max(len(seq) for seq in output_seq))

X = pad_sequences(input_seq, maxlen=max_len, padding='post')
y = pad_sequences(output_seq, maxlen=max_len, padding='post')

y_encoded = np.zeros((len(y), max_len, vocab_size), dtype=np.float32)
for i, seq in enumerate(y):
    for t, word_id in enumerate(seq):
        if word_id > 0:
            y_encoded[i, t, word_id] = 1.0

model = Sequential([
    Embedding(input_dim=vocab_size, output_dim=64, input_length=max_len),
    LSTM(128, return_sequences=True),
    Dense(vocab_size, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy')
model.fit(X, y_encoded, epochs=50, verbose=1)

def get_tensorflow_diet_advice(meals):
    categories = set()
    for meal in meals:
        cat = classify_food(meal[0])
        if cat:
            categories.add(cat)

    if not categories:
        return "No specific advice found for your meals."

    return "\n\n".join([f"• {advice_map[cat]}" for cat in categories])

