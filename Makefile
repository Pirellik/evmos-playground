.PHONY: deps
deps:
	npm install
	pipenv update

.PHONY: run
run: deps
	pipenv run python main.py
