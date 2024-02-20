lint:
	black --line-length=120 .
	isort --profile black --line-length=120 .
	ruff --fix --line-length=120 --ignore E731 .

build:
	python -m build .

distribute:
	python -m twine check dist/*
	python -m twine upload dist/*
