.PHONY : install test clean build docker-build docker-run stop server server-bg

install:
	uv tool install -e .
	uv tool update-shell

# Testing
test:
	uv sync --extra dev
	uv run pytest tests/ -v

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build
build: clean
	uv build

make publish: build
	uv publish


docker-run:
	docker compose -f docker-compose.yml up --build -d param-server

stop:
	docker compose -f docker-compose.yml down

# Local development
server:
	uv run python -m param_server.server --config examples/config/params.yml --log-level DEBUG --host 0.0.0.0

server-bg:
	uv run python -m param_server.server --config examples/config/params.yml --log-level INFO --host 0.0.0.0 &


