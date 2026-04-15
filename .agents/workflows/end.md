---
description: Conversation end memory persistence and architectural reconsolidation
---
> ⚠️ **Fault Tolerance**: If any step below fails, log the error but CONTINUE executing subsequent steps. The git push in Step 5 must not be blocked by upstream failures.

1. **Solution Self-Reflection** — Answer these questions explicitly before proceeding:
   - What decisions did I make this session? Are they recorded in the Decision Log?
   - Was there a better approach I skipped? Why?
   - How many cloud LLM calls did I make? Could any have been resolved locally?
   - Did I introduce any technical debt? If yes, add a TODO in the Roadmap.
   📝 **Persist Reflection**: After answering the above questions, append the answers as a dated entry to `.agents/reflections/` (create `YYYY-MM-DD.md` if it does not exist). This builds a searchable log of reasoning quality over time.
2. **Memory Reconsolidation & Pruning**: Execute stringently: Versioning & Dedup, Conflict Resolution (mark Superseded_by), and Quality Filtering.
3. **Sanitation**: Proactively wipe all temporary testing artifacts inside `/tmp` inside the container. Ensure zero leakage.
4. **Update AGENTS.md**: Condense newly discovered solutions and critical architectural decisions into the Decision Log and Success Log.
5. **Git Protocol & Indexing**: Execute a semantic Git commit. If a remote repository is configured (`git remote -v` returns a result), run `git push` to trigger the pre-push hook for secret scanning and memory sync.
6. **Final Persistence Confirmation**: Confirm memory synchronization and next-step readiness.
