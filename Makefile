CARGO ?= cargo
SOURCE_DIR := govee2mqtt_security_local/local-source

check:
	cd $(SOURCE_DIR) && $(CARGO) check --locked

fmt:
	cd $(SOURCE_DIR) && $(CARGO) fmt --all -- --check

clippy:
	cd $(SOURCE_DIR) && $(CARGO) clippy --locked --all-targets -- -D warnings

test:
	cd $(SOURCE_DIR) && $(CARGO) test --locked

build:
	cd $(SOURCE_DIR) && $(CARGO) build --locked

integrity:
	python3 scripts/check-store-source.py

verify: fmt clippy test build integrity
	python3 -m unittest discover -s tests -v

runtime: build
	cd $(SOURCE_DIR) && python3 ../../scripts/verify-runtime.py "$${CARGO_TARGET_DIR:-target}/debug/govee"

docker:
	python3 scripts/check-store-source.py
	docker build --build-arg CARGO_PROFILE=verification -f Dockerfile govee2mqtt_security_local

.PHONY: check fmt clippy test build integrity verify runtime docker
