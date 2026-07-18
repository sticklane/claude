# ctx pre-warm hook (R16): refresh the index in the background so the next
# query reads a warm cache. Journaled per C5 with trigger: hook.
"__CTX_BIN__" sync --hook >/dev/null 2>&1 &
