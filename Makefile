PY ?= .venv-cad/bin/python
RIMS ?= 6 9 12
ESPHOME ?= esphome

.PHONY: help venv stl print-stl check print-check render firmware-config firmware-compile all clean

help:
	@echo "make venv              create .venv-cad and install requirements.txt"
	@echo "make stl               rebuild STLs for RIMS (default: 6 9 12)"
	@echo "make print-stl         re-export stl/print/ in print orientations"
	@echo "make check             fit checks, then the printability audit"
	@echo "make print-check       overhang spans and bridges in stl/print"
	@echo "make render            regenerate docs/diagrams/*.png (preview + section)"
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

print-stl:
	@for r in $(RIMS); do \
		$(PY) cad/orient.py --rim-gap $$r || exit 1; \
	done

check:
	@for r in $(RIMS); do \
		$(PY) cad/check_fit.py --rim-gap $$r || exit 1; \
	done

render:
	$(PY) cad/preview.py
	$(PY) cad/render.py

firmware-config:
	cd firmware && $(ESPHOME) config soilsitter.yaml

firmware-compile:
	cd firmware && $(ESPHOME) compile soilsitter.yaml

all: stl print-stl check render

clean:
	rm -rf cad/__pycache__ firmware/.esphome stl/print

print-check:
	@for r in $(RIMS); do \
		$(PY) cad/printability.py --rim $$r || exit 1; \
	done
