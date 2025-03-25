import streamlit as st
import google.generativeai as genai
import pandas as pd
import random
import ast
import os
import csv

# ✅ Configure API Key securely
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ API Key is missing. Go to Streamlit Cloud → Settings → Secrets and add your API key.")
    st.stop()

# ✅ AI Response Generator
def get_ai_response(prompt, fallback_message="⚠️ AI response unavailable. Please try again later."):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt)
        return response.text.strip() if hasattr(response, "text") and response.text.strip() else fallback_message
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}\n{fallback_message}"

# ✅ Streamlit UI Configuration

# Data Setup (same as before)
data = {
    "Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] * 4,
    "Dish Name": [
        "Grilled Chicken Salad", "Vegan Buddha Bowl", "Gluten-Free Pasta",
        "Beetroot Soup", "High-Protein Stir Fry", "Pumpkin Pie", "Quinoa Salad",
        "Tofu Tacos", "Herb-Roasted Chicken", "Vegetable Soup",
        "Spinach Lasagna", "Lentil Curry", "Mango Smoothie Bowl",
        "Stuffed Bell Peppers", "Cauliflower Rice Bowl", "Chickpea Stew",
        "Zucchini Noodles", "Avocado Toast", "Black Bean Burger",
        "Sweet Potato Fries", "Berry Parfait", "Falafel Wrap", "Tomato Basil Soup",
        "Quinoa Porridge", "Eggplant Parmesan", "Carrot Ginger Soup",
        "Spinach and Feta Pie", "Kale Salad", "Pumpkin Risotto", "Veggie Stir-Fry",
        "Butternut Squash Soup"
    ],
    "Category": [
        "Main", "Main", "Main", "Side", "Main", "Dessert", "Side",
        "Main", "Main", "Side", "Main", "Main", "Dessert",
        "Main", "Main", "Main", "Main", "Side", "Main",
        "Side", "Dessert", "Main", "Side", "Main", "Main",
        "Side", "Main", "Side", "Main", "Main", "Side"
    ],
    "Ingredients": [
        "chicken, lettuce, tomatoes", "quinoa, chickpeas, vegetables",
        "gluten-free pasta, marinara sauce", "beetroot, herbs",
        "chicken, broccoli, peppers", "pumpkin, spices",
        "quinoa, spinach", "tofu, tortillas, salsa",
        "chicken, herbs, tomatoes", "vegetables, broth",
        "spinach, pasta, cheese", "lentils, curry spices",
        "mango, yogurt, granola", "bell peppers, rice",
        "cauliflower, herbs", "chickpeas, spices",
        "zucchini, garlic", "avocado, bread",
        "black beans, buns", "sweet potatoes, oil",
        "berries, yogurt", "falafel, wrap", "tomatoes, basil",
        "quinoa, milk", "eggplant, cheese",
        "carrots, ginger", "spinach, feta",
        "kale, lemon", "pumpkin, rice",
        "vegetables, soy sauce", "butternut squash, cream"
    ],
    "Diet Type": [
        "High-Protein", "Vegan", "Gluten-Free", "Vegan", "High-Protein",
        "Vegetarian", "Vegan", "Vegan", "High-Protein", "Vegan",
        "Vegetarian", "Vegan", "Vegetarian", "Vegan",
        "Vegan", "Vegan", "Low-Carb", "Vegetarian",
        "Vegan", "Vegan", "Vegetarian", "Vegan", "Vegetarian",
        "Vegan", "Vegetarian", "Vegan", "Vegetarian",
        "Vegan", "Vegetarian", "Vegan", "Vegetarian"
    ],
    "Customer Feedback": [random.randint(1, 5) for _ in range(31)]
}

num_dishes = len(data["Dish Name"])
data["Day"] = data["Day"][:num_dishes]
if len(data["Day"]) < num_dishes:
    day_cycle = data["Day"]
    while len(data["Day"]) < num_dishes:
        data["Day"].extend(day_cycle[:(num_dishes - len(data["Day"]))])

menu_df = pd.DataFrame(data)

# Helper functions
def evaluate_recipe_name(recipe_name):
    prompt = f"""
    Evaluate the following recipe name for creativity, newness, and how reasonable it is: "{recipe_name}".
    Provide a score from 1 to 10 (10 being the best) and a brief reason for the score.
    """
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        parts = response_text.split(",", 1)
        if len(parts) == 2:
            score = int(parts[0].strip())
            reason = parts[1].strip()
            return {"score": score, "reason": reason}
        else:
            return {"score": 0, "reason": "Could not parse response"}
    except Exception as e:
        return {"score": 0, "reason": f"Error: {e}"}


def suggest_leftover_recipes_gemini(leftover_ingredients):
    prompt = f"""
    Suggest 5 creative dish names and recipes based on the following leftover ingredients:
    {', '.join(leftover_ingredients)}
    Provide the output as a list of dictionaries with "name" and "recipe" keys.
    """
    try:
        response = model.generate_content(prompt)
        return ast.literal_eval(response.text)
    except Exception as e:
        return [{"name": "Error", "recipe": str(e)}]


def save_game_results_to_csv(recipe_names, filename):
    filepath = os.path.join(os.getcwd(), filename)
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Chef Name", "Recipe Name", "Score", "Reason", "Ingredients", "Date"])
        for chef, data in recipe_names.items():
            writer.writerow([chef, data["recipe"], data["score"], data["reason"], data["ingredients"], current_date])

def display_leaderboard_from_csv(filename):
    filepath = os.path.join(os.getcwd(), filename)
    try:
        df = pd.read_csv(filepath)
        st.write("### Leaderboard")
        st.dataframe(df)
    except FileNotFoundError:
        st.error("Leaderboard file not found.")

# Streamlit UI
st.title("Chef Recipe Challenge")
st.sidebar.title("Game Menu")
menu_option = st.sidebar.selectbox("Select an option", ["Recipe Naming Contest", "Leftover Challenge", "Display Leaderboard"])

if menu_option == "Recipe Naming Contest":
    st.header("Recipe Naming Contest")
    chef_name = st.text_input("Enter your name")
    if st.button("Get Ingredients"):
        ingredient_list = random.choice(menu_df["Ingredients"])
        st.write(f"Your ingredients are: **{ingredient_list}**")
        recipe_name = st.text_input("Suggest a recipe name")
        if st.button("Submit Recipe"):
            evaluation = evaluate_recipe_name(recipe_name)
            st.write(f"Score: {evaluation['score']}")
            st.write(f"Reason: {evaluation['reason']}")
elif menu_option == "Leftover Challenge":
    st.header("Leftover Challenge")
    chef_name = st.text_input("Enter your name")
    leftover_ingredients = st.text_input("Enter leftover ingredients (comma-separated)")
    if st.button("Get Suggestions"):
        ingredients = leftover_ingredients.split(",")
        suggestions = suggest_leftover_recipes_gemini(ingredients)
        for suggestion in suggestions:
            st.write(f"- **{suggestion['name']}**: {suggestion['recipe']}")
elif menu_option == "Display Leaderboard":
    st.header("Leaderboard")
    display_leaderboard_from_csv("recipe_contest_results.csv")
