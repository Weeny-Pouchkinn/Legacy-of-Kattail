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

## 2026-08-24 — Aggregate fiscal-capacity authority

Decision: represent the six independent government budget slots with shared `lok_fiscal_capacity_usage` modifier contributions, use `lok_base_fiscal_capacity` for the 100-point base, and keep variables as display/dynamic-effect mirrors rather than a second authority.

Rationale: this avoids six manually maintained usage variables while allowing any law add/remove to recalculate from current modifier totals. The overextension modifier reads the calculated penalty variable and applies only the requested political-power effect.

Consequences: changing a budget law triggers `LOK_update_fiscal_capacity`; the monthly fallback repairs or initializes missing slots. The first-pass system has no economy, money, debt, taxes, or prosperity layer.

## 2026-08-24 — Fiscal-capacity initialization fallback

Decision: initialize countries through the existing startup `every_possible_country` loop, known country-lifecycle hooks, and a monthly fallback because the current repository does not expose a verified generic country-created on-action.

Rationale: this covers scenario-start countries and the repository's known creation paths without inventing an unsupported on-action. The monthly pulse is explicitly requested and provides eventual coverage for other dynamically generated countries.

Consequences: a country created through an unrecognized path may lack the system until the next monthly pulse; this requires runtime testing against the declared game version.

## 2026-08-24 — Parliament consumes existing politics and freezes only election data

Decision: use the inspected ideology indices and tokens directly: `pol_party_array^0..^8` map to `communism`, `socialism`, `social_democratic`, `social_liberal`, `democratic`, `social_conservative`, `authoritarian_democratic`, `neutrality`, and `fascism`; `gestalt` is excluded completely. Treat `3` as hostile, `2` as coalition, and `1` as neutral, while detecting the ruling party through `has_government`.

Rationale: Parliament must observe the existing political system rather than create a second relation model. Persistent variables hold only election-time population, popularity snapshots, eligible popularity, total seats, and elected seats. Current hostility and government approval are calculated dynamically in scripted localisation.

Consequences: annual elections preserve frozen seat results between pulses; current bans and coalition/ruling changes immediately affect effective/supporting seats and approval. Party names are resolved from canonical dynamic `TAG_ideology_party` keys. The repository exposes no documented key-existence trigger, so a universal static fallback for missing party keys cannot be safely selected without runtime verification.
