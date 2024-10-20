import requests
from pydantic import BaseModel

from keys import WHATSAPP_API_TOKEN


class MessageTemplate(BaseModel):
    templateId: str
    lang: str


class Message(BaseModel):
    message: str


url = "https://graph.facebook.com/v20.0/381843911689746/messages"

headers = {
    'Authorization': 'Bearer ' + WHATSAPP_API_TOKEN,
    'Content-Type': 'application/json'}


def send_message2(message: Message):
    data = {"messaging_product": "whatsapp",
            "to": "919790031200",
            "type": "text",
            "text": {
                "body": message.message
            }
            }
    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    return response.json()


async def webhook(verify_token: str, challenge: str, mode: str):
    return challenge
