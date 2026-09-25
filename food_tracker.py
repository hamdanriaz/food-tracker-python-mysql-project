import PySimpleGUI as sg
import os
from calorie_graphs import fetch_meal_data, generate_graph, save_graph
from database import (
    add_meal, fetch_meals_today, clear_meals_table,
    signup_user, login_user, remove_users
)
from food_advisor import get_tensorflow_diet_advice as get_diet_advice
import datetime
import csv
from fpdf import FPDF

try:
    with open("theme.txt", "r") as f:
        sg.theme(f.read().strip())
except:
    sg.theme("DefaultNoMoreNagging")

ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'very_active': 1.725,
    'extra_active': 1.9
}

def calculate_tdee(user):
    bmr = 10 * user['weight_kg'] + 6.25 * user['height_cm'] - 5 * user['age']
    bmr += 5 if user['gender'] == 'male' else -161
    return round(bmr * ACTIVITY_MULTIPLIERS[user['activity_level']])

def load_food_data():
    food = {}
    try:
        with open("foods.csv", newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                food[row["Meal"]] = int(row["Calories"])
    except Exception as e:
        sg.popup_error(f"Error loading foods.csv!\n{e}")
    return food

def txt_to_pdf(txt_path, pdf_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            pdf.cell(0, 10, txt=line.rstrip(), ln=1)
    pdf.output(pdf_path)

def download_pdf_report(meals, user):
    if not meals:
        sg.popup("No meals found.")
        return
    txt_name = f"{user['username']}_report_{datetime.date.today()}.txt"
    pdf_name = txt_name.replace(".txt", ".pdf")
    with open(txt_name, "w", encoding="utf-8") as f:
        f.write("Food Tracker Report\n")
        f.write(f"User: {user['username']}\n")
        f.write(f"Date: {datetime.date.today()}\n\n")
        f.write("{:<60} {:<20} {:<30} {:<40}\n".format("Meal", "Grams", "Calories", "Timestamp"))
        f.write("-" * 150 + "\n")
        for m in meals:
            f.write("{:<60} {:<20} {:<30} {:<40}\n".format(m[0], m[1], m[2], m[3]))
    txt_to_pdf(txt_name, pdf_name)
    sg.popup("PDF Report saved", f"Saved as {pdf_name}")

import PySimpleGUI as sg

def show_tdee_popup():
    layout = [
        [sg.Text("Why enter the sensitive data", font=("Arial", 16, "bold"))],
        [sg.Multiline(
            """TDEE is the total energy you burn in a day.
The calculation needs your age, height, weight and activity level.

Formula
BMR (Mifflin-St Jeor):
Men: 10*weight + 6.25*height - 5*age + 5
Women: 10*weight + 6.25*height - 5*age - 161

TDEE = BMR * Activity Level

Activity Levels:
1. Sedentary: 1.2
2. Lightly Active: 1.375
3. Moderately Active: 1.55
4. Very Active: 1.725
5. Extra Active: 1.9""",
            size=(60,18),
            disabled=True
        )],
        [sg.Button("Close")]
    ]

    window = sg.Window("Why enter the sensitive data", layout, modal=True)

    while True:
        e, _ = window.read()
        if e in (sg.WINDOW_CLOSED, "Close"):
            break


def signup_popup():
    layout = [
        [sg.Text("Username"), sg.Input(key="-USER-")],
        [sg.Text("Password"), sg.Input(key="-PASS-", password_char="*")],
        [sg.Text("Gender"), sg.Radio("Male", group_id="Gender", key="-MALE-"), sg.Radio("Female", group_id="Gender", key="-FEMALE-")],
        [sg.Text("Height (cm)"), sg.Input(key="-HEIGHT-")],
        [sg.Text("Weight (kg)"), sg.Input(key="-WEIGHT-")],
        [sg.Text("Age"), sg.Input(key="-AGE-")],
        [sg.Text("Activity Level"),
         sg.Combo(list(ACTIVITY_MULTIPLIERS.keys()), key="-ACTIVITY-")],
        [sg.Button("Submit"), sg.Button("Cancel"), sg.Button("Why the Sensitive Data?")]
    ]
    win = sg.Window("Signup", layout, modal=True)
    while True:
        ev, val = win.read()
        if ev in (sg.WIN_CLOSED, "Cancel"):
            break
        elif ev == "Why the Sensitive Data?":
            show_tdee_popup()
        elif ev == "Submit":
            if not all(val[key] for key in ["-USER-", "-PASS-", "-HEIGHT-", "-WEIGHT-", "-AGE-", "-ACTIVITY-"]):
                sg.popup_error("Please fill in all fields.")
                continue

            if not (val["-MALE-"] or val["-FEMALE-"]):
                sg.popup_error("Please select a gender.")
                continue

            try:
                height = int(val["-HEIGHT-"])
                weight = int(val["-WEIGHT-"])
                age = int(val["-AGE-"])
            except ValueError:
                sg.popup_error("Height, weight, and age must be numbers.")
                continue

            gender = "Male" if val["-MALE-"] else "Female"

            if signup_user(val["-USER-"], val["-PASS-"], gender, height, weight, age, val["-ACTIVITY-"]):
                sg.popup("Signup Successful! Login now.")
                break
            else:
                sg.popup_error("Signup failed. Username may already exist.")

    win.close()

def remove_popup():
    layout = [
        [sg.Text("Username"), sg.Input(key="-U-")],
        [sg.Text("Password"), sg.Input(key="-P-", password_char="*")],
        [sg.Button("Remove"), sg.Button("Cancel")]
    ]

    win = sg.Window("Remove Account", layout, modal=True)

    while True:
        ev, val = win.read()
        if ev in (sg.WIN_CLOSED, "Cancel"):
            break
        if ev == "Remove":
            try:
                user = login_user(val["-U-"], val["-P-"])
                if user:
                    auth_p = sg.popup_get_text("Enter Password Again", title="Re-enter Password", password_char='*')
                    if auth_p == val["-P-"]:
                        if sg.popup_yes_no("You CANNOT undo this action... Do you wish to continue") == 'Yes':
                            if remove_users(val["-U-"]):
                                sg.popup("Account Removed")
                            else:
                                sg.popup_error("There was a problem... Try again")
                        else:
                            sg.popup("There was a problem... Try entering the correct password")
                    else:
                        sg.popup_error("There was a problem... Try again")
                else:
                    sg.popup_error("There was a problem... Try again")
            except:
                sg.popup_error("Invalid inputs. Try again.")
    win.close()


def login_window():
    layout = [
        [sg.Text("Username"), sg.Input(key="-USERNAME-")],
        [sg.Text("Password"), sg.Input(key="-PASSWORD-", password_char="*")],
        [sg.Button("Login"), sg.Button("Signup"), sg.Button("Delete Account"), sg.Button("Exit")]
    ]
    return sg.Window("Login", layout)

def show_graph_popup(user_id):
    selected_period = 'D'
    df = fetch_meal_data(user_id)

    layout = [
        [sg.Button("Daily", key='-DAILY-'), sg.Button("Weekly", key='-WEEKLY-'),
         sg.Button("Monthly", key='-MONTHLY-'), sg.Button("Yearly", key='-YEARLY-')],
        [sg.Canvas(key='-CANVAS-')],
        [sg.Button("Download Graph", key='-DOWNLOAD-'), sg.Button("Close")]
    ]

    window = sg.Window("Calorie Intake Graphs", layout, finalize=True, resizable=True, element_justification='center')

    def draw(period):
        fig = generate_graph(df, period)
        if fig:
            fig_canvas_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig.gcf())
            return fig_canvas_agg

    fig_agg = draw('D')

    while True:
        event, _ = window.read()
        if event in (sg.WINDOW_CLOSED, "Close"):
            break
        elif event == '-DAILY-':
            selected_period = 'D'
            fig_agg.get_tk_widget().forget()
            fig_agg = draw('D')
        elif event == '-WEEKLY-':
            selected_period = 'W'
            fig_agg.get_tk_widget().forget()
            fig_agg = draw('W')
        elif event == '-MONTHLY-':
            selected_period = 'M'
            fig_agg.get_tk_widget().forget()
            fig_agg = draw('M')
        elif event == '-YEARLY-':
            selected_period = 'Y'
            fig_agg.get_tk_widget().forget()
            fig_agg = draw('Y')
        elif event == '-DOWNLOAD-':
            path = save_graph(df, selected_period)
            sg.popup("Graph Saved", f"Graph saved as: {path}" if path else "No data to save")

    window.close()

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def meal_selector_popup(food_data):
    def add_custom_meal_popup():
        layout = [
            [sg.Text("Meal Name:"), sg.Input(key="-MEAL_NAME-")],
            [sg.Text("Calories per 100g:"), sg.Input(key="-CALORIES-")],
            [sg.Button("Save"), sg.Button("Cancel")]
        ]
        win = sg.Window("Add Your Own Meal", layout, modal=True)
        while True:
            event, values = win.read()
            if event in (sg.WIN_CLOSED, "Cancel"):
                break
            elif event == "Save":
                name = values["-MEAL_NAME-"].strip()
                cals = values["-CALORIES-"].strip()
                if not name or not cals.isdigit():
                    sg.popup_error("Invalid input. Enter name and numeric calories.")
                    continue
                cals = int(cals)
                with open("foods.csv", "a", newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=["Meal", "Grams", "Calories"])
                    if file.tell() == 0:
                        writer.writeheader()
                    writer.writerow({"Meal": name, "Grams": 100, "Calories": cals})
                food_data[name] = cals
                sg.popup("Meal Added!")
                break
        win.close()

    items = sorted(food_data.keys())
    layout = [
        [sg.Text("Search:"), sg.Input(key='-SEARCH-', enable_events=True)],
        [sg.Listbox(values=items, size=(30, 10), key='-LIST-', enable_events=True)],
        [sg.Button("Select"), sg.Button("Add Own Meal"), sg.Button("Cancel")]
    ]
    win = sg.Window("Choose a Meal", layout, modal=True)
    chosen = None
    while True:
        event, vals = win.read()
        if event in (sg.WIN_CLOSED, "Cancel"):
            break
        elif event == "Add Own Meal":
            add_custom_meal_popup()
            items = sorted(food_data.keys())
            win["-LIST-"].update(items)
        elif event == "-SEARCH-":
            keyword = vals["-SEARCH-"].lower()
            filtered = [item for item in items if keyword in item.lower()]
            win["-LIST-"].update(filtered)
        elif event == "Select":
            if vals["-LIST-"]:
                chosen = vals["-LIST-"][0]
                break
        elif event == "-LIST-":
            if vals["-LIST-"]:
                chosen = vals["-LIST-"][0]
    win.close()
    return chosen

def theme_window():
    def preview_theme(theme_name):
        sg.theme(theme_name)
        layout = [[sg.Text(f"This is a preview of theme: {theme_name}")],
                [sg.Button("Looks Cool"), sg.Button("Meh")]]
        preview_win = sg.Window("Theme Preview", layout)
        event, _ = preview_win.read()
        preview_win.close()

    layout = [
        [sg.Text("Select your vibe (theme):")],
        [sg.Combo(values=sg.theme_list(), key="-THEME-", size=(30, 20))],
        [sg.Button("Preview Theme"), sg.Button("Save Theme"), sg.Button("Exit")]
    ]

    window = sg.Window("Theme Chooser", layout)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == "Exit":
            break

        selected_theme = values["-THEME-"]

        if event == "Preview Theme":
            if selected_theme:
                preview_theme(selected_theme)
            else:
                sg.popup("Yo pick a theme first!", title="Bruh Moment")

        elif event == "Save Theme":
            if selected_theme:
                with open("theme.txt", "w") as f:
                    f.write(selected_theme)
                sg.popup(f"Theme '{selected_theme}' saved!", title="Success")
            else:
                sg.popup("Don't save air bro, pick a theme.", title="Warning")
    window.close()


def open_settings(user_id):
    layout = [
        [sg.Button("Choose Theme")],
        [sg.HorizontalSeparator()],
        [sg.Button("Reset Data", button_color=("white", "red"))],
        [sg.Button("Close")]
    ]
    win = sg.Window("Settings", layout, modal=True)
    while True:
        event, val = win.read()
        if event in (sg.WIN_CLOSED, "Close"):
            break
        elif event == "Choose Theme":
            win.close()
            theme_window()
            break
        elif event == "Reset Data":
            if sg.popup_yes_no("Clear all meals?") == "Yes":
                clear_meals_table(user_id)
                sg.popup("Data cleared. RESTART the app to see changes.")
    win.close()

def get_tip(cal, tdee):
    if cal == 0:
        return "Welcome! What did you eat today?"
    elif cal < 0:
        return "Bruh... how do you have negative calories?"
    elif cal < 0.4 * tdee:
        return "You REALLY need to eat!"
    elif cal > 1.5 * tdee:
        return "You should REALLY stop bro!"
    elif cal < tdee:
        return "You're under your target. You can eat more if you want."
    elif cal > tdee:
        return "You're over your target. Chill with the snacks maybe?"
    else:
        return "Perfect! You're right on track today"


def main_app(user):
    food_data = load_food_data()
    tdee = calculate_tdee(user)
    meals_today = fetch_meals_today(user['id'])
    total_calories = sum(m[2] for m in meals_today)

    def update_tip():
        return get_tip(total_calories, tdee)

    layout = [
        [sg.Text(f"Welcome, {user['username']}!  |  TDEE: {tdee} kcal")],
        [sg.Button("Select Meal"), sg.Text("", key="-MEAL_SELECTED-", size=(20, 1)),
         sg.Text("Grams:"), sg.Input(key="-GRAMS-", size=(10, 1))],
        [sg.Button("Add Meal")],
        [sg.Text("Total Calories Today:"), sg.Text(f"{total_calories} kcal", key="-CALORIES-")],
        [sg.Text("Message:"), sg.Text(update_tip(), key="-TIP-", size=(45, 1))],
        [
            sg.Button("AI Diet Advice"), 
            sg.Button("Generate Graphs"),
            sg.Button("Download Report"),
            sg.Button("Settings"), sg.Button("Exit")
            ]
    ]

    win = sg.Window("Food Tracker", layout, finalize=True)
    selected_meal = None

    while True:
        e, v = win.read()
        if e in (sg.WIN_CLOSED, "Exit"):
            break

        elif e == "Select Meal":
            selected_meal = meal_selector_popup(food_data)
            if selected_meal:
                win["-MEAL_SELECTED-"].update(selected_meal)

        elif e == "Add Meal":
            if not selected_meal:
                sg.popup_error("Select a meal first.")
                continue
            grams = v["-GRAMS-"].strip()
            if not grams.isdigit():
                sg.popup_error("Enter valid grams.")
                continue
            grams = int(grams)
            cal = (food_data[selected_meal] * grams) // 100
            total_calories += cal
            timestamp = str(datetime.datetime.now())
            add_meal(selected_meal, grams, cal, user["id"])
            meals_today.append((selected_meal, grams, cal, timestamp))
            win["-CALORIES-"].update(f"{total_calories} kcal")
            win["-TIP-"].update(update_tip())

        elif e == "Reset Meals":
            if sg.popup_yes_no("Clear all today's meals?") == "Yes":
                clear_meals_table(user["id"])
                meals_today.clear()
                total_calories = 0
                win["-CALORIES-"].update("0 kcal")
                win["-TIP-"].update(update_tip())

        elif e == "Download Report":
            download_pdf_report(meals_today, user)

        elif e == 'Generate Graphs':
            show_graph_popup(user['id'])

        elif e == "Download Graphs":
            folder = sg.popup_get_folder("Select folder to save graphs")
            if folder:
                for fname in ['daily_calories.png', 'weekly_calories.png', 'monthly_calories.png', 'yearly_calories.png']:
                    if os.path.exists(fname):
                        os.rename(fname, os.path.join(folder, fname))
                sg.popup("Graphs downloaded to:", folder)

        elif e == "Settings":
            open_settings(user["id"])

        elif e == "AI Diet Advice":
            if not meals_today:
                sg.popup("No meals to analyze.")
            else:
                advice = get_diet_advice(meals_today)
                sg.popup("AI Diet Advice", advice)

    win.close()

while True:
    win = login_window()
    event, values = win.read()

    if event in (sg.WIN_CLOSED, "Exit"):
        break

    elif event == "Signup":
        win.close()
        signup_popup()

    elif event == "Login":
        user = login_user(values["-USERNAME-"], values["-PASSWORD-"])
        if user:
            win.close()
            main_app(user)
        else:
            win.close()
            sg.popup_error("Invalid username or password.")
    
    elif event == "Delete Account":
        win.close()
        remove_popup()
    
    elif e == "Select Meal":
        selected_meal = meal_selector_popup(food_data)
        if selected_meal:
            win["-MEAL_SELECTED-"].update(selected_meal)
    
    elif e == "Settings":
        open_settings(user['id'])
