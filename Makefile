SHELL := bash

TEMPLATE_SOURCE ?=
TEMPLATE_REPO ?=
TEMPLATE_BRANCH ?= main
OUTPUT_DIR ?= ./dist/new-repo
REPO_ROOT := $(CURDIR)
OWNER_NAME ?=
OWNER_EMAIL ?=
REPO_NAME ?= timely-project
TEMPLATED ?= 1
INCLUDE_LOGS ?= 0
INIT_GIT ?= 1

SEED_SCRIPT := scripts/bootstrap-timely-template.sh
TIMELY_PLAYBOOK_BIN := .bin/timely-playbook
TEMPLATE_PACKAGE_DIR := $(REPO_ROOT)/dist/timely-template
TEMPLATE_TGZ := $(REPO_ROOT)/dist/timely-template.tgz
TIMELY_PLAYBOOK_MODULE_DIR := $(REPO_ROOT)/cmd/timely-playbook

define __seed_args
	--output $(OUTPUT_DIR) \
	--owner "$(OWNER_NAME)" \
	--email "$(OWNER_EMAIL)" \
	--repo "$(REPO_NAME)" \
	$(if $(strip $(TEMPLATE_SOURCE)),--source $(TEMPLATE_SOURCE),) \
	$(if $(strip $(TEMPLATE_REPO)),--template-repo $(TEMPLATE_REPO) --branch $(TEMPLATE_BRANCH),) \
	$(if $(filter 1,$(INIT_GIT)),--init-git,) \
	$(if $(filter 1,$(INCLUDE_LOGS)),--include-logs,) \
	$(if $(filter 1,$(TEMPLATED)),--templated,--templated=false)
endef

.PHONY: all compile validate verify help bootstrap-template test-smoke clean

all: compile

compile: $(TEMPLATE_TGZ)

$(TIMELY_PLAYBOOK_BIN):
	mkdir -p "$(dir $(TIMELY_PLAYBOOK_BIN))"
	cd "$(TIMELY_PLAYBOOK_MODULE_DIR)" && go build -o "$(REPO_ROOT)/.bin/timely-playbook" .

$(TEMPLATE_PACKAGE_DIR): $(TIMELY_PLAYBOOK_BIN)
	rm -rf "$(TEMPLATE_PACKAGE_DIR)"
	"$(TIMELY_PLAYBOOK_BIN)" package --output "$(TEMPLATE_PACKAGE_DIR)" --templated

$(TEMPLATE_TGZ): $(TEMPLATE_PACKAGE_DIR)
	tar -czf "$(TEMPLATE_TGZ)" -C "$(REPO_ROOT)/dist" timely-template

validate:
	cd "$(TIMELY_PLAYBOOK_MODULE_DIR)" && go test ./...
	python -m unittest discover -s tests -p 'test_*.py'
	bash scripts/chub.sh validate
	bash scripts/run-markdownlint.sh
	bash scripts/check-doc-links.sh

verify: validate compile
	bash scripts/bootstrap-smoke.sh --smoke

help:
	@echo "Build and package Timely Playbook artifacts"
	@echo "  make                    # default target; runs compile"
	@echo "  make compile"
	@echo "  make validate           # Go+Python tests + chub validate + docs checks"
	@echo "  make verify             # validate + package build + bootstrap smoke"
	@echo "  Output:"
	@echo "    dist/timely-template (directory)"
	@echo "    dist/timely-template.tgz (archive)"
	@echo ""
	@echo "Bootstrap a repo from Timely Playbook"
	@echo "  make bootstrap-template OWNER_NAME=\"Name\" OWNER_EMAIL=\"you@example.com\" REPO_NAME=\"repo\""
	@echo "Optional:"
	@echo "  TEMPLATE_SOURCE=/path/to/clone TEMPLATE_REPO=https://github.com/org/repo.git TEMPLATE_BRANCH=main"
	@echo "  OUTPUT_DIR=./dist/new-repo INCLUDE_LOGS=1 INIT_GIT=1 TEMPLATED=1"
	@echo "  make test-smoke"

bootstrap-template:
	@if [ -z "$(OWNER_NAME)" ] || [ -z "$(OWNER_EMAIL)" ]; then \
		echo "Required: OWNER_NAME and OWNER_EMAIL"; \
		exit 1; \
	fi
	@if [ -z "$(strip $(TEMPLATE_SOURCE))" ] && [ -z "$(strip $(TEMPLATE_REPO))" ]; then \
		echo "Either TEMPLATE_SOURCE or TEMPLATE_REPO must be set."; \
		exit 1; \
	fi
	@if [ -n "$(strip $(TEMPLATE_SOURCE))" ] && [ -n "$(strip $(TEMPLATE_REPO))" ]; then \
		echo "Set only one of TEMPLATE_SOURCE or TEMPLATE_REPO"; \
		exit 1; \
	fi
	@bash $(SEED_SCRIPT) $(__seed_args)

test-smoke:
	@bash scripts/bootstrap-smoke.sh --smoke

clean:
	rm -rf "$(REPO_ROOT)/.bin" "$(TEMPLATE_PACKAGE_DIR)" "$(TEMPLATE_TGZ)"
