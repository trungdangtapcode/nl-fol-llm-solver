from typing import Union

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional

from dotenv import dotenv_values

from timeout import *
import random

import asyncio

config = dotenv_values(".env")
app = FastAPI()
API_AUTH_TOKEN = config["API_AUTH_TOKEN"]
TIMEOUT_LIMIT = float(config["TIMEOUT_LIMIT"])
RANDOM_REQUESTS_SLEEP = float(config["RANDOM_REQUESTS_SLEEP"])

class QueryRequest(BaseModel):
    premises: List[str] = Field(..., alias="premises-NL")
    questions: List[str]

class QueryResponseItem(BaseModel):
    answers: List[str]
    idx: List[List[int]]
    explanation: List[str]


import requests
import json

current_url = ""
current_url_idx = -1
nodes = []
def init_nodes():
    global nodes, current_url, current_url_idx

    with open('nodes.json', 'r') as f:
        nodes = json.load(f)   

    assert len(nodes) > 0, "No nodes found in nodes.json"

    current_url_idx = 0
    current_url = nodes[current_url_idx]["url"]

init_nodes()

def step_change_node():
	global nodes, current_url, current_url_idx
	n = len(nodes)
	current_url_idx = (current_url_idx+1)%n
	current_url = nodes[current_url_idx]["url"]
	print("Current URL:", current_url)

def solving_fol(input_problem, time_start):
    time.sleep(random.uniform(0, RANDOM_REQUESTS_SLEEP))
    global current_url
    print('solving_fol (async current question):', input_problem['questions'])
    # print("Current URL:", current_url)
    headers = {
        'Content-Type': 'application/json'
    }
    data = json.dumps(input_problem)
    step_change_node()
    response = requests.post(current_url, headers=headers, data=data, timeout=TIMEOUT_LIMIT)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")
    
async def main_solving(inputs, start_time):
    premises_nl = inputs["premises-NL"]
    questions = inputs["questions"]

    responses = {
        "answers": [],
        "idx": [],
        "explanation": []
    }

    loop = asyncio.get_event_loop()
    tasks = [] 
    for question in questions:
        input_problem = {
            "premises-NL": premises_nl,
            "questions": [question]
        }
        # task = asyncio.create_task(solving_fol(input_problem, start_time))
        task = loop.run_in_executor(None, solving_fol, input_problem, start_time)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    for result in results:
        if isinstance(result, dict):
            responses["answers"].append(result["answers"][0])
            responses["idx"].append(result["idx"][0])
            responses["explanation"].append(result["explanation"][0])
        else:
            raise ValueError("Invalid result format")

    return responses


@app.post("/query", response_model=QueryResponseItem)
async def query(request: QueryRequest, authorization: Optional[str] = Header(None)):
    if API_AUTH_TOKEN!="-1" and authorization != f"Bearer {API_AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized. Invalid or missing token.")
    start_time = get_current_time()
    # test()
    NOTHING_RETURN = {
        "answers": ["Nothing"],
        "idx": [],
        "explanation": ["Nothing"]
    }
    # return NOTHING_RETURN

    try:
        inputs = {
			"premises-NL": request.premises,
			"questions": request.questions
		}
        result = await main_solving(inputs, start_time)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    init_nodes()