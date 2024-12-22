import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from PIL import Image
from io import BytesIO
from streamlit_option_menu import option_menu
from utils import load_prompt, generate_response_llm
import logging
import time
from google.api_core.exceptions import ResourceExhausted
from langdetect import detect  # Import langdetect for language detection
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up Streamlit page configuration
st.set_page_config(
    page_title="Dashboard App",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hardcoded username and password
USERNAME = "admin"
PASSWORD = "uy2x4AD8"

def login():
    st.title("Login")
    st.write("Please enter your credentials to access the application.")
    # Login form
    with st.form(key='login_form'):
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if username == USERNAME and password == PASSWORD:
                st.session_state.logged_in = True
                st.session_state.login_attempts = 0
                st.session_state.show_popup = True  # Set the popup flag
                st.session_state.page = 'Home'  # Navigate to Home page after login
            else:
                st.session_state.login_attempts = st.session_state.get('login_attempts', 0) + 1
                st.error("Invalid credentials. Please try again.")
                if st.session_state.login_attempts >= 3:
                    st.error("Too many failed login attempts. Please wait a moment.")
                    st.session_state.login_attempts = 0

def create_pdf(response):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    styles = getSampleStyleSheet()

    response_lines = response.strip().split("\n")
    response_data = [line.split("|")[1:-1] for line in response_lines]

    col_widths = [doc.width * 0.21, doc.width * 0.23, doc.width * 0.23, doc.width * 0.21]
    response_table = Table(response_data, colWidths=col_widths)
    
    response_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    story.append(Paragraph("<b>Response:</b>", styles['Heading2']))
    story.append(response_table)
    story.append(Paragraph("<br/>", styles['Normal']))

    doc.build(story)

    buffer.seek(0)
    return buffer

def show_welcome_popup():
    st.markdown("""
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        #welcome-popup {
            position: absolute;
            top: 200px;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 4em;
            font-weight: bold;
            color:rgba(255, 87, 51, 0.9);
            z-index: 1000;
            text-align: center;
            animation: fadeOut 3s forwards;
        }
        @keyframes fadeOut {
            0% { opacity: 1; }
            100% { opacity: 0; }
        }
        .hide-popup {
            display: none;
        }
    </style>
    <div id="welcome-popup">
        <div>
            <div class="festival-icon">🎉</div>
            Welcome to Health Dashboard App!
        </div>
    </div>
    <script>
        setTimeout(function() {
            document.getElementById('welcome-popup').classList.add('hide-popup');
            document.body.style.overflow = 'auto';
        }, 3000);
    </script>
    """, unsafe_allow_html=True)

def get_base64_image(img_path):
    try:
        with open(img_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except FileNotFoundError:
        st.error(f"Image file {img_path} not found.")
        return None

def generate_response_with_retry(*args, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = generate_response_llm(*args, **kwargs)
            logging.info("API response received successfully.")
            return response
        except ResourceExhausted as e:
            logging.warning(f"Quota exceeded, retrying... ({attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retrying
            else:
                logging.error("Quota exceeded. Please try again later.")
                st.error("Quota exceeded. Please try again later.")
                raise e

def extract_table_from_response(response):
    try:
        # Split the response into lines
        lines = response.strip().split("\n")

        # Check if there are enough lines in the response
        if len(lines) < 2:
            return pd.DataFrame()  # Return empty DataFrame if not enough lines

        # Determine headers based on the first non-empty line
        first_line = lines[0].strip()
        if "|" in first_line:
            headers = [header.strip() for header in first_line.split("|") if header.strip()]
        else:
            # Fallback if first line does not contain '|'
            headers = ['Header1', 'Header2', 'Header3', 'Header4', 'Header5']  # Example default headers

        data = []
        for line in lines[1:]:  # Skip the first line if it is a header
            # Skip lines that contain symbols like '---'
            if '---' in line:
                continue  # Skip this line

            # Split each line by '|' and strip whitespace
            row = [cell.strip() for cell in line.split("|") if cell.strip()]

            # Append rows that match the number of headers and are not empty
            if len(row) == len(headers) and any(row):
                data.append(row)
            else:
                logging.warning(f"Skipped malformed line: {line}")

        # Create a DataFrame with placeholder columns
        df = pd.DataFrame(data)
        
        # Debugging statements
        logging.info(f"DataFrame shape before renaming columns: {df.shape}")
        logging.info(f"Number of headers: {len(headers)}")
        logging.info(f"Headers: {headers}")

        # Ensure the number of headers matches the number of DataFrame columns
        if len(headers) != df.shape[1]:
            logging.error(f"Column length mismatch: {len(headers)} headers but {df.shape[1]} columns in DataFrame")
            # Handle mismatch, e.g., truncate or pad headers to match DataFrame columns
            headers = headers[:df.shape[1]]  # Adjust headers to match the number of DataFrame columns

        df.columns = headers  # Update DataFrame columns with new headers

        return df

    except Exception as e:
        logging.error(f"Error extracting table data: {e}")
        return pd.DataFrame()  # Return empty DataFrame in case of any error
def main_app():
    # Sidebar menu
    with st.sidebar:
        selected = option_menu('Dashboard',
                              ['Home', 'Extractor', 'Data Analysis', 'Data Visualization'],
                              icons=['house', 'activity', 'bar-chart', 'file-text'],
                              default_index=0)
    
    # Update page selection in session state
    if 'page' not in st.session_state:
        st.session_state.page = selected
    else:
        st.session_state.page = selected

    # Home page content
    if st.session_state.page == 'Home':
        if st.session_state.get("show_popup", False):
            show_welcome_popup()
            st.session_state.show_popup = False
        
        st.markdown("""
            <style>
                .title {
                    font-size: 3em;
                    color: #FF5733;
                    text-align: center;
                    animation: fadeIn 5s ease-in-out;
                }
                .subtitle {
                    font-size: 2em;
                    color: #FF5733;
                    text-align: center;
                    animation: fadeIn 5s ease-in-out;
                }
                .image-container {
                    text-align: center;
                    margin: 20px 0;
                    animation: fadeIn 5s ease-in-out;
                }
                .image {
                    width: 100%;
                    max-width: 1200px;
                    border: 5px solid #FF5733;
                    border-radius: 15px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
            </style>
            <h1 class="title"><em> Health Dashboard App </em></h1>
        """, unsafe_allow_html=True)

        img_base64 = get_base64_image('img.jpg')
        if img_base64:
            st.markdown(f"""
                <div class="image-container">
                    <img src="data:image/jpeg;base64,{img_base64}" class="image">
                </div>
            """, unsafe_allow_html=True)

        st.markdown("""
            <h2 class="subtitle"><em>Welcome to the Health Dashboard App!</em></h2>
            <p style="text-align: center;">Our application is designed to help you analyze and visualize your health data effectively. Navigate through the app using the menu on the left.</p>
        """, unsafe_allow_html=True)

    elif st.session_state.page == 'Data Analysis':
        st.markdown("<h2 style='color: #FF5733;'><em>Data Analysis :</em></h2>", unsafe_allow_html=True)

        def load_data(file):
            file_extension = file.name.split(".")[-1].lower()  # Ensure lowercase extension
            if file_extension == "csv":
                data = pd.read_csv(file)
            elif file_extension in ["xls", "xlsx"]:
                data = pd.read_excel(file)
            else:
                st.warning("Unsupported file format. Please upload a CSV or Excel file.")
                return None
            return data

        file = st.file_uploader("Upload your DataSet in CSV or EXCEL format", type=["csv", "xls", "xlsx"])
        if file is not None:
            data = load_data(file)
            if data is not None:
                st.markdown("<h4 style='color: #FF7F50;'><em>Preview of Loaded Dataset :</em></h4>", unsafe_allow_html=True)
                st.dataframe(data.head())
                
                if 'Name' in data.columns:
                    patient_names = data['Name'].unique()
                    selected_name = st.selectbox("Select Patient Name", patient_names)
                    st.write(f"Welcome, {selected_name}!")
                else:
                    st.warning("The dataset does not contain a 'Name' column.")

    elif st.session_state.page == 'Data Visualization':
        st.markdown("<h1 style='color: #FF5733;'><em>Data Visualization :</em></h1>", unsafe_allow_html=True)

        def load_data(file):
            file_extension = file.name.split(".")[-1].lower()  # Ensure lowercase extension
            if file_extension == "csv":
                data = pd.read_csv(file)
            elif file_extension in ["xls", "xlsx"]:
                data = pd.read_excel(file)
            else:
                st.warning("Unsupported file format. Please upload a CSV or Excel file.")
                return None
            return data

        file = st.file_uploader("Upload your DataSet in CSV or EXCEL format", type=["csv", "xls", "xlsx"])
        if file is not None:
            data = load_data(file)
            if data is not None:
                st.markdown("<h2 style='color: #FF5733;'><em>Data Preview</em></h2>", unsafe_allow_html=True)
                st.write(data.head())

                chart_type = st.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Scatter Plot", "Histogram", "Pie Chart"])

                if chart_type in ["Bar Chart", "Line Chart"]:
                    x_column = st.selectbox("Select X Column", data.columns)
                    y_column = st.selectbox("Select Y Column", data.columns)
                elif chart_type == "Scatter Plot":
                    x_column = st.selectbox("Select X Column (Numeric)", data.select_dtypes(include=['int', 'float']).columns)
                    y_column = st.selectbox("Select Y Column (Numeric)", data.select_dtypes(include=['int', 'float']).columns)
                elif chart_type == "Histogram":
                    x_column = st.selectbox("Select Column for Histogram", data.columns)
                elif chart_type == "Pie Chart":
                    x_column = st.selectbox("Select Column for Pie Chart", data.columns)

                fig = None

                if chart_type == "Bar Chart":
                    fig = px.bar(data, x=x_column, y=y_column, title=f"Bar Chart: {y_column} vs {x_column}")
                elif chart_type == "Line Chart":
                    fig = px.line(data, x=x_column, y=y_column, title=f"Line Chart: {y_column} vs {x_column}", width=800, height=600)
                elif chart_type == "Scatter Plot":
                    fig = px.scatter(data, x=x_column, y=y_column, title=f"Scatter Plot: {y_column} vs {x_column}", width=800, height=600)
                elif chart_type == "Histogram":
                    fig = px.histogram(data, x=x_column, title=f"Histogram: {x_column}")
                elif chart_type == "Pie Chart":
                    fig = px.pie(data, names=x_column, title=f"Pie Chart: {x_column}")

                if fig:
                    st.plotly_chart(fig)

    elif st.session_state.page == 'Extractor':
        user_question = st.text_input("Input prompt", key="input")

        st.sidebar.title("Invoice Image")

        uploaded_file = st.sidebar.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])

        image = None
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded image", use_column_width=True)

        prompt = load_prompt()

        if st.button("Send"):
            if image is not None:
                with st.spinner("Start processing..."):
                    response = generate_response_with_retry(input_question=user_question, image=image, prompt=prompt)
                    st.subheader("Response:")
                    st.write(response)

            # Extract table data from response
            df = extract_table_from_response(response)
            # Load and preview the DataFrame
            st.write("Preview of Loaded Dataset:")
            st.dataframe(df)

            if not df.empty:
                st.subheader("Extracted Table Data:")
                st.dataframe(df)

                # Detect language and update headers
                try:
                    detected_language = detect(response)
                    if detected_language == 'fr':
                        headers = ['Nom', 'Paramètre', 'Unité', 'Résultat', 'Valeur']
                    else:
                        headers = ['Name', 'Parameter', 'Unit', 'Result', 'Value']
                except Exception as e:
                    logging.error(f"Error detecting language: {e}")
                    headers = ['Name', 'Parameter', 'Unit', 'Result', 'Value']  # Default to English headers

                if len(headers) == df.shape[1]:  # Ensure headers length matches DataFrame columns
                    df.columns = headers  # Update DataFrame columns with new headers
             

                csv = df.to_csv(index=False)  # Ensure index is not included
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="table_data.csv",
                    mime="text/csv"
                )

                # Prepare PDF download
                pdf_buffer = create_pdf(response)
                st.download_button(
                    label="Download Response as PDF",
                    data=pdf_buffer.getvalue(),
                    file_name="response.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("No table data found in the response.")
    else:
        st.warning("Please upload an image before processing.")

# App initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    main_app()
