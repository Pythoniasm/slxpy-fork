lint:
	ruff check --fix .
	ruff format .

build:
	python -m build .

distribute:
	python -m twine check dist/*
	python -m twine upload dist/*
