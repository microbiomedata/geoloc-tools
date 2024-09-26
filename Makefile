.PHONY: test

test:
	pytest tests

lint:
	ruff format --check
	ruff check

lint-fix:
	ruff check --fix
	ruff format
