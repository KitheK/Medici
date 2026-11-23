# Batch run report

Issue: E9-3. Summarise a batch run: tokens, cost and failures per batch, printed as a table and saved as JSON. Read counters from the batch runner (`src/medici/batch`); do not recompute them. The report contains counts, IDs and costs only: no names, emails or page text. Tests live in `tests/batch/`.
