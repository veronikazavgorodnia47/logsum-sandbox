# K 5.W.9 — By-hand vs by-agent comparison

## What both produced
Both chains delivered the same core deliverables: `spec.md`, `src/logsum.py`,
`tests/test_logsum.py`, `.github/workflows/ci.yml`, a refactor pass, and a
provenance note. Tests passed in CI on both branches.

## Where the agent saved time
- Completed the full feature chain (spec → implementation → tests → CI → refactor →
  provenance) with no output corrections needed. Two workflow interventions were
  required: the user ran `git reset --hard` manually (auto-mode blocked the destructive
  command), and committed the `provenance.md` merge conflict manually.
- Handled the ruff lint fix (unused import, unsorted imports) without prompting —
  caught, fixed, and bundled into the CI commit on its own.
- Produced a clean, focused branch with no accumulated session artefacts.

## Where the agent went wrong or shorter
- **Provenance note incomplete** — `Model` and `Context loaded` fields left blank
  ("skipped for this session"). The supervised provenance (K 5.W.7) named the
  model, context files, and justified every deviation explicitly.
- **Simpler tests** — same coverage, but no inline comments, less granular
  assertions, and missing some edge cases present in the supervised suite
  (e.g. `test_columns_accepted_in_any_order`, more granular `TestEmptyInput`).
- **Dropped the coheader guard comment** in `src/logsum.py` — the supervised chain
  annotated `reader.fieldnames` with `# triggers header read`; the replay dropped
  the comment but kept the guard (`if not fieldnames:`) itself.
- **No session notes** — `ci-notes.md` and `refactor-notes.md` do not exist on
  the replay branch. A reviewer inheriting this branch has no record of what
  failed and why, or what the refactor removed.
- **CLAUDE.md not updated** — the improved Commands and Architecture sections
  added during the supervised session are absent from the replay branch.

## What the agent did better
- The replay branch reads as a cleaner feature story — each commit adds exactly
  one deliverable with no accumulated notes or fix commits mixed in.
- The lint fix was handled proactively without the red-CI-then-fix cycle the
  supervised session required.

## What I learned about supervised vs async
Supervised work produces richer evidence: session notes, commented tests, an
honest provenance note, and rule-file improvements. The agent replay is faster
but produces thinner provenance — a reviewer can verify the output but cannot
reconstruct the decisions. For a change that anyone downstream needs to audit
(QA, Security, the next engineer), the supervised evidence chain is necessary.
For a bounded, low-risk task with a clear spec, async is faster and the output
is clean enough to review directly.

## What I would do differently next time
- Require provenance fields (model, context loaded) to be filled — specify this
  in the task prompt, not as a follow-up ask.
- Pre-load a richer context bundle before the replay so the agent starts from
  the same CLAUDE.md state as the supervised session.
- Ask for session notes (`ci-notes.md`, `refactor-notes.md`) explicitly in the
  task plan — the agent will not produce them unless named.
