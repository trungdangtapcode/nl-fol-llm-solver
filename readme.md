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