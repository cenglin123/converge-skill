5. Close completed agents: accurate and operationally important.

For independence:

- Every Reviewer should use a newly spawned agent with `fork_context:false`.
- Reusing a Reviewer through `send_input` preserves that Reviewer’s context and is suitable only for the same inner-loop review thread, not for a fresh-eyes round.
- A forked Executor inherits the Orchestrator’s framing and anchoring risks exactly as the plan anticipates.

H1’s generative boundary remains sound: inherited context should be limited to roles whose output is subsequently mechanically re-verified by a fresh, independently spawned reviewer. Codex can implement that boundary directly rather than degrading it to documentation convention.

Bottom line: Part B has a real Codex realization in version 0.141.0 through `multi_agent_v1.spawn_agent(fork_context=true)`; Codex is not fresh-only. The adapter should add this parameterized Spawn mode, retain fresh Spawn for every Reviewer, and keep Codex budget enforcement `auditable-only` until deny-before-spawn hook behavior is empirically proven.
tokens used
113,005
## Runtime identity

- Codex CLI: `codex-cli 0.141.0`
- Platform/build: npm installation, Windows x86-64; build commit reported as `unknown`.
- Feature flags:
  - `multi_agent`: stable, enabled
  - `hooks`: stable, enabled
  - `multi_agent_v2`: disabled, under development
  - `token_budget`: disabled, under development
- `multi_agent_v1`: exposed and successfully exercised.
- Workspace remained unchanged; `git status --short` was empty.

Evidence came from live tool schemas, `codex --version`, `codex doctor --json`, `codex features list`, CLI help, repository inspection, and read-only fresh/forked sub-agent probes. Official documentation lookup was unavailable in this read-only/network-restricted session, so hook details not established by runtime evidence are marked uncertain.

## 1. Context inheritance / fork

Yes. This runtime has a direct realization of Part B:

```text
multi_agent_v1.spawn_agent(
  message=...,
  fork_context=true
)
```

The exposed schema says:

> “True forks the current thread history into the new agent; false or omitted starts with only the initial prompt.”

I spawned both variants:

- `fork_context:true`: the child correctly summarized the parent user’s full requested report and named `refs/framework-adapters.md`.
- `fork_context:false`: the child did not receive the parent task. It still received baseline system/workspace instructions, including the encoding guidance. Therefore “fresh” means fresh relative to the parent conversation, not absence of system/developer/AGENTS context.

[UNCERTAIN] The runtime does not expose whether inherited history is always a byte-for-byte transcript, a model-visible event snapshot, or a compacted summary after context compaction. The verified semantic guarantee is inheritance of the current thread history as presented to the child.

Full-history forks must inherit the parent agent type, model, and reasoning effort. A probe that combined `fork_context:true` with `agent_type:"explorer"` was rejected with that exact constraint.

CLI commands are different:

- `codex fork [SESSION_ID] [PROMPT]` starts a new interactive session branched from a previously saved session.
- `codex resume [SESSION_ID] [PROMPT]` continues that saved interactive session.
- They operate on saved CLI sessions, not live child agents. They do not return a `multi_agent_v1` child handle or provide `send_input`/`wait_agent` orchestration.

Thus CLI `fork` alone is not a practical sub-agent adapter, but `multi_agent_v1.spawn_agent(fork_context=true)` is.

## 2. Fresh Spawn

Available and verified:

```text
multi_agent_v1.spawn_agent(
  message="self-contained prompt",
  fork_context=false   # or omitted
)
```

Prompt input can be passed as either:

- `message`: plain text
- `items`: structured text/image/local-image/skill/mention items

Return shape:

```json
{
  "agent_id": "019ee797-...",
  "nickname": "Copernicus"
}
```

`agent_id` is the stable instance identifier used by lifecycle calls.

Correction to [framework-adapters.md](/<user-home>/.agents/skills/converge/refs/framework-adapters.md:71): A.3 is broadly correct, but it is now incomplete because Spawn supports both fresh and inherited context.

## 3. Continue / Wait / Close

All are exposed and were exercised.

- Continue:

  ```text
  send_input(target=<agent_id>, message=...)
  ```

  It returns a `submission_id`, not the agent’s reply. My follow-up verified that prior child context was preserved.

- Wait:

  ```text
  wait_agent(targets=[...], timeout_ms=...)
  ```

  It returns per-agent status and `timed_out`. Completed status includes the final response.

- Close:

  ```text
  close_agent(target=<agent_id>)
  ```

  It returns the status observed before shutdown. Completed agents remain allocated until closed, so A.3 constraint #5 is accurate.

- Additional current capability not documented in A.3:

  ```text
  resume_agent(id=<agent_id>)
  ```

  I closed, resumed, continued, and waited on the same agent; its prior context remained available.

