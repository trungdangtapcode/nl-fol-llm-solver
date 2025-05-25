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
from tqdm import tqdm

def get_embedding(text: str, client: OpenAI, model: str = "text-embedding-004") -> List[float]:
    """Generate embedding for a given text using Gemini's OpenAI-compatible API."""
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding

def embed_and_save_strings(string_list: List[str], api_key: str, output_file: str = "embeddings.joblib") -> List[List[float]]:
    """
    Embed a list of strings using Gemini API and save to a joblib file.
    
    Args:
        string_list: List of strings to embed.
        api_key: Gemini API key.
        output_file: Path to save the embeddings (default: 'embeddings.joblib').
    
    Returns:
        List of embeddings for the input strings.
    """
    # Initialize OpenAI client with Gemini API
    # client = OpenAI(
    #     api_key=api_key,
    #     base_url="https://generativelanguage.googleapis.com/v1beta/"
    # )
    with open('./../clients.json',"r") as f:
        js = json.load(f)
        cli = js[0]
        client = OpenAI(
            api_key=cli["api_key"],
            base_url=cli["base_url"]
        )
    
    # Generate embeddings for all strings
    embeddings = []
    for s in tqdm(string_list, desc="Generating embeddings"):
        embeddings.append(get_embedding(s, client))

    # Save embeddings (and optionally strings) to joblib file
    data = {"strings": string_list, "embeddings": embeddings}
    joblib.dump(data, output_file)
    
    return embeddings

# Example usage
if __name__ == "__main__":
    # Replace with your Gemini API key
    GEMINI_API_KEY = "ABC"
    
    # Example string list
    strings = strs
    
    # Embed strings and save to file
    embeddings = embed_and_save_strings(strings, GEMINI_API_KEY)
    print(f"Embeddings generated and saved to 'embeddings.joblib'")
    print(f"Number of embeddings: {len(embeddings)}")