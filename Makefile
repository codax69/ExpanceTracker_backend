.PHONY: docs

docs:
	python manage.py spectacular --color --file schema.yml
