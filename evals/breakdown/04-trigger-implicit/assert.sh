#!/usr/bin/env bash
# Trigger scenario: the prompt states breakdown's job — dividing a spec into
# independently dispatchable work — without naming the skill.
set -u
bash "$EVALS_LIB/assert-trigger.sh" fired breakdown
