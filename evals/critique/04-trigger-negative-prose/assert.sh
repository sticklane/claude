#!/usr/bin/env bash
# Negative trigger scenario: editing human-facing prose belongs to the writing
# pack, not to critique. Critique activating here is description over-reach —
# the failure mode a positive-only evalset never catches.
set -u
bash "$EVALS_LIB/assert-trigger.sh" not-fired critique
