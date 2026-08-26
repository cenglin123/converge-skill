# Converge Archive Index

## Decision

- value: 可执行
- type: reviewer-verdict
- event: [event](evidence/events/00000017-308c7258-85ad-491e-bd19-10e225c417e1.json)

## Integrity & Threat Boundary

- schema: `converge.archive 1.0`
- status: archived only when this directory is under the canonical done root and `check` reports valid
- guarantee: archive-time internal consistency, structural integrity, and traceable declared provenance
- does not guarantee: historical truth or resistance to a same-permission writer rewriting the whole archive and Git history

## Degradations

- model-provenance:configured
- permissions:acl-confidentiality-not-verified

## Revision Timeline

- current: r1

## Event Timeline

- 0001 `invocation-started` [34b2b7e8-ca35-4220-bc0a-b576b90d0403](evidence/events/00000001-34b2b7e8-ca35-4220-bc0a-b576b90d0403.json)
- 0002 `invocation-started` [fe9340a7-e53c-425c-94d5-19063e31258b](evidence/events/00000002-fe9340a7-e53c-425c-94d5-19063e31258b.json)
- 0003 `invocation-started` [4d8b91c5-5489-4564-9fda-480feba2184d](evidence/events/00000003-4d8b91c5-5489-4564-9fda-480feba2184d.json)
- 0004 `invocation-terminal` [d23da73f-f3d5-46d1-92a2-6d6794ac1d51](evidence/events/00000004-d23da73f-f3d5-46d1-92a2-6d6794ac1d51.json)
- 0005 `invocation-terminal` [f2e8ee46-5397-4019-97fe-ff7186ed2137](evidence/events/00000005-f2e8ee46-5397-4019-97fe-ff7186ed2137.json)
- 0006 `invocation-terminal` [8ce26274-8d78-4dcb-ad8e-eb7a7bb8ed50](evidence/events/00000006-8ce26274-8d78-4dcb-ad8e-eb7a7bb8ed50.json)
- 0007 `invocation-started` [32d1290c-7195-404d-8650-28867d905379](evidence/events/00000007-32d1290c-7195-404d-8650-28867d905379.json)
- 0008 `invocation-started` [2d373ccf-ce6e-4577-8c13-de60382fec24](evidence/events/00000008-2d373ccf-ce6e-4577-8c13-de60382fec24.json)
- 0009 `invocation-terminal` [f3ae3f82-2b9a-47c2-b00d-2bc57ca7bfa0](evidence/events/00000009-f3ae3f82-2b9a-47c2-b00d-2bc57ca7bfa0.json)
- 0010 `invocation-terminal` [747be20d-6ff4-4d51-8f38-f4c9e79eab25](evidence/events/00000010-747be20d-6ff4-4d51-8f38-f4c9e79eab25.json)
- 0011 `invocation-started` [30e1239e-45bd-4017-a4eb-ba59fb44fbcc](evidence/events/00000011-30e1239e-45bd-4017-a4eb-ba59fb44fbcc.json)
- 0012 `invocation-terminal` [c7a36f14-3625-4837-9d38-82e7a028bab6](evidence/events/00000012-c7a36f14-3625-4837-9d38-82e7a028bab6.json)
- 0013 `invocation-started` [121dc200-5697-4001-bbc1-d6bba6f72efd](evidence/events/00000013-121dc200-5697-4001-bbc1-d6bba6f72efd.json)
- 0014 `invocation-started` [a8c0b734-2603-4ad0-b072-eb738a108b91](evidence/events/00000014-a8c0b734-2603-4ad0-b072-eb738a108b91.json)
- 0015 `invocation-terminal` [cde8dfdb-6533-493b-ae29-54db67d9f0e4](evidence/events/00000015-cde8dfdb-6533-493b-ae29-54db67d9f0e4.json)
- 0016 `invocation-terminal` [7ca93e47-5638-4640-a61f-d4408f95b413](evidence/events/00000016-7ca93e47-5638-4640-a61f-d4408f95b413.json)
- 0017 `terminal-decision` [308c7258-85ad-491e-bd19-10e225c417e1](evidence/events/00000017-308c7258-85ad-491e-bd19-10e225c417e1.json)

