# Converge Archive Index

## Decision

- value: 可执行
- type: reviewer-verdict
- event: [event](evidence/events/00000007-40808243-c717-4682-a2d8-1036395ba26d.json)

## Integrity & Threat Boundary

- schema: `converge.archive 1.0`
- status: archived only when this directory is under the canonical done root and `check` reports valid
- guarantee: archive-time internal consistency, structural integrity, and traceable declared provenance
- does not guarantee: historical truth or resistance to a same-permission writer rewriting the whole archive and Git history

## Degradations

- model-provenance:configured
- model-provenance:unavailable
- permissions:acl-confidentiality-not-verified

## Revision Timeline

- current: r1

## Event Timeline

- 0001 `invocation-started` [4706bd4d-da2f-4445-bc2e-1d3df954fe12](evidence/events/00000001-4706bd4d-da2f-4445-bc2e-1d3df954fe12.json)
- 0002 `invocation-terminal` [cf06728c-35a9-42bf-a5b6-23cc67da7954](evidence/events/00000002-cf06728c-35a9-42bf-a5b6-23cc67da7954.json)
- 0003 `invocation-started` [1a20616c-6814-461d-abda-2fa8782af582](evidence/events/00000003-1a20616c-6814-461d-abda-2fa8782af582.json)
- 0004 `invocation-terminal` [b8c776b1-1a63-4e1c-825d-a097c6d05d16](evidence/events/00000004-b8c776b1-1a63-4e1c-825d-a097c6d05d16.json)
- 0005 `invocation-started` [bccd1e50-65bf-482f-8e27-e583477657b2](evidence/events/00000005-bccd1e50-65bf-482f-8e27-e583477657b2.json)
- 0006 `invocation-terminal` [8ddc663b-fbdc-49ec-9d0c-efad96d70518](evidence/events/00000006-8ddc663b-fbdc-49ec-9d0c-efad96d70518.json)
- 0007 `terminal-decision` [40808243-c717-4682-a2d8-1036395ba26d](evidence/events/00000007-40808243-c717-4682-a2d8-1036395ba26d.json)

## Model Provenance

- `4706bd4d-da2f-4445-bc2e-1d3df954fe12` invocation-started: requested=xiaomi/mimo-v2.5-pro; resolved=unavailable; evidence=pending; source=pending; reason=none
- `cf06728c-35a9-42bf-a5b6-23cc67da7954` invocation-terminal: requested=unavailable; resolved=unavailable; evidence=configured; source=cli_argument; reason=backend-does-not-expose
- `1a20616c-6814-461d-abda-2fa8782af582` invocation-started: requested=deepseek/deepseek-v4-flash; resolved=unavailable; evidence=pending; source=pending; reason=none
- `b8c776b1-1a63-4e1c-825d-a097c6d05d16` invocation-terminal: requested=unavailable; resolved=unavailable; evidence=unavailable; source=none; reason=invocation-failed-before-resolution
- `bccd1e50-65bf-482f-8e27-e583477657b2` invocation-started: requested=deepseek/deepseek-v4-pro; resolved=unavailable; evidence=pending; source=pending; reason=none
- `8ddc663b-fbdc-49ec-9d0c-efad96d70518` invocation-terminal: requested=unavailable; resolved=unavailable; evidence=configured; source=cli_argument; reason=backend-does-not-expose

## Artifact Provenance

- none

## Auxiliary Evidence (non-event-derived)

Imported and hash-verified, but not part of the event graph and not carrying any provenance
claim — see `EVIDENCE_RESERVED_SUBDIRS` in the Archive Contract for what *is* event-derived.

- none

## Residual Risks

- same-writer-rewrite-undetectable

## Next Reads

- [Final round](round-2.md)
- [Retrospective](retrospective.md)
- [Terminal decision evidence](evidence/events/00000007-40808243-c717-4682-a2d8-1036395ba26d.json)
