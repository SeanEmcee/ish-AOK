# Native Zsh NO_EXEC investigation (2026-11-27)

Status: diagnostic branch only; NOT a fix or release. Order: Native Zsh, expanded profile updater, Unicode renderer, command parity.

App baseline: 67b190b099030a30ced4f327ff427d6ad3bffca7 (feature/native-browser). working was 142536fc2cf7209e082fd190a5351492b4454e10 at inspection. Both pin deps/zsh to emkey1/zsh@c30b3b8d9a5c4d538f7cd124d4198c41d90593cd. Installed build 567 provenance not independently verified. Prior feature/native-browser IPA run 45497919863 ended unsuccessfully (job cancelled).

Device evidence: zsh -f -n via stdin and file warns "subshell state did not finish" for an undefined command or function invocation; -c also warns for a command sequence. Invalid syntax returns nonzero. A marker side effect did not occur. Actual prompt-controls.zsh runtime switches full/compact/auto without stderr. Simple subshell and 50 repeated substitutions passed in normal execution. Do not suppress the warning in the updater.

Source hypothesis: Src/exec.c execsimple checks EXECOPT, while execpline can allocate jobs before the later execution guard. Candidate is an early guard in execpline, immediately after local declarations and before job allocation:
```c
    if (!isset(EXECOPT))
        return lastval = 0;
```
The parser constructs the list first. execlist advances to the next sublist after execpline returns. Review other callers (including exectime) and ensure syntax errors and runtime behavior are preserved. This is a candidate, not a verified root fix.

Owning Zsh repository is read-only through current connector. Obtain a user-owned fork (or coordinate upstream), branch directly at the pinned source SHA, commit the minimal edit in Src/exec.c, then update the app submodule URL and gitlink in a review branch. Do not build with an untracked source overlay or modify installed binaries. Reconcile branch heads and installed build provenance before choosing an app release baseline.

Test: tests/manual/native_zsh_noexec.py, run on old and candidate native runtime. Also run existing native_zsh_fork_state.sh and relevant startup and job-control tests. Require a failing baseline, passing candidate, exact provenance, isolated build, archive hash, and physical iPhone acceptance before release. The Linux host here has no Xcode or reachable GitHub git transport. No IPA has been built. Existing Stage 3 updater and iCloud profile backup remain unchanged; Stage 4 stays blocked.
