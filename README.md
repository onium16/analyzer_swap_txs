### 📘 Available in other languages:
- 🇷🇺 [Читать на русском](README.ru.md)

## Transaction Analyzer

(!Automatic deployment of Docker Compose services)

A multi-service solution for transaction analysis. Demonstrates interaction between services (Docker containers) using REST API (FastAPI), background tasks (Celery), caching (Redis), and a database (PostgreSQL).

### Main Functionality:
- Accepts a number of blocks or a range by block number for parsing.
- Collects transaction data.
- Filters to keep only swaps for Uniswap V2 and Uniswap V3.
- Decodes input data.
- Stores data in Redis and PostgreSQL (automatically creates a test server with a database named `analyzer` and a table named `swap_txs`).

### Additional Features:
Allows:
- Retrieving data by transaction hash.
- Retrieving transaction data by block number.
- Retrieving task status data.
- Returning a list of tasks with their status and results.
- Checking the status of the Redis service (cache) and PostgreSQL (database), which is necessary for scaling.

|| The project uses parallel ports by default (+1 from standard to avoid conflicts between containers).

## Key Project Features

- Works with **multiple nodes**, controls load distribution between them, and allocates a free node for operation.
- Supports **multiple workers**, controls load distribution between them, and allocates a free worker for operation.
- Enables **long-running transaction processing** in the background to avoid blocking the main process.
- Allows running workers in parallel mode on different machines to increase transaction processing speed.
- Workers have access to **Redis** for caching data, exchanging messages, node status data, worker status data, and fast access to up-to-date information with TTL.
- Uses **PostgreSQL** as a permanent storage for transaction data.
- Parses **transactions** using **RPC** by querying nodes.
- In the basic version, parses Uniswap V2 and V3 swap transactions, decoding input using **ABI**.
- Implements two load **balancers**:
  - First layer (analysis): Celery distributes load between nodes, processing requests and caching responses in Redis.
  - Second layer (queries): Celery distributes database queries, caching in Redis.

## Technologies Used

