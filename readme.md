# Logical Reasoning API

This API evaluates logical reasoning questions based on provided premises in natural language (NL). It accepts a POST request with premises and questions, processes them to determine valid conclusions, and returns answers, relevant premise indices, and explanations.

## API Endpoint

**Method**: POST  
**URL**: `/evaluate`

## Request Format

The request body is a JSON object containing two fields:
- `premises-NL`: An array of strings representing logical premises in natural language.
- `questions`: An array of strings containing questions to evaluate based on the premises.

### Example Request

```json
{
  "premises-NL": [
    "If a student attends at least 80% of classes, they will be allowed to take the final exam.",
    "If a student is allowed to take the final exam and completes the exam, they can pass the course.",
    "If a student fails to pass the course, they must retake the course.",
    "If a course requires a major assignment, the student must complete the major assignment or take the final exam.",
    "If a student attends less than 50% of classes, they will not be allowed to take the final exam.",
    "If a student completes 3 courses with a score above 8.5, they will receive a scholarship.",
    "If a student takes the exam but scores below the passing threshold, they will not pass the course.",
    "If a student attends all classes but does not complete the exam, they cannot pass the course.",
    "If a student passes 3 required courses, they will graduate.",
    "If a student attends less than 50% of the classes but completes the assignment and gets professor approval, they can take the exam."
  ],
  "questions": [
    "Based on the premises, which conclusion is logically valid?\nA. A student with low attendance, assignment completion, and professor approval can pass the course if they complete the exam.\nB. A student with less than 80% attendance who doesn’t complete the assignment can still take the exam.\nC. A student with 60% attendance and a scholarship automatically passes all courses.\nD. A student who attends every class but doesn’t complete the exam can still pass.",
    "Is it true that a student who completes 3 courses with scores above 8.5 will graduate, according to the premises?"
  ]
}
```

## Response Format

The response is a JSON object containing three fields:
- `answers`: An array of strings representing the answers to the questions (e.g., option letter for multiple-choice or "Yes"/"No" for true/false).
- `idx`: An array of arrays, where each inner array contains the indices of premises used to derive the answer for the corresponding question.
- `explanation`: An array of strings providing detailed explanations for each answer, referencing the relevant premises.

### Example Response

```json
{
  "answers": [
    "A",
    "No"
  ],
  "idx": [
    [
      2,
      10
    ],
    [
      6,
      7,
      9
    ]
  ],
  "explanation": [
    "Premise 10 states that if a student attends less than 50% of the classes but completes the assignment and gets professor approval, they can take the exam. Premise 2 states that if a student is allowed to take the final exam and completes the exam, they can pass the course. Premise 7 states that if a student takes the exam but scores below the passing threshold, they will not pass the course. Therefore, a student with low attendance, assignment completion, and professor approval can pass the course if they complete the exam with a passing score.",
    "Premise 6 states that if a student completes 3 courses with a score above 8.5, they will receive a scholarship. Premise 9 states that if a student passes 3 required courses, they will graduate. The question conflates receiving a scholarship with graduating, but these are separate conditions."
  ]
}
```

## Usage

1. Send a POST request to the `/evaluate` endpoint with a JSON body containing `premises-NL` and `questions`.
2. The API processes the premises and questions to determine logically valid conclusions.
3. The response includes the answers, indices of relevant premises, and explanations for each question.

## Notes

- Premises should be clear, logical statements in natural language.
- Questions can be multiple-choice (with options labeled A, B, C, etc.) or true/false.
- The API assumes premises are consistent and sufficient to answer the questions.
- Ex

# Project Setup and Configuration

## Configuration Files

### `clients.json`
```json
[
  {
    "api_key": "<your_key>",
    "base_url": "<your_url>",
    "model": "<your_model>"
  }
]
```

### `.env`
```plaintext
API_AUTH_TOKEN=-1
TIMEOUT_LIMIT=50
RANDOM_REQUESTS_SLEEP=2
```

### `nodes.json`
```json
[
  {
    "url": "http://<your_sub_url>:<some_port>/query"
  }
]
```

## Installation and Running Servers

### Install Dependencies
```bash
pip install -e .
```

### Run Uvicorn Servers
#### Individual Nodes
```bash
uvicorn main:app --host 0.0.0.0 --port <some_port> --reload
```

#### Main Application
```bash
uvicorn async_main:app --host 0.0.0.0 --port <main_port> --reload
```

### Example Setup
#### Running Multiple Nodes
```bash
pip install -e .
uvicorn main:app --host 0.0.0.0 --port 81 --reload
uvicorn main:app --host 0.0.0.0 --port 82 --reload
uvicorn main:app --host 0.0.0.0 --port 83 --reload
uvicorn main:app --host 0.0.0.0 --port 84 --reload
uvicorn async_main:app --host 0.0.0.0 --port 80 --reload
```

#### Corresponding `nodes.json`
```json
[
  {"url": "http://127.0.0.1:81/query"},
  {"url": "http://127.0.0.1:82/query"},
  {"url": "http://127.0.0.1:83/query"},
  {"url": "http://127.0.0.1:84/query"}
]
```

## VS Code Integration
### Set `nodes.json`
```json
[
  {"url": "http://127.0.0.1:81/query"},
  {"url": "http://127.0.0.1:82/query"},
  {"url": "http://127.0.0.1:83/query"},
  {"url": "http://127.0.0.1:84/query"},
  {"url": "http://127.0.0.1:85/query"},
  {"url": "http://127.0.0.1:86/query"},
  {"url": "http://127.0.0.1:87/query"},
  {"url": "http://127.0.0.1:88/query"},
  {"url": "http://127.0.0.1:89/query"},
  {"url": "http://127.0.0.1:90/query"},
  {"url": "http://127.0.0.1:91/query"},
  {"url": "http://127.0.0.1:92/query"}
]
```

### Running Servers
1. Open Terminal in VS Code
2. Select `Run Task...`
3. Choose `Run uvicorn server`
4. Run `uvicorn async_main:app --host 0.0.0.0 --port 80 --reload`

### Stopping Servers
1. Open Terminal in VS Code
2. Select `Run Task...`
3. Choose `Stop uvicorn server`

## Ngrok Integration
```bash
ngrok tunnel --label edge=<your_edge> http://localhost:80
```