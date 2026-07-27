# inventree-altium-bridge (InvenTree plugin)

One InvenTree plugin (mixins: Settings + Schedule + Urls) that bridges InvenTree with Altium
and the pick-and-place machine — no separate image, CronJob, or volume mounts.

- **Task A — offer feed OUT (implemented):** builds the Altium Custom-Parts-Provider feed from
  the ORM (per MPN: `Supplier=InvenTree, SPN=IPN, Stock, Price, ProductURL, Photo`) and writes
  `offers.csv` to an SMB share (Altium reads it). Also served at
  `…/plugin/altium-bridge/offers.csv`.
- **Task B — P&P stock IN (stub):** read the pick-and-place machine's stock file from an SMB
  share, pre-process, and update InvenTree stock. `import_pnp_stock()` is a documented stub —
  fill in once the machine's file format is known. This closes the loop: real stock → real
  quantities in the Altium tiles.

SMB is accessed directly via `smbprotocol` (credentials in plugin Settings), so **no k8s volume
mounts / deployment changes** — GitOps-friendly, and pip pulls the dependency on install.

## Install (your existing GitHub flow)
InvenTree Admin → Plugins → Install → repo URL `github.com/frickly-systems/inventree-altium-bridge`
(subdir `plugin/` if kept in this monorepo) + package name `inventree-altium-bridge`. pip pulls
`smbprotocol` automatically. Enable the plugin; it needs the "Enable Schedule Integration" +
"Enable URL Integration" plugin options for the scheduled tasks and the HTTP endpoint.

## Configure (plugin Settings)
`SUPPLIER_LABEL`, `MEDIA_BASE`, SMB `HOST/SHARE/USER/PASSWORD/DOMAIN`, `OFFERS_ENABLED`,
`OFFERS_PATH`, and (later) `PNP_IMPORT_ENABLED` / `PNP_PATH`.

## Altium side
Point the `.PrtSync` Custom Parts Provider config at the `offers.csv` on the share (file source),
map columns (see [../altium-provider/README.md](../altium-provider/README.md)), enable the
`EDMS.CustomOffersMerge` beta flag, schedule `ComponentSync.Executor.exe`.

## Status / validation
Syntax-checked here, but **not yet run inside InvenTree** — validate on your instance:
model field assumptions (`Part.total_stock`, `Part.pricing.overall_min`, `ManufacturerPart.MPN`)
and the mixin/scheduler API against your InvenTree version. The offer logic mirrors the
REST-based `altium-provider/gen_offers.py`, which is tested (5,501 rows) against the live instance.

## To implement Task B — share when ready
- A sample of the P&P machine's stock file (the "weird format").
- The SMB path to it, and how P&P part references map to InvenTree parts (IPN? MPN? a custom field?).
