from typing import Union

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional

from dotenv import dotenv_values

from nl_solving import solving_fol

config = dotenv_values(".env")
app = FastAPI()
API_AUTH_TOKEN = config["API_AUTH_TOKEN"]


class QueryRequest(BaseModel):
    premises: List[str] = Field(..., alias="premises-NL")
    questions: List[str]

class QueryResponseItem(BaseModel):
    answer: List[str]
    idx: List[List[int]]
    explanation: List[str]

@app.post("/query", response_model=QueryResponseItem)
async def query(request: QueryRequest, authorization: Optional[str] = Header(None)):
    if API_AUTH_TOKEN!="-1" and authorization != f"Bearer {API_AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized. Invalid or missing token.")

    try:
        inputs = {
			"premises-NL": request.premises,
			"questions": request.questions
		}
        result = solving_fol(inputs)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}