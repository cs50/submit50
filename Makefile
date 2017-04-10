.PHONY: build
build: clean
	python3 setup.py sdist

.PHONY: clean
clean:
	rm -rf *.egg-info dist

.PHONY: install
install: build
	pip3 install dist/*.tar.gz

# used by .travis.yml
.PHONY: release
release:
	curl -d "{ \
		\"tag_name\": \"v$$(python setup.py --version)\",
		\"target_commitish\": \"master\",
		\"name\": \"v$$(python setup.py --version)\"
	}" -u kzidanebot:$$GITHUB_TOKEN https://api.github.com/repos/$$TRAVIS_REPO_SLUG/releases
