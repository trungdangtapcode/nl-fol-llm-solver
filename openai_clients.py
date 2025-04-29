from openai import OpenAI
import json

clients = []
model_names = []
client = None
model_name = None
client_idx = 0

def load_clients():
    global clients, model_names
    with open('clients.json',"r") as f:
        js = json.load(f)
        for cli in js:
            openai_client = OpenAI(
                api_key=cli["api_key"],
                base_url=cli["base_url"]
            )
            model = cli["model"]
            clients.append(openai_client)
            model_names.append(model)
    global client, model_name
    client = clients[0]
    model_name = model_names[0]

def step_change_client():
    global clients, model_names, client, model_name, client_idx

    n = len(clients)
    client_idx = (client_idx+1)%n
    client = clients[client_idx]
    model_name = model_names[client_idx]

load_clients()