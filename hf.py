import os
import torch
from transformers import AutoModel, AutoTokenizer, AutoConfig
from sklearn.preprocessing import normalize

model_dir = "Marqo/dunzhang-stella_en_400M_v5"
model = AutoModel.from_pretrained(model_dir, trust_remote_code=True).eval()
tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
query_prompt = "Instruct: Given a web search query, retrieve relevant passages that answer the query.\nQuery: "


def calculate_embeddings(doc):
    with torch.no_grad():
        input_data = tokenizer(doc, padding="longest", truncation=True, max_length=512, return_tensors="pt")
        input_data = {k: v for k, v in input_data.items()}
        attention_mask = input_data["attention_mask"]
        last_hidden_state = model(**input_data)[0]
        last_hidden = last_hidden_state.masked_fill(~attention_mask[..., None].bool(), 0.0)
        query_vectors = last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]
        query_vectors = normalize(query_vectors.cpu().numpy())
    return query_vectors


def generate_embed(doc):
    return calculate_embeddings(query_prompt + doc).tolist()[0]
