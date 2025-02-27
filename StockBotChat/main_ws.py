from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv

load_dotenv()
# Access the OpenAI API key
openai_api_key = os.getenv('OPENAI_API_KEY')
openai_model = os.getenv('OPENAI_MODEL')
openai = OpenAI(api_key=openai_api_key)

app = FastAPI()
templates = Jinja2Templates(directory="html_sockets")

chat_responses = []

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})

chat_log = [{'role': 'system',
             'content': 'You are a Stock Specialist'
             }]

@app.websocket("/ws")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_input = await websocket.receive_text()
        chat_log.append({'role': 'user', 'content': user_input})
        chat_responses.append(user_input)
        try:
            response = openai.chat.completions.create(
                model=openai_model,
                messages=chat_log,
                temperature=0.6,
                stream=True
            )
            ai_response = ''
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    ai_response += chunk.choices[0].delta.content
                    #print("resp",chunk.choices[0].delta.content)
                    #chat_responses.append(ai_response)
                    await websocket.send_text(chunk.choices[0].delta.content)
            chat_responses.append(ai_response)
        except Exception as e:
            await websocket.send_text(f'Error: {str(e)}')
            break














