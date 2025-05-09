from typing import Union

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional

from dotenv import dotenv_values

from nl_solving import solving_fol

from timeout import *

config = dotenv_values(".env")
app = FastAPI()
API_AUTH_TOKEN = config["API_AUTH_TOKEN"]
TIMEOUT_LIMIT = config["TIMEOUT_LIMIT"]

class QueryRequest(BaseModel):
    premises: List[str] = Field(..., alias="premises-NL")
    questions: List[str]

class QueryResponseItem(BaseModel):
    answers: List[str]
    idx: List[List[int]]
    explanation: List[str]

@app.post("/query", response_model=QueryResponseItem)
async def query(request: QueryRequest, authorization: Optional[str] = Header(None)):
    if API_AUTH_TOKEN!="-1" and authorization != f"Bearer {API_AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized. Invalid or missing token.")

    start_time = get_current_time()

    try:
        inputs = {
			"premises-NL": request.premises,
			"questions": request.questions
		}
        result = solving_fol(inputs, start_time)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}