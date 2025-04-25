## 📘 Available in other languages:

📘 [Read English](README.md)

## Analyser transactions

(!Атоматическое развертывание сервисов Docker Compose)

Мультисервисное решение для анализа транзакций. Демонстрирует взаимодействие между сервисами (Docker conteiners) с использованием REST API (FastAPI), фоновых задач (Celery), кэширования (Redis) и базы данных (PostgreSQL). 

### Основной функционал: 
Принимает значение количества блоков или срез, по номеру блока, для парсинга. 
Собирает данные о транзакциях. 
Фильтрует оставляя только swap для Uniswap V2, Uniswap V3. 
Декодирует input. 
Cохраняет в  данные в Redis и в PostgreSQL (автоматически создаёт тестовый сервер с базой данных (analyzer) и таблицей (swap_txs)). 

### Дополнительные функции:
Позволяет:
- получить данные по hash транзакции.
- получить данные транзакций по номеру блока.
- получить данные о статусе задания.
- вернуть перечень заданий с их состоянием и результатом работы
- проверить состояние сервиса Redis (кэша) и PostgreSQL (базы данных) (Необходимо при масштабировании).

|| В проекте используются: паралельные порты по умолчанию (+1 от стандартных, чтоб избежать конфликтов, контейнеров).


## Ключевые особенности проекта

- Работает с **несколькими нодами** и контролирует нагрузку между ними, и выделяет свободную ноду для работы.

- Позволяет работать с **несколькими воркерами** и контролирует нагрузку между ними, и выделяет свободный воркер для работы.

- Позволяет **производить долгое обработку транзакций** в фоновом режиме, чтобы не заблокировать основной процесс.

- Позволяет запускать workers в паралельном режиме разных машинах, чтобы увеличить скорость обработки транзакций. 

- Воркеры обеспечены доступом к **Redis** для кэширования данных и обмена сообщениями между ними, данными о состоянии нод а также данными о состоянии воркеров, и пыстрый доступ к актуальной информации с TTL.

- В качесве постоянного хранилища **PostgreSQL** используется для сохранения данных о транзакциях.

- Парсит **транзакции** с помощью **rpc** обращаясь к нодам.

- В базовой версии парсит Swap транзакции Uniswap V2 и V3. Декодирует input используя **abi**.

- Реализовано два балансира нагрузки:
    - Первый слой (анализ): Celery распределяет нагрузку между нодами обрабатывая запросы, кэшируя ответы в Redis.
    - Второй слой (запросы): Celery распределяет запросы к базе, кэшируя в Redis.


## Используемые технологии

