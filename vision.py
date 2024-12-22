from dotenv import load_dotenv
import streamlit as st
import os
from PIL import Image
import google.generativeai as genai
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

load_dotenv()  # Load environment variables from .env

# Configure the Google Generative AI API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Gemini model and get responses
def get_gemini_response(input_text, image):
    model = genai.GenerativeModel('gemini-1.5-flash')  # Update with the appropriate model
    if input_text != "":
        response = model.generate_content([input_text, image])
    else:
        response = model.generate_content(image)
    return response.text

# Function to convert extracted data to a PDF
def create_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    styles = getSampleStyleSheet()

    col_widths = [doc.width * 0.3] * len(data[0])  # Adjust according to the number of columns

    response_table = Table(data, colWidths=col_widths)

    response_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))

    story.append(Paragraph("<b>Analysis Report</b>", styles['Title']))
    story.append(response_table)

    doc.build(story)

    buffer.seek(0)
    return buffer

# Initialize Streamlit app
st.set_page_config(page_title="Gemini Image Demo")
st.header("Gemini Application")

# User input and image upload
input_text = st.text_input("Input Prompt: ", key="input")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

image = None
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image.", use_column_width=True)

# Generate and display response
if st.button("Tell me about the image"):
    response = get_gemini_response(input_text, image)
    st.subheader("The Response is")
    st.write(response)

    try:
        # Parse the response to get the table data directly
        response_lines = response.strip().split("\n")
        # Convert response_lines directly to list of lists
        data = [line.split("|") for line in response_lines]  # Adjust based on actual separator

        # Generate PDF and provide download link
        pdf_buffer = create_pdf(data)

        st.download_button(
            label="Download analysis report as PDF",
            data=pdf_buffer,
            file_name="analysis_report.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"An error occurred while generating the analysis report: {e}")
