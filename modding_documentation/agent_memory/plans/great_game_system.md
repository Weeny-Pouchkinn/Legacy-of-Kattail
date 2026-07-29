# Signed-Axis Great Game System

## Status

- [x] Audit the replacement specification and reverted repository state.
- [x] Verify local event, decision, array, compliance, annexation, and scripted-localisation patterns.
- [x] Add constants, effects, triggers, decisions, scripted localisation, events, English localisation, and system documentation.
- [x] Add `lok_debug.22` for PRL versus MEW over WPR.
- [x] Complete static validation and resolve all relevant diagnostics.
- [ ] Exercise the required scenario matrix in Hearts of Iron IV.

## Decisions

- One active Great Game per country; live arrays are host-owned and UI/action values are participant-local.
- Country references use scope-valued variables and `var:<name>` scoping.
- Passive influence and final ownership are snapshotted before mutation.
- Failed starts retain staged inputs and set `lok_gg_setup_invalid`.
- The daily loop is scheduled only on each live host.

## Known validation boundary

The repository declares support for 1.17.*, while the locally installed game previously identified in this workspace is 1.19.2. Parser or runtime checks against that install do not prove strict 1.17 compatibility. In-game scenario tests remain required.
