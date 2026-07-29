# Architectural Decisions

## 2026-07-29 — Signed-axis Great Game data model

Decision: represent every contested state with one signed `lok_gg_influence` variable, use exactly one live game per country, store iteration arrays on the host, and mirror only UI/action/reference data to participants.

Rationale: this makes positive and negative competition directly comparable, prevents ambiguous multi-game participant state, and avoids host-side parallel actor metadata arrays.

Consequences: supporters never receive states; their `lok_gg_beneficiary_ref` points to a principal. Participant decisions can read local round data without unsupported owner-variable localisation chains.

## 2026-07-29 — Event-driven bounded processing

Decision: schedule one daily event only on each active host. AI selection is recalculated per action from bounded host-state arrays; spill and settlement use snapshot phases.

Rationale: avoid global recurring scans and iteration-order-dependent outcomes.

Consequences: cost scales with configured participants, their actions, and the host's disputed states. The constants cap participants at 50, actions at 20, and rounds at 200.

## 2026-07-29 — Failed setup and landless-host handling

Decision: failed setup retains staged inputs and sets `lok_gg_setup_invalid`; successful setup clears staging. If settlement transfers every host state, the former-capital recipient annexes the now-landless host after the state split.

Rationale: retained staging is inspectable during content debugging, while post-transfer annexation provides an explicit unit/country cleanup path without letting annexation decide the multi-recipient state distribution.

Consequences: content should call `lok_begin_great_game_configuration` before retrying. Landless annexation semantics remain an explicitly documented in-game validation requirement.
