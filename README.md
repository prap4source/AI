============ StockChatBot  ===========================
For Developing StockChatBot follow these steps

1) Create account in OpenAI API https://platform.openai.com/
2) Create API-KEY under https://platform.openai.com/settings/organization/api-keys
3) SAVE API-KEY, lets call it OPENAI_API_KEY
4) Download Python editor, i used PyCharmCE
5) Install Packages using 
#pip install -r requirements.txt
5) Download github sources
6) Under AI directory create .env file
**#Create .env with OPENAI KEY AND MODEL**
OPENAI_API_KEY='<Your openAI Key>'
OPENAI_MODEL='<model to use gpt-4o-mini etc'
7) In Pycharm terminal run the app
  a) For running Non-Websockets Chatbot
#cd StockBotChat
#uvicorn --reload main:app 
Openbrowser http://127.0.0.1/8080
  b) For running Non-Websockets Chatbot
#cd StockBotChat
#uvicorn --reload main_ws:app 
Openbrowser http://127.0.0.1/8080



 
