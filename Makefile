PY ?= .venv-cad/bin/python
RIMS ?= 6 9 12
ESPHOME ?= esphome

.PHONY: help venv stl check render firmware-config firmware-compile all clean

help:
	@echo "make venv              create .venv-cad and install requirements.txt"
	@echo "make stl               rebuild STLs for RIMS (default: 6 9 12)"
	@echo "make check             fit/printability checks for RIMS"
	@echo "make render            regenerate docs/diagrams/*.png"
	@echo "make firmware-config   esphome config (needs firmware/secrets.yaml)"
	@echo "make firmware-compile  full ESPHome build"
	@echo "make all               venv + stl + check + render"

venv:
	python3 -m venv .venv-cad
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -r requirements.txt

stl:
	@for r in $(RIMS); do \
		$(PY) cad/soilsitter.py --rim-gap $$r || exit 1; \
	done

check:
	@for r in $(RIMS); do \
		$(PY) cad/check_fit.py --rim-gap $$r || exit 1; \
	done

render:
	$(PY) cad/render.py

firmware-config:
	cd firmware && $(ESPHOME) config soilsitter.yaml

firmware-compile:
	cd firmware && $(ESPHOME) compile soilsitter.yaml

all: stl check render

clean:
	rm -rf cad/__pycache__ firmware/.esphome
