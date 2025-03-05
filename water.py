import gradio as gr
import numpy as np
import joblib
from tinydb import TinyDB, Query
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import re
from datetime import datetime
from fpdf import FPDF

# Load the trained model
model = joblib.load("best_rf_model.pkl")

# Initialize database for storing user queries
db = TinyDB("user_queries.json")

# Initialize database for storing user credentials
user_db = TinyDB("user_credentials.json")

# Initialize database for community sharing
community_db = TinyDB("community_data.json")

# Feature columns for reference
features = ['pH', 'Hardness', 'Solids', 'Chloramines', 'Sulfate', 'Conductivity', 'Organic_carbon', 'Trihalomethanes', 'Turbidity']

# Default values for potable water (default values for sliders)
default_values = {
    'pH': 7.5,
    'Hardness': 150,
    'Solids': 500,
    'Chloramines': 4,
    'Sulfate': 250,
    'Conductivity': 500,
    'Organic_carbon': 2,
    'Trihalomethanes': 80,
    'Turbidity': 1
}

# Global variable to track login status
logged_in_user = None

# Function to validate password
def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

# Function to handle user signup
def signup(username, password):
    if not validate_password(password):
        return "Password must be at least 8 characters long and contain at least one special character."
    User = Query()
    if user_db.search(User.username == username):
        return "Username already exists. Please choose a different username."
    user_db.insert({"username": username, "password": password})
    return "Signup successful! Please login."

# Function to handle user login
def login(username, password):
    global logged_in_user
    User = Query()
    user = user_db.search((User.username == username) & (User.password == password))
    if user:
        logged_in_user = username
        return "Login successful!", gr.update(visible=True), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
    else:
        return "Invalid username or password.", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True)

# Function to handle user logout
def logout():
    global logged_in_user
    logged_in_user = None
    return "Logout successful!", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=True)

# Function to check if the user is logged in
def is_logged_in():
    return logged_in_user is not None

# Function to generate a PDF report
def generate_report(pH, Hardness, Solids, Chloramines, Sulfate, Conductivity, Organic_carbon, Trihalomethanes, Turbidity):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Water Quality Report", ln=True, align="C")
    pdf.cell(200, 10, txt="----------------------------------------", ln=True, align="C")
    pdf.cell(200, 10, txt=f"pH: {pH}", ln=True)
    pdf.cell(200, 10, txt=f"Hardness: {Hardness} mg/L", ln=True)
    pdf.cell(200, 10, txt=f"Solids: {Solids} mg/L", ln=True)
    pdf.cell(200, 10, txt=f"Chloramines: {Chloramines} mg/L", ln=True)
    pdf.cell(200, 10, txt=f"Sulfate: {Sulfate} mg/L", ln=True)
    pdf.cell(200, 10, txt=f"Conductivity: {Conductivity} µS/cm", ln=True)
    pdf.cell(200, 10, txt=f"Organic Carbon: {Organic_carbon} mg/L", ln=True)
    pdf.cell(200, 10, txt=f"Trihalomethanes: {Trihalomethanes} µg/L", ln=True)
    pdf.cell(200, 10, txt=f"Turbidity: {Turbidity} NTU", ln=True)
    pdf.cell(200, 10, txt="----------------------------------------", ln=True, align="C")
    pdf.cell(200, 10, txt="Thank you for using our system!", ln=True, align="C")
    pdf_output = "water_quality_report.pdf"
    pdf.output(pdf_output)
    return pdf_output

# Function to display water quality standards
def display_water_standards():
    standards = {
        "Parameter": ["pH", "Hardness", "Solids", "Chloramines", "Sulfate", "Conductivity", "Organic Carbon", "Trihalomethanes", "Turbidity"],
        "Standard Value": ["6.5 - 8.5", "0 - 300 mg/L", "< 500 mg/L", "< 4 mg/L", "< 250 mg/L", "50 - 500 µS/cm", "< 2 mg/L", "< 80 µg/L", "< 1 NTU"]
    }
    return pd.DataFrame(standards)
import gradio as gr

# Define the function before calling it
def predict_water_quality(pH, Hardness, Solids, Chloramines, Sulfate, Conductivity, Organic_carbon, Trihalomethanes, Turbidity):
    # Your prediction logic here
    return "Potable"  # Example return value

