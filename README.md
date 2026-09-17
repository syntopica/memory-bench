# memory-bench

A two-track benchmark for agent memory systems: **source discovery** kept apart
from **answer sufficiency**, in Spanish and English.

Most memory benchmarks collapse the two. A system can surface the right
document and still answer badly, or answer well from the wrong source and score
as correct. Separating the tracks makes it possible to say which half is
failing.

## Status

Design only. `docs/` holds the design and the first implementation plan; there
is no harness yet. Read it as a specification, not as a tool you can run.

## Licence

MIT.
