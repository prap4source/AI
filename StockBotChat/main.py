from openai import OpenAI
from fastapi import FastAPI, Form, Request
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from mangum import Mangum
import os
from dotenv import load_dotenv

load_dotenv()
# Access the OpenAI API key
openai_api_key = os.getenv('OPENAI_API_KEY')
openai_model = os.getenv('OPENAI_MODEL')
openai = OpenAI(api_key=openai_api_key)

app = FastAPI()
handler = Mangum(app)
templates = Jinja2Templates(directory="templates")

chat_responses = []

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    print("GETTING CHAT PAGE")
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})

chat_log = [{'role': 'system',
             'content': 'You are a Specialist in Stocks, options, investments. High expertise knowledge of Trading'
             }]

@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    #print("Chat log", chat_log)
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = openai.chat.completions.create(
        model=openai_model,
        messages=chat_log,
        temperature=0.6
    )
    bot_response = response.choices[0].message.content
    #print("Response", bot_response)
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})

@app.get("/image", response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse("image.html", {"request": request})


@app.post("/image", response_class=HTMLResponse)
async def create_image(request: Request, user_input: Annotated[str, Form()]):

    response = openai.images.generate(
        prompt=user_input,
        n=1,
        size="512x512"
    )

    image_url = response.data[0].url
    return templates.TemplateResponse("image.html", {"request": request, "image_url": image_url})














