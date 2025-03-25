#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
import random
import csv
import os
import google.generativeai as genai

# Configure API Key securely
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ API Key is missing. Go to Streamlit Cloud → Settings → Secrets and add your API key.")
    st.stop()

# Generate AI Evaluation for Recipe Name
def evaluate_recipe_name(recipe_name):
    prompt = f"""
    Evaluate the following recipe name for creativity, relevance, and originality:
    "{recipe_name}"
    Provide:
    - A score out of 10
    - A brief reason for the score.
    Return this as a JSON object with keys 'score' and 'reason'.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        return eval(response_text)  # Convert AI response to dictionary
    except Exception as e:
        return {"score": 0, "reason": f"AI Error: {str(e)}"}

# Save results to a CSV file
def save_results_to_csv(data, filename="recipe_contest_results.csv"):
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Chef Name", "Recipe Name", "Score", "Reason"])
        for chef, details in data.items():
            writer.writerow([chef, details["recipe"], details["score"], details["reason"]])

# Load results from CSV for leaderboard
def load_results_from_csv(filename="recipe_contest_results.csv"):
    filepath = os.path.join(os.getcwd(), filename)
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    else:
        return pd.DataFrame(columns=["Chef Name", "Recipe Name", "Score", "Reason"])

# Streamlit App
def main():
    st.title("🍽️ AI Recipe Name Contest")
    st.write("Compete to create the best recipe names!")

    # Step 1: Collect inputs
    st.header("Step 1: Enter Chef and Recipe Details")
    chefs = []
    recipe_data = {}

    chef_name = st.text_input("Enter Chef Name")
    if chef_name:
        ingredients = random.choice(["chicken, garlic, onion", "quinoa, spinach, avocado", "tofu, soy sauce, ginger"])
        st.write(f"Your ingredients are: **{ingredients}**")
        recipe_name = st.text_input("Enter Your Recipe Name")

        # Evaluate recipe name
        if st.button("Evaluate Recipe Name"):
            with st.spinner("Evaluating recipe..."):
                evaluation = evaluate_recipe_name(recipe_name)
                recipe_data[chef_name] = {
                    "recipe": recipe_name,
                    "score": evaluation["score"],
                    "reason": evaluation["reason"],
                }
                st.success(f"Score: {evaluation['score']}/10")
                st.write(f"Reason: {evaluation['reason']}")

    # Save results
    if recipe_data:
        save_results_to_csv(recipe_data)

    # Step 2: Display Leaderboard
    st.header("Step 2: View Leaderboard")
    leaderboard = load_results_from_csv()
    if not leaderboard.empty:
        st.write("🏆 **Leaderboard** 🏆")
        st.dataframe(leaderboard)
    else:
        st.write("No results yet. Submit a recipe name to get started!")

if __name__ == "__main__":
    main()

