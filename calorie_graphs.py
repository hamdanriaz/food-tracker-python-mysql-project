import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from database import connect_db

def fetch_meal_data(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT date_added, calories FROM meals WHERE user_id = %s", (user_id,))
    records = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(records, columns=["date_added", "calories"])
    df['date_added'] = pd.to_datetime(df['date_added'])
    return df

def generate_graph(df, period='D'):
    if df.empty:
        return None

    plt.figure(figsize=(8, 4))
    if period == 'D':
        df['hour'] = df['date_added'].dt.hour
        df_daily = df.groupby('hour')['calories'].sum().reset_index()
        plt.plot(df_daily['hour'], df_daily['calories'], marker='o')
        plt.title('Daily Calorie Intake (Time of Day)')
        plt.xlabel('Time')
        plt.xticks(rotation=45)
    else:
        freq_map = {'W': 'W', 'M': 'ME', 'Y': 'YE'}
        df_grouped = df.groupby(pd.Grouper(key='date_added', freq=freq_map[period])).sum().reset_index()
        plt.plot(df_grouped['date_added'], df_grouped['calories'], marker='o')
        plt.title(f'{period}ly Calorie Intake')
        plt.xlabel('Date')

    plt.ylabel('Calories')
    plt.tight_layout()
    return plt

def save_graph(df, period):
    fig = generate_graph(df, period)
    if fig:
        filename = f"calorie_{period.lower()}_graph.png"
        fig.savefig(filename)
        fig.close()
        return filename
    return None
