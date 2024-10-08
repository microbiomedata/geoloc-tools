.PHONY: test lint lint-fix

RUN = poetry run

test:
	$(RUN) pytest tests

lint:
	$(RUN) ruff format --check
	$(RUN) ruff check

lint-fix:
	$(RUN) ruff check --fix
	$(RUN) ruff format
