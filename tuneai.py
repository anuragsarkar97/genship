import json
import textwrap

import requests

from keys import TUNE_API_TOKEN

stream = False
url = "https://proxy.tune.app/chat/completions"
headers = {
    "Authorization": TUNE_API_TOKEN,
    "Content-Type": "application/json",
}


def get_llm_response(system, query, history):
    qq = [
        {
            "role": "system",
            "content": system
        }
    ]
    for i in range(len(history)):
        qq.append({
            "role": history[i][0],
            "content": history[i][1]
        })
    qq.append({
        "role": "user",
        "content": query
    })
    data = {
        "temperature": 0.8,
        "messages": qq,
        "model": "meta/llama-3.1-405b-instruct",
        "stream": stream,
        "frequency_penalty": 0,
        "max_tokens": 4096
    }

    response = requests.post(url, headers=headers, json=data)
    if stream:
        for line in response.iter_lines():
            if line:
                l = line[6:]
                if l != b'[DONE]':
                    return json.loads(l)['choices'][0]['message']['content']
    else:
        print(response.json())
    return response.json()['choices'][0]['message']['content']
