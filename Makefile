.PHONY: deps
deps:
	npm install

.PHONY: run
run: deps
	pipenv run python main.py
