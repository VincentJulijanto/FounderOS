.PHONY: dev install test

dev:
	@./dev.sh

install:
	.venv/bin/pip install -r backend/requirements.txt
	cd frontend && npm install

test:
	.venv/bin/python3 -m pytest backend/tests/ -q