## Model Provenance

- `34b2b7e8-ca35-4220-bc0a-b576b90d0403` invocation-started: requested=deepseek-official/deepseek-v4-flash; resolved=unavailable; evidence=pending; source=pending; reason=none
- `fe9340a7-e53c-425c-94d5-19063e31258b` invocation-started: requested=deepseek-official/deepseek-v4-flash; resolved=unavailable; evidence=pending; source=pending; reason=none
- `4d8b91c5-5489-4564-9fda-480feba2184d` invocation-started: requested=deepseek-official/deepseek-v4-flash; resolved=unavailable; evidence=pending; source=pending; reason=none
- `d23da73f-f3d5-46d1-92a2-6d6794ac1d51` invocation-terminal: requested=unavailable; resolved=unavailable; evidence=configured; source=cli_argument; reason=backend-does-not-expose
- `f2e8ee46-5397-4019-97fe-ff7186ed2137` invocation-terminal: requested=unavailable; resolved=unavailable; evidence=configured; source=cli_argument; reason=backend-does-not-expose
- `8ce26274-8d78-4dcb-ad8e-eb7a7bb8ed50` invocation-terminal: requested=unavailable; resolved=unavailable; evidence=configured; source=cli_argument; reason=backend-does-not-expose
- `32d1290c-7195-404d-8650-28867d905379` invocation-started: requested=unavailable; resolved=unavailable; evidence=pending; source=pending; reason=none
- `2d373ccf-ce6e-4577-8c13-de60382fec24` invocation-started: requested=deepseek-official/deepseek-v4-flash; resolved=unavailable; evidence=pending; source=pending; reason=none
- `f3ae3f82-2b9a-47c2-b00d-2bc57ca7bfa0` invocation-terminal: requested=unavailable; resolved=unavailable; evidence=configured; source=cli_argument; reason=backend-does-not-expose
- `747be20d-6ff4-4d51-8f38-f4c9e79eab25` invocation-terminal: requested=unavailable; resolved=unavailable; evidence=configured; source=cli_argument; reason=backend-does-not-expose
- `30e1239e-45bd-4017-a4eb-ba59fb44fbcc` invocation-started: requested=unavailable; resolved=unavailable; evidence=pending; source=pending; reason=none
- `c7a36f14-3625-4837-9d38-82e7a028bab6` invocation-terminal: requested=unavailable; resolved=unavailable; evidence=configured; source=cli_argument; reason=backend-does-not-expose
- `121dc200-5697-4001-bbc1-d6bba6f72efd` invocation-started: requested=deepseek-official/deepseek-v4-flash; resolved=unavailable; evidence=pending; source=pending; reason=none
- `a8c0b734-2603-4ad0-b072-eb738a108b91` invocation-started: requested=unavailable; resolved=unavailable; evidence=pending; source=pending; reason=none
- `cde8dfdb-6533-493b-ae29-54db67d9f0e4` invocation-terminal: requested=unavailable; resolved=unavailable; evidence=configured; source=cli_argument; reason=backend-does-not-expose
- `7ca93e47-5638-4640-a61f-d4408f95b413` invocation-terminal: requested=unavailable; resolved=unavailable; evidence=configured; source=cli_argument; reason=backend-does-not-expose

## Artifact Provenance

- none

## Auxiliary Evidence (non-event-derived)

Imported and hash-verified, but not part of the event graph and not carrying any provenance
claim — see `EVIDENCE_RESERVED_SUBDIRS` in the Archive Contract for what *is* event-derived.

- none

## Residual Risks

- same-writer-rewrite-undetectable

## Next Reads

- [Final round](round-1.md)
- [Retrospective](retrospective.md)
- [Terminal decision evidence](evidence/events/00000017-308c7258-85ad-491e-bd19-10e225c417e1.json)
- [Design-review highlights](design-review.md)
