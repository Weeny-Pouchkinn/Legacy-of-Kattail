# Read-only painter prototype

1. Inspect actual HOI4 setup and the EU4 painter's flat Stellaris masks. Done.
2. Build a local desktop map browser with editable in-memory country/state and arbitrary script fields. Done.
3. Add tintable flat-mask flags at the three observed HOI4 dimensions. Done.
4. Build a separate, reviewable state-history culture/species migration experiment. Preserve runtime consumers and refuse unsupported startup logic. Done; staged, not installed.
5. Verify parser, draft isolation, real-data loading, migration equivalence and actual Tk controls. Done; 11 fixture checks, real-data UI/render/isolation checks and installer fixture checks passed. Packaged for the requested mod subfolder.

The live mod is outside the session's writable roots. All source data is read-only; installation must be performed by the user. No game launch or game-file export is part of the painter prototype.
