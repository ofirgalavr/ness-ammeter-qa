#!/bin/bash
# run_pipeline.sh
# Runs test stages in order: smoke -> unit -> functional -> e2e
# Uses pytest markers to select tests — no need to list files explicitly.
# SO_REUSEADDR is set in base_ammeter.py — ports are reused across sessions safely.
#
# Usage:
#   ./tests/run_pipeline.sh                        # Run full pipeline
#   ./tests/run_pipeline.sh smoke                  # Run smoke only
#   ./tests/run_pipeline.sh unit                   # Run unit only
#   ./tests/run_pipeline.sh functional             # Run functional only
#   ./tests/run_pipeline.sh e2e                    # Run e2e only
#   ./tests/run_pipeline.sh smoke unit             # Run smoke then unit
#   ./tests/run_pipeline.sh functional e2e         # Run functional then e2e
#
# Failure behavior:
#   smoke:      stop pipeline immediately with error message
#   unit:       stop pipeline immediately with error message
#   functional: mark as failed, continue to next stage
#   e2e:        mark as failed, show summary

# Navigate to project root regardless of where the script is called from
cd "$(dirname "$0")/.."

# Single log file for entire pipeline run
export PYTEST_LOG_FILE="results/logs/$(date +%Y%m%d_%H%M%S)_pipeline_run.log"
mkdir -p results/logs

BOLD="\033[1m"
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RESET="\033[0m"

# Determine which stages to run
if [ $# -eq 0 ]; then
    STAGES=("smoke" "unit" "functional" "e2e")
else
    STAGES=("$@")
fi

# Validate arguments
VALID_STAGES=("smoke" "unit" "functional" "e2e")
for stage in "${STAGES[@]}"; do
    valid=false
    for valid_stage in "${VALID_STAGES[@]}"; do
        [ "$stage" = "$valid_stage" ] && valid=true && break
    done
    if [ "$valid" = false ]; then
        echo -e "${RED}Unknown stage: '$stage'. Valid stages: smoke, unit, functional, e2e${RESET}"
        exit 1
    fi
done

echo ""
echo -e "${CYAN}${BOLD}=================================================${RESET}"
echo -e "${CYAN}${BOLD}          NESS Ammeter QA Pipeline               ${RESET}"
echo -e "${CYAN}${BOLD}  Stages: ${STAGES[*]}${RESET}"
echo -e "${CYAN}${BOLD}=================================================${RESET}"
echo ""

# Initialize results
SMOKE_RESULT=-1
UNIT_RESULT=-1
FUNCTIONAL_RESULT=-1
E2E_RESULT=-1

run_stage() {
    local stage=$1
    local stage_upper=$(echo "$stage" | tr '[:lower:]' '[:upper:]')

    echo -e "${BOLD}--- ${stage_upper} ---${RESET}"
    ./venv/bin/python3 -m pytest tests/ -v --no-header -m "$stage"
    local result=$?
    echo ""
    return $result
}

print_summary() {
    echo -e "${CYAN}${BOLD}=================================================${RESET}"
    echo -e "${CYAN}${BOLD}              PIPELINE SUMMARY                  ${RESET}"
    echo -e "${CYAN}${BOLD}=================================================${RESET}"
    [ $SMOKE_RESULT -eq 0 ]      && echo -e "  SMOKE          ${GREEN}PASSED${RESET}" || { [ $SMOKE_RESULT -eq -1 ] && echo -e "  SMOKE          -" || echo -e "  SMOKE          ${RED}FAILED${RESET}"; }
    [ $UNIT_RESULT -eq 0 ]       && echo -e "  UNIT           ${GREEN}PASSED${RESET}" || { [ $UNIT_RESULT -eq -1 ] && echo -e "  UNIT           -" || echo -e "  UNIT           ${RED}FAILED${RESET}"; }
    [ $FUNCTIONAL_RESULT -eq 0 ] && echo -e "  FUNCTIONAL     ${GREEN}PASSED${RESET}" || { [ $FUNCTIONAL_RESULT -eq -1 ] && echo -e "  FUNCTIONAL     -" || echo -e "  FUNCTIONAL     ${RED}FAILED${RESET}"; }
    [ $E2E_RESULT -eq 0 ]        && echo -e "  E2E            ${GREEN}PASSED${RESET}" || { [ $E2E_RESULT -eq -1 ] && echo -e "  E2E            -" || echo -e "  E2E            ${RED}FAILED${RESET}"; }
    echo -e "${CYAN}${BOLD}=================================================${RESET}"
    echo ""
}

# Run selected stages
for stage in "${STAGES[@]}"; do
    case $stage in
        smoke)
            run_stage "smoke"
            SMOKE_RESULT=$?
            if [ $SMOKE_RESULT -ne 0 ]; then
                echo -e "${RED}${BOLD}SMOKE tests failed — aborting pipeline.${RESET}"
                echo ""
                print_summary
                exit 1
            fi
            ;;
        unit)
            run_stage "unit"
            UNIT_RESULT=$?
            if [ $UNIT_RESULT -ne 0 ]; then
                echo -e "${RED}${BOLD}UNIT tests failed — aborting pipeline.${RESET}"
                echo ""
                print_summary
                exit 1
            fi
            ;;
        functional)
            run_stage "functional"
            FUNCTIONAL_RESULT=$?
            ;;
        e2e)
            run_stage "e2e"
            E2E_RESULT=$?
            ;;
    esac
done

print_summary

# Exit with failure if any stage failed
for result in $SMOKE_RESULT $UNIT_RESULT $FUNCTIONAL_RESULT $E2E_RESULT; do
    [ $result -ne 0 ] && [ $result -ne -1 ] && exit 1
done
exit 0
