import json 

with open("./../train_v1.json", "r", encoding='utf-8') as f:
    train_data = json.load(f)

def to_string(data):
    str_datas = []
    for item in data:
        del item['premises-FOL']
        cur_string = json.dumps(item, ensure_ascii=False)
        str_datas.append(cur_string)
    return str_datas

strs = to_string(train_data)

import joblib
from openai import OpenAI
from typing import List
import numpy as np
import os
THIS_CODE_PATH = os.path.dirname(os.path.abspath(__file__))
embedded = joblib.load(f"{THIS_CODE_PATH}/embeddings.joblib")

with open('./../clients.json',"r") as f:
    js = json.load(f)
    cli = js[0]
    client = OpenAI(
        api_key=cli["api_key"],
        base_url=cli["base_url"]
    )

def get_embedding(text: str, model: str = "text-embedding-004") -> List[float]:
    """Generate embedding for a given text using Gemini's OpenAI-compatible API."""
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding
def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

def get_closest_strings(inputdict, top_k=1):
    similarities = []
    embedding = get_embedding(inputdict)

    for i, emb in enumerate(embedded["embeddings"]):
        similarity = cosine_similarity(embedding, emb)
        similarities.append((i, similarity))

    # Sort by similarity and get top_k indices
    similarities.sort(key=lambda x: x[1], reverse=True)
    closest_indices = [idx for idx, _ in similarities[:top_k]]

    return_strings = []
    for i in closest_indices:
        return_strings.append(embedded["strings"][i])  
    
    return return_strings

# idx = 3
# tmp = train_data[idx]
# print(tmp)
# tmp.pop("idx")
# tmp.pop("explanation")
# tmp.pop("answers")
# # print(tmp)
# # tmp.pop("premises-FOL")


# print(get_closest_strings(json.dumps(tmp)))