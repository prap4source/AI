import google.generativeai as genai
from fastapi import FastAPI, Form, Request, WebSocket
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Access the Gemini API key
gemini_api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=gemini_api_key)

model = genai.GenerativeModel('gemini-1.5-pro-latest')
image_model = genai.GenerativeModel('gemini-pro-vision')

app = FastAPI()
templates = Jinja2Templates(directory="html_sockets")

chat_responses = []

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})

#chat_log = [{'role': 'user', 'parts': ["You are a Stock Specialist. Answer all questions related to stocks." ]}]
chat_log = []
@app.websocket("/ws")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_input = await websocket.receive_text()
        chat_log.append({'role': 'user', 'parts': [user_input]})
        chat_responses.append(user_input)
        try:
            response = model.generate_content(
                chat_log,
                stream=True,
                generation_config=genai.types.GenerationConfig(temperature=0.6)
            )
            ai_response = ''
            for chunk in response:
                if chunk.text:
                    ai_response += chunk.text
                    await websocket.send_text(chunk.text)
            chat_responses.append(ai_response)
        except Exception as e:
            await websocket.send_text(f'Error: {str(e)}')
            break

@app.get("/image", response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse("image.html", {"request": request})

@app.post("/image", response_class=HTMLResponse)
async def create_image(request: Request, user_input: Annotated[str, Form()]):
    try:
        response = image_model.generate_content(
            user_input,
            generation_config=genai.types.GenerationConfig(temperature=0.9)
        )

        if response.parts:
            #gemini returns parts, not a direct url like openai.
            image_url = response.parts[0].inline_data.data # base64 encoded image data
            mime_type = response.parts[0].inline_data.mime_type
            image_data_url = f"data:{mime_type};base64,{image_url}"

            return templates.TemplateResponse("image.html", {"request": request, "image_url": image_data_url})
        else:
            return templates.TemplateResponse("image.html", {"request": request, "error": "Image generation failed."})

    except Exception as e:
        return templates.TemplateResponse("image.html", {"request": request, "error": f"Error: {e}"})