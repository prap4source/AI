from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
# Access the OpenAI API key
openai_api_key = os.getenv('OPENAI_API_KEY')
openai_model = os.getenv('OPENAI_MODEL')
openai = OpenAI(api_key=openai_api_key)
response = openai.chat.completions.create(
  model=openai_model,
  messages=[
    {
      "role": "system",
      "content": "You a Stock Analyst"
    },
    {
      "role": "user",
      "content": "Who is the CEO of APPLE"
    }
  ],
  temperature=0.8,
  max_tokens=256,
  top_p=1
)
print(response)