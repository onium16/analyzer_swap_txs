# Makefile

DOCKER_COMPOSE=docker compose -f docker/docker_compose.yml -p test_pool

up:
	$(DOCKER_COMPOSE) up --build -d

down:
	$(DOCKER_COMPOSE) down

logs:
	$(DOCKER_COMPOSE) logs -f

restart: down up