#!/usr/bin/env bash
# Everything that can be checked without hardware: the printed geometry for
# every rim size, and the ESPHome configuration.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PY:-.venv-cad/bin/python}
[ -x "$PY" ] || { echo "no $PY - run 'make venv' first" >&2; exit 1; }

status=0
for rim in 6 9 12; do
    echo "== fit checks, rim $rim mm"
    if ! "$PY" cad/check_fit.py --rim-gap "$rim"; then status=1; fi
done

echo "== esphome config"
if ! command -v esphome >/dev/null 2>&1; then
    echo "esphome not installed - skipping (pip install esphome)" >&2
else
    cd firmware
    if [ ! -f secrets.yaml ]; then
        # Local dummy secrets, never committed: the YAML only needs the keys to
        # resolve, and `esphome config` does not talk to the network.
        sed -e 's/^wifi_ssid: .*/wifi_ssid: "validate"/' \
            -e 's/^wifi_password: .*/wifi_password: "validate-validate"/' \
            -e 's/^ap_password: .*/ap_password: "validate-validate"/' \
            -e 's/^ota_password: .*/ota_password: "validate-validate"/' \
            -e 's/^api_encryption_key: .*/api_encryption_key: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="/' \
            secrets.yaml.example > secrets.yaml
        echo "(wrote a throwaway firmware/secrets.yaml - gitignored)"
    fi
    if ! esphome config soilsitter.yaml > /tmp/soilsitter-config.log 2>&1; then
        tail -25 /tmp/soilsitter-config.log
        status=1
    else
        echo "configuration is valid"
    fi
fi

exit "$status"
