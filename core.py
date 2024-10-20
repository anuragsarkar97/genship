import json

import whatsapp
from hf import generate_embed
from promts import RESPONSE_GENERATION_SYSTEM_PROMPT, MASTER_ROUTER_SYSTEM_PROMPT, SMALL_TALK_SYSTEM_PROMPT, \
    FOLLOW_UP_SYSTEM_PROMPT
from qdrant import fetch_results, rerank
from tuneai import get_llm_response
import re
from threading import Thread


def identify_json_in_gpt_response(response_content):
    pattern = r'\{.*\}'
    response_content = response_content.replace('\n', '')
    match = re.search(pattern, response_content)
    return match


def process_query(message, history):
    # history = []
    result = get_llm_response(MASTER_ROUTER_SYSTEM_PROMPT, message, history)
    result = json.loads(identify_json_in_gpt_response(result).group())
    selected = result['output'][0]['tool']
    if selected == "search-product-tool":
        query = result['output'][0]['query']
        filters = result['output'][0]['filters']
        print(query, filters)
        return [query, filters, "NEXT"]
    elif selected == "small_talk_tool":
        print("small talk")
        result = get_llm_response(SMALL_TALK_SYSTEM_PROMPT, message, [])
        return [result, None, "END"]
    elif selected == "follow_up_question_tool":
        result = get_llm_response(FOLLOW_UP_SYSTEM_PROMPT, message, history)
        return [result, None, "END"]
    return [message, None, "NEXT"]


def find_products(messages, filters):
    results = []
    for message in messages:
        embedding = generate_embed(message)
        result = rerank(message, fetch_results(embedding, filters))
        results.extend([filter_json(x) for x in result])
    print(results)
    return results


def filter_json(data):
    try:
        data.pop('image')
        data.pop('link')
        data.pop('name_embedding')
    except Exception as e:
        pass
    return data


def build_response(results):
    threads = []
    x = []
    for r in results:
        p = Thread(target=call_llm, args=(RESPONSE_GENERATION_SYSTEM_PROMPT, json.dumps(r), [], x))
        p.start()
        threads.append(p)
    for process in threads:
        process.join()
    return '\n\n\n'.join(x)


def build_response2(results):
    content = ""
    for r in results:
        content += get_llm_response(RESPONSE_GENERATION_SYSTEM_PROMPT, json.dumps(r), [])
        content += "\n\n\n"
    return content


def call_llm(system, data, history, result):
    result.append(get_llm_response(system, data, history))


def process_message(message: str, history: [[str, str]]):
    print(f"process {message} with history {history}")
    context = process_query(message, history)
    if context[2] == "END":
        return context[0]
    result = find_products([context[0]], context[1])
    return build_response(result)