A.3 should clarify that Continue is `send_input` followed by `wait_agent`, not a single call returning the reply.

## 4. Blocking hook / budget enforcement

No verified Codex mechanism currently justifies extending converge’s spawn-cap tier to Codex.

Verified facts:

- Hooks are stable/enabled.
- CLI exposes hook-trust controls.
- Approval policies govern command execution/sandbox escalation.
- `notify` only injects output; it cannot deny a call.
- MCP gating is not applicable because `multi_agent_v1` is not an MCP server.
- No approval prompt or budget interceptor appeared before `spawn_agent`.
- `token_budget` is under development and disabled.

[UNCERTAIN] Codex hooks may support deny-capable pre-tool interception generally, but I could not verify that they see or can reject `multi_agent_v1.spawn_agent`. Feature presence alone is insufficient evidence.

Recommendation: keep Codex at `auditable-only` unless a real hook test proves that a configured pre-tool hook receives the spawn event and can prevent agent creation. Do not infer this from `hooks = stable`.

## 5. Per-subagent model selection

Yes, for ordinary fresh spawns. `spawn_agent` exposes:

- `model`
- `reasoning_effort`
- `service_tier`

The current schema advertised `gpt-5.5`, `gpt-5.4`, and `gpt-5.4-mini` overrides. The default is parent-model inheritance.

Therefore A.3 constraint #4 is a policy preference, not a capability limitation. It is accurate to prefer inheritance, but per-agent override is available.

Important fork restriction: full-history forks must inherit agent type, model, and reasoning effort. A per-fork model override is therefore not available in this runtime.

## 6. Runtime capability probing

Probe the callable tool schema, not only CLI version or feature flags:

1. Check whether `multi_agent_v1.spawn_agent` is actually exposed.
2. Inspect whether its input schema contains `fork_context`.
3. For fresh Spawn, omit it or set `false`.
4. For inherited Executor Spawn, set `true`.
5. Detect `send_input`, `wait_agent`, `close_agent`, and optionally `resume_agent` independently.
6. Treat unsupported parameter/tool errors as capability failure and degrade to fresh Spawn.

`codex features list` is useful supporting evidence—`multi_agent` is enabled here—but it does not prove that the host exposed the corresponding tools to the current agent.

A.5 should add a fourth adapter question: “Can Spawn inherit the current parent thread, and under what restrictions?” Wait/Close should also be treated as lifecycle capabilities even if they remain outside the three conceptual atoms.

## 7. Net assessment for Part B

Codex has a native, live equivalent: `spawn_agent(fork_context=true)`. It directly avoids an Executor having to reconstruct the Orchestrator’s conversation from a self-contained prompt.

The CLI’s saved-session `fork` is only a partial/manual analogue and should not be encoded as the adapter. Goals are also not a substitute: this runtime exposes thread goal-management tools, but no verified `/goal` facility that automatically runs an Executor/reviewer convergence loop. A.3’s `/goal` paragraph is therefore [UNCERTAIN] and should not claim current Codex support without a separate TUI probe.

The plan’s H3 premise that “only Claude Code truly uses fork” is now factually outdated. Codex also supports it in the active multi-agent runtime.

## 8. Agent-model implications and repository corrections

A.3 constraints:

1. Explicit authorization: accurate; the live schema requires delegation/sub-agent authorization.
2. No default nested spawn: accurate here. Both children reported no exposed `multi_agent_v1` tools.
3. Conservative file visibility: appropriate. Both children shared the same cwd and could read the repository. The tool guidance describes workers editing in a forked workspace and changes being uploaded for integration. Exact write propagation was not tested because this review was read-only.
4. Model inheritance: accurate as a default policy, but overrides exist for fresh agents; inherited-context forks must inherit.
5. Close completed agents: accurate and operationally important.

For independence:

- Every Reviewer should use a newly spawned agent with `fork_context:false`.
- Reusing a Reviewer through `send_input` preserves that Reviewer’s context and is suitable only for the same inner-loop review thread, not for a fresh-eyes round.
- A forked Executor inherits the Orchestrator’s framing and anchoring risks exactly as the plan anticipates.

H1’s generative boundary remains sound: inherited context should be limited to roles whose output is subsequently mechanically re-verified by a fresh, independently spawned reviewer. Codex can implement that boundary directly rather than degrading it to documentation convention.

Bottom line: Part B has a real Codex realization in version 0.141.0 through `multi_agent_v1.spawn_agent(fork_context=true)`; Codex is not fresh-only. The adapter should add this parameterized Spawn mode, retain fresh Spawn for every Reviewer, and keep Codex budget enforcement `auditable-only` until deny-before-spawn hook behavior is empirically proven.