# Function to display user dashboard in table format
def get_user_dashboard():
    if not is_logged_in():
        return pd.DataFrame({"Error": ["Please login to access the dashboard."]})
    User = Query()
    history = db.search(User.username == logged_in_user)
    if not history:
        return pd.DataFrame({"Message": ["No historical data found."]})
    df = pd.DataFrame(history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    return df

# Function to visualize user input data as a bar graph
def visualize_input_data(pH, Hardness, Solids, Chloramines, Sulfate, Conductivity, Organic_carbon, Trihalomethanes, Turbidity):
    fig, ax = plt.subplots(figsize=(8, 5))
    params = [pH, Hardness, Solids, Chloramines, Sulfate, Conductivity, Organic_carbon, Trihalomethanes, Turbidity]
    ax.bar(features, params, color='teal')
    ax.set_title("Water Quality Parameters")
    ax.set_ylabel("Value")
    ax.set_xlabel("Parameters")
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    img_tag = f'<img src="data:image/png;base64,{img_str}" width="600"/>'
    return img_tag

# Function to create a gallery of water quality visualizations
def create_visualization_gallery():
    if not is_logged_in():
        return "Please login to view the gallery."
    User = Query()
    history = db.search(User.username == logged_in_user)
    if not history:
        return "No historical data found."
    df = pd.DataFrame(history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # Create a gallery of plots
    gallery_html = "<div style='display: flex; flex-wrap: wrap; gap: 20px;'>"
    for feature in features:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(df.index, df[feature], label=feature, color='blue')
        ax.set_title(f"{feature} Over Time")
        ax.set_ylabel(feature)
        ax.set_xlabel("Timestamp")
        ax.legend()
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")
        gallery_html += f"<div style='flex: 1 1 300px;'><img src='data:image/png;base64,{img_str}' width='100%'/></div>"
        plt.close()
    gallery_html += "</div>"
    return gallery_html

# Custom CSS for better styling
custom_css = """
    .gradio-container {
        font-family: Arial, sans-serif;
    }
    .gradio-button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 5px;
    }
    .gradio-button:hover {
        background-color: #45a049;
    }
    .gradio-slider {
        width: 100%;
    }
    .gradio-textbox {
        width: 100%;
        padding: 10px;
        margin: 5px 0;
        box-sizing: border-box;
        border: 2px solid #ccc;
        border-radius: 4px;
    }
    .gradio-output {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
    }
"""

# Create the Gradio interface for signup, login, and main features
with gr.Blocks(css=custom_css) as main_ui:
    gr.Markdown("# Water Potability Prediction System")
    with gr.Tabs():
        with gr.TabItem("Signup"):
            gr.Markdown("## Signup")
            username = gr.Textbox(label="Username")
            password = gr.Textbox(label="Password", type="password")
            signup_button = gr.Button("Signup")
            signup_output = gr.Textbox(label="Signup Status", interactive=False)
            signup_button.click(signup, inputs=[username, password], outputs=signup_output)

        with gr.TabItem("Login"):
            gr.Markdown("## Login")
            username = gr.Textbox(label="Username")
            password = gr.Textbox(label="Password", type="password")
            login_button = gr.Button("Login")
            login_output = gr.Textbox(label="Login Status", interactive=False)
            water_ui_visibility = gr.Textbox(visible=False)  # Placeholder for water_ui visibility
            login_ui_visibility = gr.Textbox(visible=False)  # Placeholder for login_ui visibility
            logout_button = gr.Button("Logout", visible=False)
            login_button.click(login, inputs=[username, password], outputs=[login_output, water_ui_visibility, login_ui_visibility, logout_button, login_button])
            logout_button.click(logout, outputs=[login_output, water_ui_visibility, login_ui_visibility, logout_button, login_button])

        with gr.TabItem("Water Potability Prediction"):
            gr.Markdown("## 🌊 Water Potability Prediction System")
            gr.Markdown("### Enter Water Parameters:")
            with gr.Row():
                pH = gr.Slider(minimum=0, maximum=14, step=0.1, label="pH Level", value=7.5, info="pH level of the water (6.5 to 8.5 is ideal).")
                Hardness = gr.Slider(minimum=0, maximum=500, step=1, label="Hardness (mg/L)", value=150, info="Hardness of the water (0-300 mg/L is optimal).")
            with gr.Row():
                Solids = gr.Slider(minimum=0, maximum=50000, step=10, label="Solids (mg/L)", value=500, info="Total dissolved solids (less than 500 mg/L is optimal).")
                Chloramines = gr.Slider(minimum=0, maximum=10, step=0.1, label="Chloramines (mg/L)", value=4, info="Chloramines level (less than 4 mg/L is ideal).")
            with gr.Row():
                Sulfate = gr.Slider(minimum=0, maximum=500, step=1, label="Sulfate (mg/L)", value=250, info="Sulfate level (less than 250 mg/L is ideal).")
                Conductivity = gr.Slider(minimum=0, maximum=2000, step=5, label="Conductivity (μS/cm)", value=500, info="Electrical conductivity of water (50-500 µS/cm is optimal).")
            with gr.Row():
                Organic_carbon = gr.Slider(minimum=0, maximum=50, step=0.5, label="Organic Carbon (mg/L)", value=2, info="Organic carbon level (less than 2 mg/L is ideal).")
                Trihalomethanes = gr.Slider(minimum=0, maximum=150, step=1, label="Trihalomethanes (μg/L)", value=80, info="Trihalomethanes level (less than 80 µg/L is optimal).")
            Turbidity = gr.Slider(minimum=0, maximum=10, step=0.1, label="Turbidity (NTU)", value=1, info="Turbidity level (less than 1 NTU is ideal).")
            submit = gr.Button("🔍 Predict")
            reset = gr.Button("🔄 Reset")
            potability_score = gr.Textbox(label="Potability Score", interactive=False, elem_classes=["output"])
            recommendations = gr.Textbox(label="Recommendations", interactive=False, elem_classes=["output"])
            prediction_output = gr.Textbox(label="Prediction (0: Not Potable, 1: Potable)", interactive=False, elem_classes=["output"])
            water_chart = gr.HTML(label="Water Quality Chart")
            # Define UI components
    with gr.Blocks() as demo:
        pH = gr.Number(label="pH")
        Hardness = gr.Number(label="Hardness")
        Solids = gr.Number(label="Solids")
        Chloramines = gr.Number(label="Chloramines")
        Sulfate = gr.Number(label="Sulfate")
        Conductivity = gr.Number(label="Conductivity")
        Organic_carbon = gr.Number(label="Organic Carbon")
        Trihalomethanes = gr.Number(label="Trihalomethanes")
        Turbidity = gr.Number(label="Turbidity")
        submit = gr.Button("Predict")
        submit.click(predict_water_quality, inputs=[pH, Hardness, Solids, Chloramines, Sulfate, Conductivity, Organic_carbon, Trihalomethanes, Turbidity],
                         outputs=[potability_score, recommendations, prediction_output, water_chart])
        reset.click(lambda: [7.5, 150, 500, 4, 250, 500, 2, 80, 1], outputs=[pH, Hardness, Solids, Chloramines, Sulfate, Conductivity, Organic_carbon, Trihalomethanes, Turbidity])

        with gr.TabItem("Water Quality Standards"):
            gr.Markdown("## Water Quality Standards")
            standards = gr.Dataframe(label="Standards", interactive=False, value=display_water_standards())

        with gr.TabItem("User Dashboard"):
            gr.Markdown("## User Dashboard")
            dashboard_output = gr.Dataframe(label="Dashboard", interactive=False)
            refresh_dashboard = gr.Button("🔄 Refresh Dashboard")
            refresh_dashboard.click(get_user_dashboard, outputs=dashboard_output)

        with gr.TabItem("Data Visualization Gallery"):
            gr.Markdown("## Water Quality Data Visualization Gallery")
            gallery_output = gr.HTML()
            refresh_gallery = gr.Button("🔄 Refresh Gallery")
            refresh_gallery.click(create_visualization_gallery, outputs=gallery_output)

        with gr.TabItem("Generate Report"):
            gr.Markdown("## Generate Water Quality Report")
            report_output = gr.File(label="Download Report")
            generate_report_button = gr.Button("Generate Report")
            generate_report_button.click(generate_report, inputs=[pH, Hardness, Solids, Chloramines, Sulfate, Conductivity, Organic_carbon, Trihalomethanes, Turbidity], outputs=report_output)

        with gr.TabItem("Visualize Input Data"):
            gr.Markdown("## Visualize Input Data")
            visualize_output = gr.HTML()
            visualize_button = gr.Button("Visualize Data")
            visualize_button.click(visualize_input_data, inputs=[pH, Hardness, Solids, Chloramines, Sulfate, Conductivity, Organic_carbon, Trihalomethanes, Turbidity], outputs=visualize_output)

main_ui.launch()
