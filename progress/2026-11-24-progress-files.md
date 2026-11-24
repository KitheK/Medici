# 2026-11-24: One progress file per entry

- Every PR appended to the end of `progress.md`, so each merge made the others conflict. Entries are now
  separate files here, and `progress.md` is closed.
- `/fix-conflicts` moves entries that open PRs already added to `progress.md` into files of their own.
- Its comment now says to approve the waiting runs when `GH_PAT` is not set.
- Next: open PRs may conflict on `progress.md` once more; run `/fix-conflicts` on those.
