# Paste into the InvenTree Django shell to verify the offer-feed ORM logic
# (no plugin install needed). Validates the field assumptions + prints samples.
from company.models import ManufacturerPart

rows, with_stock, errs = [], 0, []
for mp in ManufacturerPart.objects.select_related("part", "manufacturer").iterator():
    p = mp.part
    mpn = (mp.MPN or "").strip()
    if not mpn or p is None or not p.active:
        continue
    try:
        stock = p.total_stock                      # <-- assumption 1
    except Exception as e:
        errs.append(("total_stock", repr(e))); stock = None
    price = ""
    try:
        pr = getattr(p, "pricing", None)
        price = getattr(pr, "overall_min", None) if pr else None   # <-- assumption 2
    except Exception as e:
        errs.append(("pricing.overall_min", repr(e)))
    rows.append((mpn, mp.manufacturer.name if mp.manufacturer else "", p.IPN or "", stock, price))
    if stock and stock > 0:
        with_stock += 1

print(f"offer rows: {len(rows)}")
print(f"rows with stock > 0: {with_stock}")
print("field errors:", set(errs) or "none")
# single statement (executes even when the script is piped into the interactive shell)
print("sample:\n" + "\n".join("  MPN=%-22s mfr=%-20s SPN=%-16s stock=%s price=%s" % r for r in rows[:8]))
# the rows that actually carry stock (this is where your 100-stock part shows up)
stocked = [r for r in rows if r[3] and r[3] > 0]
print("\nstocked rows (%d):\n" % len(stocked)
      + "\n".join("  MPN=%-22s mfr=%-20s SPN=%-16s stock=%s" % (r[0], r[1], r[2], r[3]) for r in stocked))
