**Verified Runtime**

opencode version: `1.17.8`.

How verified: `opencode --version`, `opencode --help`, `opencode run --help`, `opencode agent list`, `opencode debug agent general/explore/plan`, live opencode docs, and one read-only `task` spawn/resume probe. I did not run `opencode run --fork` because it would create or alter session state.

1. **Context-Inheritance / Fork**

No true in-conversation subagent fork is exposed to me.

`opencode run --fork --session <id>` exists, but CLI help defines it as: fork the session before continuing. That is a CLI/session operation, not a `task` subagent spawn mode. It appears to copy/fork an existing opencode session into a new resumable session, then continue there. It is not a live child subagent inside the parent conversation.

[UNCERTAIN] Exact copied payload: full transcript vs compacted/session representation. Docs/help only say “fork the session”. I would treat it as a copied resumable session, not live-shared context.

Parent resumability: yes in principle, because the original session remains addressable by its session id, while the fork is a separate session. But this is not the same as “Executor inherits Orchestrator context and returns to the parent as a subagent”.

2. **Fresh Spawn**

A.2 is mostly accurate but needs qualification.

Actual mechanism: `task` tool invokes a configured subagent by `subagent_type`. The prompt is passed as the `prompt` argument. The returned handle is a session-like `task_id`, e.g. my read-only probe returned `ses_11862f46cffeUcd9OKOnC2loHK`.

Important correction: `subagent_type: "general"` is not universally available in every current mode. The local opencode registry has native `general` as a subagent, but this current plan/read-only primary agent denies `task general`, and the exposed tool schema in this session only listed `explore`. In normal/full-access agent config, `general` exists and is intended for general multi-step work.

3. **Continue**

Confirmed.

Mechanism: call `task` again with the same `task_id`. I spawned an `explore` subagent with a marker, then resumed it with the returned `task_id`; it remembered the prior marker. So A.2’s `task_id` resume claim is accurate for this version.

4. **Blocking Hook / Budget Enforcement**

Yes, opencode has mechanisms that can deny before execution.

Mechanism 1: permission system. `permission.task` can statically allow/ask/deny subagent launches by subagent type. This is true pre-execution blocking, but static; it is not naturally a dynamic budget counter unless config is externally changed/reloaded, which I did not verify.

Mechanism 2: plugin hook `tool.execute.before`. Docs show this hook can throw an error to block a tool before it runs. A budget plugin could inspect `task` calls and deny when a cap is hit. Plugins live in `.opencode/plugins/`, `~/.config/opencode/plugins/`, or configured npm plugins.

Current runtime: no plugins loaded (`opencode debug info` reported none). So converge on this setup is not already hook-guarded. It could be extended to opencode via a plugin, but today’s `framework-adapters.md` Claude-only hook wording is accurate for the existing converge implementation.

5. **Per-Subagent Model Selection**

Partial support.

The `task` tool exposed to me has no per-call `model` argument. So you cannot say “spawn this task with model X” in the task call itself.

opencode agents can have a configured `model` field. Docs also say subagents without a model inherit the invoking primary agent’s model. Therefore model selection is possible by defining separate subagent types with different `model` configs, not by per-spawn parameter in the current `task` call.

6. **Runtime Capability Probing**

For fresh spawn/continue: inspect the current tool schema or try a harmless read-only `task` spawn, then resume by returned `task_id`.

For available subagent types: use `opencode agent list` or `opencode debug agent <name>`, and account for current primary-agent permissions because denied subagents may disappear from the task description.

For CLI session fork: parse `opencode run --help` for `--fork` plus `--session`/`--continue`.

For true subagent context inheritance: probe the `task` tool schema for a context/fork parameter or a `fork` subagent mode. In this runtime I found neither.

7. **Net Assessment**

For Part B’s exact goal, opencode does not offer an equivalent to Claude Code’s `subagent_type: fork`.

It offers partial substitutes: CLI session fork via `opencode run --fork --session`, normal fresh subagent spawn via `task`, continuation of existing subagent sessions via `task_id`, and possible persistent state via files or session summaries. None is a clean “Executor child inherits current Orchestrator transcript and returns as a subagent”.

So on opencode, Part B degrades to fresh Spawn unless converge adds a separate opencode-specific workaround. The best native alternative worth encoding is not session fork; it is “fresh executor with compressed context handoff”, possibly via state files/attempt logs, because that preserves the existing task model.

8. **Other Agent-Model Implications**

opencode’s `task` subagents are child sessions. That supports Reviewer independence when spawned fresh with a self-contained prompt.

Continue preserves subagent context, so inner-loop review can reuse the same Reviewer instance. That matches converge’s current abstraction.

For H1, opencode’s lack of true fork actually protects the boundary: Executor remains fresh unless explicitly given context through prompt/files. If a future opencode plugin or custom tool adds fork-like behavior, the H1 principle should be enforced at the adapter layer: only use inherited context for roles whose output is mechanically re-verified by a fresh downstream reviewer.

**Bottom Line**

Part B’s fork concept has no real opencode subagent realization in this runtime. opencode is effectively “fresh Spawn + resumable child sessions” for converge purposes; `opencode run --fork` forks CLI sessions, not live in-conversation subagents. The safe adapter behavior is to degrade Executor to fresh Spawn and optionally optimize the handoff, not to treat CLI `--fork` as equivalent.