- [**Docker**](https://www.docker.com/) — контейнеризация
- [**FastAPI**](https://fastapi.tiangolo.com/) — фреймворк для создания REST API
- [**Celery**](https://docs.celeryq.dev/en/stable/) — асинхронная обработка фоновых задач
- [**Redis**](https://redis.io/) — система кэширования и брокер сообщений
- [**PostgreSQL**](https://www.postgresql.org/) — реляционная база данных
- [**Flower**](https://flower.readthedocs.io/en/stable/) — визуализация данных Redis


## Планируемые улучшения

Необходимо добавить конфигурацию `nginx` как реверс-прокси для повышения безопасности:

- Инкапсуляция всех сервисов за Nginx  
  Публично доступными останутся только необходимые порты (например, 80/443).

- Ограничение доступа к внутренним сервисам  
  Будут закрыты порты `5433`, `6380`, `8001`, `5556` извне — доступ к ним будет осуществляться только через Nginx.

- Создание альтернативного compose-файла `docker-compose.nginx.yml`  
  Для продакшн-сред, с включённым Nginx и отключёнными внешними портами для всех сервисов, кроме него.


## Руководство по использованию

1. Установите [Docker](https://www.docker.com/) и [Docker Compose](https://docs.docker.com/compose/install/).

2. Создание проекта
    2.1. Создаем дерикторию и виртуальное окружение:
    * С оздайте новую директорию для проекта:

        ```bash 
        mkdir NewProject
        ```
    * Перейдите в директорию проекта:

        ```bash
        cd NewProject
        ```

    * Создайте и активируйте виртуальное окружение:

        For Linux/MacOS:

        ```bash
        python -m venv venv  # Create a virtual environment
        source venv/bin/activate  # Activate the environment
        ```
        For Windows:

        ```bash
        python -m venv venv  # Create a virtual environment
        venv\Scripts\activate  # Activate the environment
        ```

    2.2. Клонируем репозиторий:

    ```bash
    git clone https://github.com/onium16/analyzer_swap_txs.git
    ```

3. Создаем два файла .env и docker/.env:
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

4. Запускаем контейнеры:

    I. вариант:
    4.1 Перейдите в директорию проекта и выполните одну из необходимых команд:

    ```bash
    make up      # Запустить контейнеры
    make down    # Остановить контейнеры
    make logs    # Смотреть логи
    make restart # Перезапуск
    ```
    4.2. Подождите, пока контейнеры будут запущены.

    ```bash
    docker ps -a
    ```
    
    или

    ```
    docker compose -f docker/docker_compose.yml -p test_pool ps
    ```

    II. вариант:

    4.1. Перейдите в директорию проекта и выполните команду:

    ```bash
    docker compose -f docker/docker_compose.yml -p test_pool up --build -d
    ```

    4.2. Подождите, пока контейнеры будут запущены.

    ```bash
    docker ps -a
    ```
    
    или

    ```
    docker compose -f docker/docker_compose.yml -p test_pool ps
    ```

    example:

    ```
    CONTAINER ID   IMAGE                          COMMAND                   CREATED        STATUS                  PORTS                                                                                                                                                                                                            NAMES
    e2d5935bcf3a   test_pool-flower               "celery -A tasks.ana…"    11 hours ago   Up 11 hours             0.0.0.0:5556->5555/tcp, [::]:5556->5555/tcp                                                                                                                                                                      test_pool-flower-1
    042d044cff8c   test_pool-celery_worker        "celery -A tasks.ana…"    11 hours ago   Up 11 hours                                                                                                                                                                                                                              test_pool-celery_worker-1
    315c2dc185db   test_pool-api                  "uvicorn api.main:ap…"    11 hours ago   Up 11 hours             0.0.0.0:8001->8000/tcp, [::]:8001->8000/tcp                                                                                                                                                                      test_pool-api-1
    88b02d802ced   redis:6                        "docker-entrypoint.s…"    23 hours ago   Up 11 hours (healthy)   0.0.0.0:6380->6379/tcp, [::]:6380->6379/tcp                                                                                                                                                                      test_pool-redis-1
    d7d5a1b73f07   postgres:13                    "docker-entrypoint.s…"    23 hours ago   Up 11 hours (healthy)   0.0.0.0:5433->5432/tcp, [::]:5433->5432/tcp                                                                                                                                                                      test_pool-db-1

    ```

    4.3. Перейдите в директорию проекта и выполните команду:

    ```docker compose -f docker/docker_compose.yml -p test_pool ps```

    4.4. Проверьте, что все контейнеры запущены.
    
    ```docker compose -f docker/docker_compose.yml -p test_pool logs```


5. Для работы с проектом воспользуемся [FastAPI Docs](http://127.0.0.1:8001/docs).

6. Для визуализации работы Celery + Redis воспользуемся [Flower](http://127.0.0.1:5556).

7. После завершения работы с проектом можем удалить все тома и билды, сети и базу данных

    ```docker compose -f docker/docker_compose.yml -p test_pool down --volumes --rmi all```

## Список портов:
```
    host: 127.0.0.1 or localhost

    SERVICE     PORT_CUSTOM     PORT_DEFAULT

    FastAPI:    8001            8000
    Celery:     -           
    Redis:      6380            6379
    PostgreSQL: 5433            5432
    Flower:     5556            5555
```
example:

```
http://localhost:8001
```
Проверь или свободны порты [8001,6380,5433,5556]:

```
sudo lsof -i :8001
```

### Using

##### check redis status
```bash
redis-cli -h localhost -p 6380
```
```bash
redis-cli -h redis -p 6380 ping # return PONG
```

#### Запуск получения данных о Swap транзакциях, анализ, сохранение в базу данных (с указанием глубины блоков, например: 2):
Requests to api:
```bash
curl -X 'POST' \
  'http://localhost:8001/analyze/blocks' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "depth_blocks": 1
}'
```

Return:
```json
{"task_id":"11e897b9-a5af-42a9-82ae-739c602b1473","status":"Task started"}
```


#### Запуск получения данных о Swap транзакциях, анализ, сохранение в базу данных (с указанием среза блоков, например: 22324710, 22324712):

Requests to api:
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
Return:
```json
{"task_id":"a8a1d944-fdc7-4896-9707-b876438d1567","status":"Task started"}
```

#### Запуск получения данных о Swap транзакции по transaction hash:

Requests to api:
```bash
curl -X 'GET' \
  'http://localhost:8001/data/transaction/0x5bdc2ef4af09142f3999aa9e5af9384855fc5071cab1a4b6ba02dc48afa80b85' \
  -H 'accept: application/json'
```
Return:
```json
{"task_id":"a8a1d944-fdc7-4896-9707-b876438d1567","status":"Task started"}
```

#### Запуск получения данных о Swap транзакциях, анализ, сохранение в базу данных (с указанием среза блоков, например: 22324710, 22324712):

Requests to api:
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
Return:
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

#### Проверка статуса задачи:

Requests to api:
```bash
curl -X 'GET' \
  'http://localhost:8001/tasks/status/a288c77e-5cc4-47d1-a54a-c3230928d8da' \
  -H 'accept: application/json'
```
Return:
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
#### Вернуть срез задач:

Requests to api:
```bash
curl -X 'GET' \
  'http://localhost:8001/tasks/all?start=0&end=100' \
  -H 'accept: application/json'
```
Return:
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

#### Вернуть состояние Redis:

Requests to api:
```bash
curl -X 'GET' \
  'http://localhost:8001/tasks/health_redis' \
  -H 'accept: application/json'
```
Return:
```json
{
  "status": "healthy",
  "redis": "connected"
}
```

#### Вернуть состояние Analyzer Transactions:

Requests to api:
```bash
curl -X 'GET' \
  'http://localhost:8001/' \
  -H 'accept: application/json'
```
Return:
```json
{
  "message": "Transaction Analyzer API"
}
```

### Requirements

For manual mode or development  use requirements.txt
```bash
pip install -r tests/requirements.txt
```

### Official Documentation Links

For more details on how FastAPI works, visit:
[FastAPI Documentation](https://fastapi.tiangolo.com/)

For more details on how Docker works, visit:
[Docker Documentation](https://docs.docker.com/)

For more details on how Celery works, visit:
[Celery Documentation](https://docs.celeryq.dev/en/stable/)

For more details on how Redis works, visit:
[Redis Documentation](https://redis.io/)

For more details on how PostgreSQL works, visit:
[PostgreSQL Documentation](https://www.postgresql.org/)

For more details on how Flower works, visit:
[Flower Documentation](https://flower.readthedocs.io/en/stable/)

For more details on how uvicorn works, visit:
[uvicorn Documentation](https://www.starlette.io/uvicorn/)

For more details on how SQLAlchemy works, visit:
[SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/14/index.html)

For more details on how Asyncio works, visit:
[Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

For more details on how asyncio works, visit:
[Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

For more details on how web3 works, visit:
[web3 Documentation](https://web3py.readthedocs.io/en/stable/index.html)

For more details on how pytest works, visit:
[pytest Documentation](https://docs.pytest.org/en/7.2.x/)

For more details on how Flashbots works, visit:  
[Flashbots Documentation](https://flashbots.net)

### This project

For more details on how Analyzer works, visit:
[Analyzer Transactions](https://github.com/onium16/analyzer_swap_txs.git)



### License

This project is open-source and can be freely used in any project. You are welcome to integrate and modify it as needed.  
Source code is available on GitHub: 
[Analyzer Transactions](https://github.com/onium16/analyzer_swap_txs.git)

---

author: SeriouS

email: onium16@gmail.com
