# crashfixture reference

There is no passing reference solution for `crashfixture`: the task exists to
exercise the runner's crash/cap recording path, where the stub session dies
mid-run. Its row is always `pass: false` with a non-null partial cost. This
directory exists so the manifest's `reference` path resolves as a real
out-of-mount sibling of `repo/`, matching every other task's layout.
