.ONESHELL:
SHELL := /bin/zsh

version = 0.4.3

test:
	@rm -rf examples/.venv/lib/python3.13/site-packages/catasta
	@cp -r catasta examples/.venv/lib/python3.13/site-packages

upload:
	python -m build
	python -m twine upload dist/*
	git tag -a v$(version) -m "v$(version)"
	git push origin v$(version)
	gh release create v$(version) dist/*


.PHONY: test
