#!/usr/bin/env bash
# Trigger scenario: the prompt describes critique's own job in the user's
# words and never names the skill, so a run that does not activate critique is
# a description failure, not an execution failure.
set -u
bash "$EVALS_LIB/assert-trigger.sh" fired critique
