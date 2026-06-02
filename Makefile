.PHONY: install run debug clean lint lint-strict

PY_FILES = cam.py connection.py drone.py hub.py main.py network.py parsing.py\
pathfinder.py reservation.py visualizer.py

install:
	uv venv
	uv pip install -r requirements.txt

run:
	uv run ./main.py

debug:
	uv run python3 -m pdb main.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf .venv

lint:
	uv run flake8 $(PY_FILES)
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 $(PY_FILES)
	uv run mypy $(PY_FILES) --strict