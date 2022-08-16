include $(PWD)/.env

ifeq ($(ENVIRONMENT), dev)
	COMPOSE_FILE_PATH := 
else ifeq ($(ENVIRONMENT), staging)
	COMPOSE_FILE_PATH := -f docker-compose.yml -f docker-compose.staging.yml
else # Production
	COMPOSE_FILE_PATH := -f docker-compose.yml
endif

CKAN_CONTAINER := $(shell docker ps --filter "name=ckan" --latest --format "{{.Names}}")

build.all:
	docker compose $(COMPOSE_FILE_PATH) build --no-cache

build.ckan:
	docker compose $(COMPOSE_FILE_PATH) build --no-cache ckan

rebuild.ckan:
	docker compose $(COMPOSE_FILE_PATH) up -d --build ckan

volumes.create:
	docker volume create caddy_data & docker volume create ckan_storage

restart.ckan:
	docker compose $(COMPOSE_FILE_PATH) up -d --force-recreate ckan

debug.ckan:
	docker stop ${CKAN_CONTAINER} && docker compose $(COMPOSE_FILE_PATH) run --rm --no-deps --name ckan ckan

replace.ckan:
	./update_ckan_container.sh

scaleup.ckan:
	docker compose $(COMPOSE_FILE_PATH) up -d --no-deps --scale ckan=2 --no-recreate ckan

scaledown.ckan:
	docker compose $(COMPOSE_FILE_PATH) up -d --no-deps --scale ckan=1 --no-recreate ckan

ssh.ckan:
	docker exec -it $(CKAN_CONTAINER) /bin/bash

start: up logs

up:
	docker compose $(COMPOSE_FILE_PATH) up -d

down:
	docker compose $(COMPOSE_FILE_PATH) down

logs:
	docker compose $(COMPOSE_FILE_PATH) logs -f --tail 100

ps: 
	docker compose $(COMPOSE_FILE_PATH) ps
	
reload.caddy:
	docker compose ${COMPOSE_FILE_PATH} exec -w /etc/caddy caddy caddy reload

restart.redis:
	docker compose $(COMPOSE_FILE_PATH) up -d --no-deps --force-recreate redis

harvest.gather:
	docker exec $(CKAN_CONTAINER) /bin/bash -c "ckan harvester gather-consumer"

harvest.fetch:
	docker exec $(CKAN_CONTAINER) /bin/bash -c "ckan harvester fetch-consumer"

harvest.run:
	docker exec $(CKAN_CONTAINER) /bin/bash -c "ckan harvester run"

xloader.submit:
	docker exec $(CKAN_CONTAINER) /bin/bash -c "ckan xloader submit all"

qa.run:
	docker exec $(CKAN_CONTAINER) /bin/bash -c "ckan qa run"

qa.init:
	docker exec $(CKAN_CONTAINER) /bin/bash -c "ckan report initdb"

search.reindex:
	docker exec $(CKAN_CONTAINER) /bin/bash -c "ckan search-index rebuild"

db.backup:
	./backup_db.sh $(ENVIRONMENT) db ckan && \
	./backup_db.sh $(ENVIRONMENT) db datastore

db.nuke:
	# shut down postgres and solr & remove volumes
	docker compose stop db solr && docker volume rm docker-ckan_pg_data docker-ckan_solr_data \
	&& up


dev:
	cd src/ckanext-subakdc && npm run dev


# WIP currently having issues running this locally
test.plugins:
	docker exec -w "/srv/app/src_extensions/ckanext-subakdc-plugins" $(CKAN_CONTAINER) /bin/bash -c "pip install pytest-ckan requests_mock && pytest --ckan-ini=test.ini"
