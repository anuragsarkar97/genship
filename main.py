# write fast api code which takes whatsapp webhook
# and sends message to the user
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from starlette.responses import PlainTextResponse
import whatsapp
from core import process_message
from promts import RESPONSE_GENERATION_SYSTEM_PROMPT
from tuneai import get_llm_response
from fastapi import BackgroundTasks

print("starting connection ....... ")
database = file = open('database.txt', 'r+')


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # close database connection
    print("closing connection ....... ")
    for w in history:
        database.write(w + '\n')
    database.close()


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8082",

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

history = []


class MessageTemplate(BaseModel):
    templateId: str
    lang: str


class Message(BaseModel):
    message: str


def write_into_database(type_, message):
    history.append(type_ + " " + message)


def get_history():
    key = {"USER": "USER", "ASSI": "ASSISTANT"}
    return [[key[d[:4]], d[5:]] for d in history]


@app.post("/send_message")
async def send_message2(message: Message):
    result = await whatsapp.send_message2(message)
    return JSONResponse(content=result)


@app.get("/webhook")
async def webhook(request: Request):
    response = await whatsapp.webhook(request.query_params['hub.verify_token'], request.query_params['hub.challenge'],
                                      request.query_params['hub.mode'])
    return PlainTextResponse(response)


def process(body):
    try:
        # body = request.json()
        if 'contacts' not in body['entry'][0]['changes'][0]['value']:
            print('not user message')
            return
        print('user message', body['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'])
        message = body['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
        response = process_message(message, get_history())
        whatsapp.send_message2(Message(message=response))
        write_into_database('USER', message)
        write_into_database('ASSI', response)
        return {}
    except Exception as e:
        print(e)
        # whatsapp.send_message2(Message(message="Seems like I cannot process this message at the moment"))
        return {}


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        background_tasks.add_task(process, body)
        return JSONResponse({}, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse({}, status_code=200)


@app.get("/tesst")
async def test():
    import cohere
    co = cohere.Client('ACkNOOGu5ukthcUA6tyT7QjMMKyn9iNxfuB7RYgd')
    query = 'What is the capital of the United States?'
    docs = ['Carson City is the capital city of the American state of Nevada.',
            'The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.',
            'Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district. ',
            'Capital punishment (the death penalty) has existed in the United States since before the United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states.'
            ]
    results = co.rerank(query=query, documents=docs, top_n=3, model='rerank-english-v3.0')
    return results


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Run the code using the command
# uvicorn main:app --reload
