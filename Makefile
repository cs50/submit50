.PHONY: build
build: clean
	python3 setup.py sdist

.PHONY: clean
clean:
	rm -rf *.egg-info dist

.PHONY: install
install: build
	pip3 install dist/*.tar.gz

.PHONY: push
push:
	git push origin "v$$(python3 setup.py --version)"

.PHONY: release
release: tag push

.PHONY: tag
tag:
	git tag "v$$(python3 setup.py --version)"
