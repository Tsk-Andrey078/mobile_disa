.DEFAULT_GOAL := help

CURRENT_UID := $(shell id -u)
CURRENT_GID := $(shell id -g)

PRIVILEGES = ${APP} chown -R $(CURRENT_UID):$(CURRENT_GID)

help: ## Help message
	@echo "Please choose a task:"
	@grep -E '(^[a-zA-Z_-]+:.*?##.*$$)|(^##)' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[32m%-30s\033[0m %s\n", $$1, $$2}' | sed -e 's/\[32m##/[33m/'

PROJECT_DIR=$(shell dirname $(realpath $(MAKEFILE_LIST)))

ifeq (manage,$(firstword $(MAKECMDGOALS)))
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(RUN_ARGS):;@:)
endif

start: ## Start all services
	python manage.py runserver

migrate: clean makemigrations migration ## Clean start migrations

clean: ## Clean migrations
	find ./mobile_rest/migrations -type f ! -name '__init__.py' -name '*.py' -delete
	@echo "Migrations deleted!"

collectstatic: ## Collectstatic
	python manage.py collectstatic --noinput
	chown -R $(CURRENT_UID):$(CURRENT_GID) static
	@echo ">>> Controller done!"

makemigrations: ## Make migrations
	python manage.py makemigrations
	@echo ">>> Migrations created!"

migration: ## Create new migration
	python manage.py migrate
	@echo ">>> Migration done!"

test: ## Run all tests
	python manage.py test
	@echo ">>> Tests completed!"

createsuperuser: ## Create a superuser
	python manage.py createsuperuser

install: ## Install dependencies
	pip install -r requirements.txt
	@echo ">>> Dependencies installed!"

lint: ## Check code style with flake8
	flake8 .
	@echo ">>> Linting completed!"

makemessages: ## Make translations
	python manage.py makemessages -l ru
	@echo ">>> Messages updated!"

compilemessages: ## Compile translations
	python manage.py compilemessages
	@echo ">>> Messages compiled!"

backup: ## Backup database
	python manage.py dumpdata --indent 2 > backup.json
	@echo ">>> Database backup created in backup.json!"

clean-tmp: ## Remove temporary files
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	@echo ">>> Temporary files cleaned!"