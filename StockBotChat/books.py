from fastapi import FastAPI
BOOKS = {
    'book1' : {'title' : 'One','Author': 'Pradeep ', 'category':'fiction'},
    'book2' : {'title' : 'One','Author': 'Risheeth','category':'science'},
    'book3' : {'title' : 'One','Author': 'Ramya','category':'Dotnet'},
}
app = FastAPI()
@app.get("/api-endpoint")
async def first_api():
    return {'message': 'Your First website'}
@app.get("/readbooks")
async def read_all_books():
    return BOOKS