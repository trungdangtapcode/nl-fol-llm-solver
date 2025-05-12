import random
from typing import Union

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional

from dotenv import dotenv_values

from nl_solving import solving_fol

from timeout import *

import asyncio

config = dotenv_values(".env")
app = FastAPI()
API_AUTH_TOKEN = config["API_AUTH_TOKEN"]
TIMEOUT_LIMIT = config["TIMEOUT_LIMIT"]
RANDOM_MAIN_SLEEP = float(config["RANDOM_MAIN_SLEEP"])

class QueryRequest(BaseModel):
    premises: List[str] = Field(..., alias="premises-NL")
    questions: List[str]

class QueryResponseItem(BaseModel):
    answers: List[str]
    idx: List[List[int]]
    explanation: List[str]


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



#===================================================================
def func(arg):
    print('start')
    try:
        arg //= 0
        raise ValueError("ZeroDivisionError")
    except Exception as e:
        arg = -arg
        pass

    import time
    time.sleep(1)

    return arg

async def test():
    tasks = []
    loop = asyncio.get_event_loop()
    for i in range(1, 20):
        # Run synchronous func in executor since it's not a coroutine
        task = loop.run_in_executor(None, func, i)
        tasks.append(task)
    res = await asyncio.gather(*tasks)
    return res

@app.post("/test")
async def atest():
    res = await test()
    return res
#===================================================================

@app.post("/query", response_model=QueryResponseItem)
async def query(request: QueryRequest, authorization: Optional[str] = Header(None)):
    if API_AUTH_TOKEN!="-1" and authorization != f"Bearer {API_AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized. Invalid or missing token.")
    start_time = get_current_time()
    # delay for 1 second
    await asyncio.sleep(random.uniform(0, RANDOM_MAIN_SLEEP))

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


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}