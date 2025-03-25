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

def suggest_leftover_recipes_gemini(leftover_ingredients):
    prompt = f"""
    Suggest 5 creative dish names and recipes based on the following leftover ingredients:
    Leftover Ingredients: {', '.join(leftover_ingredients)}
    Provide the output in a list of dictionary, with name and recipe as keys.
    """
    try:
        response = get_ai_response(prompt)
        return ast.literal_eval(response)
    except (ValueError, SyntaxError) as e:
        st.error(f"Error generating leftover recipes: {e}, Response: {response}")
        return []
    except Exception as e:
        st.error(f"Error generating leftover recipes: {e}")
        return []

def evaluate_recipe_name(recipe_name):
    prompt = f"""
    Evaluate the following recipe name for creativity, newness, and how reasonable it is: "{recipe_name}".
    Provide a score from 1 to 10 (10 being the best) and a brief reason for the score.
    Return the score and reason as a comma-separated string.
    For example:
    7, The recipe is original and uses common ingredients
    """
    response_text = get_ai_response(prompt)
    parts = response_text.split(",", 1)
    if len(parts) == 2:
        try:
            score = int(parts[0].strip())
            reason = parts[1].strip()
            return {"score": score, "reason": reason}
        except ValueError:
            st.error(f"ValueError: Could not parse score as integer, Response: {response_text}")
            return {"score": 0, "reason": "Could not parse response"}
    else:
        st.error(f"Could not parse response: {response_text}")
        return {"score": 0, "reason": "Could not parse response"}

def save_game_results_to_csv(recipe_names, filename):
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Chef Name", "Recipe Name", "Score", "Reason", "Ingredients"])
        for chef, data in recipe_names.items():
            writer.writerow([chef, data['recipe'], data['score'], data['reason'], data['ingredients']])
    st.success(f"Results saved to {filename}")

def display_leaderboard_from_csv(filename):
    filepath = os.path.join(os.getcwd(), filename)
    try:
        df = pd.read_csv(filepath)
        st.subheader(f"{filename.replace('results.csv', '').replace('', ' ').title()} Leaderboard")
        for _, row in df.iterrows():
            st.write(f"**{row['Chef Name']}:**")
            st.write(f"- Recipe: {row['Recipe Name']}")
            st.write(f"- Score: {row['Score']}")
            st.write(f"- Reason: {row['Reason']}")
            st.write(f"- Ingredients: {row['Ingredients']}")
    except FileNotFoundError:
        st.warning(f"File {filename} not found.")

def chef_recipe_contest():
    st.subheader("Recipe Naming Contest")
    chefs = st.text_input("Enter chef names (comma-separated):")
    if st.button("Start Contest"):
        chefs_list = [chef.strip() for chef in chefs.split(",")]
        recipe_names = {}
        for chef_name in chefs_list:
            ingredient_list = random.choice(menu_df['Ingredients'])
            st.write(f"{chef_name}, your ingredients are: {ingredient_list}")
            recipe_name = st.text_input("Suggest a recipe name:", key=f"recipe_{chef_name}")
            if st.button("Submit", key=f"submit_{chef_name}"):
