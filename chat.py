from dotenv import load_dotenv
import openai
import os

load_dotenv()  # Load environment variables from .env

# Configure OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def chat_with_openai(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()
