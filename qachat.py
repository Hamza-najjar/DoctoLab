import openai
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

# Configure OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def qachat(input_text):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=input_text,
        max_tokens=150
    )
    return response.choices[0].text.strip()