- [Docker](https://www.docker.com/) — containerization
- [FastAPI](https://fastapi.tiangolo.com/) — framework for creating REST API
- [Celery](https://docs.celeryq.dev/en/stable/) — asynchronous background task processing
- [Redis](https://redis.io/) — caching system and message broker
- [PostgreSQL](https://www.postgresql.org/) — relational database
- [Flower](https://flower.readthedocs.io/en/stable/) — Redis data visualization

## Usage Guide

1. Install [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/install/).

2. Project Setup
   2.1. Create a directory and virtual environment:
    - Create a new directory for the project:
     ```bash
    mkdir NewProject
     ```
    - Navigate to the project directory:
     ```bash
    cd NewProject
     ```
    - Create and activate a virtual environment: For Linux/MacOS:
     ```bash
    python -m venv venv  # Create a virtual environment
    source venv/bin/activate  # Activate the environment
     ```
     For Windows:
     ```bash
    python -m venv venv  # Create a virtual environment
    venv\Scripts\activate  # Activate the environment
     ```

   2.2. Clone the repository:
    - Clone the repository:
     ```bash
    git clone https://github.com/onium16/analyzer_swap_txs.git
     ```

3. Create two files: `.env` and `docker/.env`:

.env:
```bash 
REDIS_URL=redis://localhost:6380/0
CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/0
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=analyzer
POSTGRES_TABLE_SWAP=swap_txs
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5433/analyzer
LOG_LEVEL=DEBUG
INFURA_KEY=test
```
docker/.env:
```bash
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=analyzer
POSTGRES_TABLE_SWAP=swap_txs
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/analyzer
LOG_LEVEL=DEBUG
INFURA_KEY=test
```

4.Start the containers:
    
Option I:
4.1. Navigate to the project directory and run one of the necessary commands:

```bash
make up      # Start containers
make down    # Stop containers
make logs    # View logs
make restart # Restart
```
4.2. Wait until the containers are started:

```bash
docker ps -a
```
or

```bash
docker compose -f docker/docker_compose.yml -p test_pool ps
```

Option II:
4.1. Navigate to the project directory and run the command:
```bash
docker compose -f docker/docker_compose.yml -p test_pool up --build -d
```
4.2. Wait until the containers are started:

```bash
docker ps -a
```
or

```bash
docker compose -f docker/docker_compose.yml -p test_pool ps
```
Example:
```bash
CONTAINER ID   IMAGE                          COMMAND                   CREATED        STATUS                  PORTS                                                                                                                                                                                                            NAMES
e2d5935bcf3a   test_pool-flower               "celery -A tasks.ana…"    11 hours ago   Up 11 hours             0.0.0.0:5556->5555/tcp, [::]:5556->5555/tcp                                                                                                                                                                      test_pool-flower-1
042d044cff8c   test_pool-celery_worker        "celery -A tasks.ana…"    11 hours ago   Up 11 hours                                                                                                                                                                                                                              test_pool-celery_worker-1
315c2dc185db   test_pool-api                  "uvicorn api.main:ap…"    11 hours ago   Up 11 hours             0.0.0.0:8001->8000/tcp, [::]:8001->8000/tcp                                                                                                                                                                      test_pool-api-1
88b02d802ced   redis:6                        "docker-entrypoint.s…"    23 hours ago   Up 11 hours (healthy)   0.0.0.0:6380->6379/tcp, [::]:6380->6379/tcp                                                                                                                                                                      test_pool-redis-1
d7d5a1b73f07   postgres:13                    "docker-entrypoint.s…"    23 hours ago   Up 11 hours (healthy)   0.0.0.0:5433->5432/tcp, [::]:5433->5432/tcp                                                                                                                                                                      test_pool-db-1
```
4.3. Navigate to the project directory and run:
```bash
docker compose -f docker/docker_compose.yml -p test_pool ps
```
4.4. Verify that all containers are running:
```bash
docker compose -f docker/docker_compose.yml -p test_pool logs
```
5. To work with the project, use FastAPI Docs.
6. To visualize Celery + Redis operations, use Flower.
7. After finishing work with the project, remove all volumes, builds, networks, and the database:
```bash
docker compose -f docker/docker_compose.yml -p test_pool down --volumes --rmi all
```

### Port List

```bash
host: 127.0.0.1 or localhost

SERVICE     PORT_CUSTOM     PORT_DEFAULT
FastAPI:    8001            8000
Celery:     -           
Redis:      6380            6379
PostgreSQL: 5433            5432
Flower:     5556            5555
```

Example:
```bash
http://localhost:8001
```
Check if ports [8001, 6380, 5433, 5556] are free:
```bash
sudo lsof -i :8001
```

### Using

#### Check Redis Status

```bash
redis-cli -h localhost -p 6380
```
```bash
redis-cli -h redis -p 6380 ping # returns PONG
```

#### Start Retrieving Swap Transaction Data, Analysis, and Saving to Database (Specifying Block Depth, e.g., 1) 
**Request to API:** 

```bash
 curl -X 'POST' \ 'http://localhost:8001/analyze/blocks' \ -H 'accept: 
application/json' \ -H 'Content-Type: 
application/json' \ -d '{ "depth_blocks": 
1 }' 
``` 

**Response:** 
```json 
{"task_id":"11e897b9-a5af-42a9-82ae-739c602b1473","status":"Task started"} 
``` 

#### Start Retrieving Swap Transaction Data, Analysis, and Saving to Database (Specifying Block Range, e.g., 22324710 to 22324712)

**Request to API:** 
```bash
 curl -X 'POST' \ 'http://localhost:8001/analyze/block-range' \ -H 'accept: 
application/json' \ -H 'Content-Type: 
application/json' \ -d '{ "start_block": 
22324710, "end_block": 
22324712 }' 
``` 
**Response:** 
```json 
{"task_id":"a8a1d944-fdc7-4896-9707-b876438d1567","status":"Task started"} 
``` 

#### Retrieve Swap Transaction Data by Transaction Hash 
**Request to API:** 
```bash
 curl -X 'GET' \ 'http://localhost:8001/data/transaction/0x5bdc2ef4af09142f3999aa9e5af9384855fc5071cab1a4b6ba02dc48afa80b85' \ -H 'accept: 
application/json' 
``` 
**Response:** 
```json 
{"task_id":"a8a1d944-fdc7-4896-9707-b876438d1567","status":"Task started"} 
``` 

#### Retrieve Swap Transaction Data, Analysis, and Saving to Database (Specifying Block Range, e.g., 22324710 to 22324712) 
**Request to API:** 
```bash
curl -X 'POST' \
  'http://localhost:8001/analyze/block-range' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "start_block": 22324710,
  "end_block": 22324712
}'
``` 
**Response:** 
```json 
{
  "status": "completed",
  "transaction": {
    "tx_hash": "0x5bdc2ef4af09142f3999aa9e5af9384855fc5071cab1a4b6ba02dc48afa80b85",
    "block_number": 22328461,
    "decoded_input": {
      "method": "swapExactETHForTokens",
      "params": {
        "to": "0x03b7a339e9c2c36b2cf14a8cb7ebc522dd111e18",
        "path": [
          "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
          "0xe0805c80588913c1c2c89ea4a8dcf485d4038a3e"
        ],
        "deadline": 1745373207,
        "amountOutMin": 0
      }
    }
  }
}
``` 

#### Check Task Status 
**Request to API:** 
```bash
curl -X 'GET' \
  'http://localhost:8001/tasks/status/a288c77e-5cc4-47d1-a54a-c3230928d8da' \
  -H 'accept: application/json'
``` 
**Response:** 
```json 
{
  "task_id": "a288c77e-5cc4-47d1-a54a-c3230928d8da",
  "status": "completed",
  "result": {
    "status": "completed",
    "tx_hashes": [
      "0x5bdc2ef4af09142f3999aa9e5af9384855fc5071cab1a4b6ba02dc48afa80b85"
    ],
    "count": 1,
    "save_task_id": "0995768a-35e2-4b79-8cdd-3e31e7ac1a30"
  }
}
``` 

#### Retrieve a Range of Tasks 
**Request to API:** 
```bash
curl -X 'GET' \
  'http://localhost:8001/tasks/all?start=0&end=100' \
  -H 'accept: application/json'
``` 
**Response:** 
```json 
{
  "tasks": [
    {
      "task_id": "a288c77e-5cc4-47d1-a54a-c3230928d8da",
      "state": "SUCCESS",
      "status": "SUCCESS",
      "result": "{'status': 'completed', 'tx_hashes': ['0x5bdc2ef4af09142f3999aa9e5af9384855fc5071cab1a4b6ba02dc48afa80b85'], 'count': 1, 'save_task_id': '0995768a-35e2-4b79-8cdd-3e31e7ac1a30'}"
    },
    {
      "task_id": "c6742074-bf82-40e4-b926-b0638c7944e5",
      "state": "SUCCESS",
      "status": "SUCCESS",
      "result": "{'status': 'completed', 'tx_hashes': ['0x1c82d2d1b380e764ab3ab7df5b340a32078d76d5959a3d9d3b65ee9ac5fbc2a6', '0xa454eda9dded2a2d489963d6fa4c239f64c5162538567e7cfc2952dbc1386e1a', '0xa00308b09db138f301b8009356e62e238f5ef31e3b66f582496d8c52a2e8fce2', '0x45f8484aeb36d4e161baf35cdc8ad99a5ccdf2fb0d687650d960f21f3cd54805', '0x99a0f22e0ebc696df88ad44d66034b22f10b4a4a818d6d3eac2dde361ea0c1b1', '0xbf80d5d3e8a1ff46305727b7e6aa1878d81abb7f0c1fba082c5b00a5ccdaf3f3', '0xedaaf2ecf1ff4c1c3f4485fafdda38e4babc5ec1138cb513270408f8522b71c6'], 'count': 7, 'save_task_id': 'df52e028-c03e-44e7-aabe-acd72aaca8a0'}"
    }
  ]
}
``` 

#### Check Redis Status 
**Request to API:** 
```bash
curl -X 'GET' \
  'http://localhost:8001/tasks/health_redis' \
  -H 'accept: application/json'
``` 
**Response:** 
```json 
{
  "status": "healthy",
  "redis": "connected"
}
``` 

#### Check Transaction Analyzer Status 
**Request to API:** 
```bash
curl -X 'GET' \
  'http://localhost:8001/' \
  -H 'accept: application/json'
``` 
**Response:** 
```json 
{
  "message": "Transaction Analyzer API"
}
``` 

### Requirements for installation or development, use `requirements.txt` or `tests/requirements_test.txt`: 

```bash
 pip install -r requirements.txt 
 ``` 
 For testing: 

```bash
 pip install -r tests/requirements_test.txt 
 ``` 
 Alternatively, install as a Python package: 

```bash
 pip install . 
 ``` 
 For development with additional tools: 

```bash
 pip install .[dev] 
 ``` 


### Official Documentation Links

For more details on how **FastAPI** works, visit:
[FastAPI Documentation](https://fastapi.tiangolo.com/)

For more details on how **Docker** works, visit:
[Docker Documentation](https://docs.docker.com/)

For more details on how **Celery** works, visit:
[Celery Documentation](https://docs.celeryq.dev/en/stable/)

For more details on how **Redis** works, visit:
[Redis Documentation](https://redis.io/)

For more details on how **PostgreSQL** works, visit:
[PostgreSQL Documentation](https://www.postgresql.org/)

For more details on how **Flower** works, visit:
[Flower Documentation](https://flower.readthedocs.io/en/stable/)

For more details on how **uvicorn** works, visit:
[uvicorn Documentation](https://www.starlette.io/uvicorn/)

For more details on how **SQLAlchemy** works, visit:
[SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/14/index.html)

For more details on how **Asyncio** works, visit:
[Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

For more details on how **asyncio** works, visit:
[Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

For more details on how **web3** works, visit:
[web3 Documentation](https://web3py.readthedocs.io/en/stable/index.html)

For more details on how **pytest** works, visit:
[pytest Documentation](https://docs.pytest.org/en/7.2.x/)

For more details on how **Flashbots** works, visit:  
[Flashbots Documentation](https://flashbots.net)

### This project

For more details on how **Analyzer** works, visit:
[Analyzer Transactions](https://github.com/onium16/analyzer_swap_txs.git)


### License

This project is open-source and can be freely used in any project. You are welcome to integrate and modify it as needed.  
Source code is available on GitHub: 
[Analyzer Transactions](https://github.com/onium16/analyzer_swap_txs.git)

---

author: SeriouS

email: onium16@gmail.com
