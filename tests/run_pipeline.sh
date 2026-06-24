#!/bin/bash
# run_pipeline.sh
# Runs all tests in a SINGLE pytest session: smoke -> unit -> functional -> e2e
# Emulators start once via session-scoped fixture in conftest.py

# Navigate to project root regardless of where the script is called from
cd "$(dirname "$0")/.."

BOLD="\033[1m"
GREEN="\033[0;32m"
RED="\033[0;31m"
CYAN="\033[0;36m"
RESET="\033[0m"

echo ""
echo -e "${CYAN}${BOLD}=================================================${RESET}"
echo -e "${CYAN}${BOLD}          NES Ammeter QA Pipeline               ${RESET}"
echo -e "${CYAN}${BOLD}=================================================${RESET}"
echo ""

./venv/bin/python3 -m pytest \
    tests/test_smoke.py \
    tests/test_ammeter_tester.py \
    tests/test_ammeter_framework.py \
    tests/test_functional.py \
    tests/test_e2e.py \
    --no-header -v

RESULT=$?

echo ""
echo -e "${CYAN}${BOLD}=================================================${RESET}"
echo -e "${CYAN}${BOLD}              PIPELINE SUMMARY                  ${RESET}"
echo -e "${CYAN}${BOLD}=================================================${RESET}"
[ $RESULT -eq 0 ] \
    && echo -e "  ALL TESTS   ${GREEN}PASSED${RESET}" \
    || echo -e "  PIPELINE    ${RED}FAILED${RESET}"
echo -e "${CYAN}${BOLD}=================================================${RESET}"
echo ""

exit $RESULT
