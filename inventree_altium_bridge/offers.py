"""Build the Altium Custom-Parts-Provider offer feed straight from the InvenTree ORM.

One row per manufacturer-part MPN: MPN, Manufacturer, Supplier(=InvenTree), SPN(=IPN),
Stock, Price, Currency, ProductURL, Photo.  (Mirror of altium-provider/gen_offers.py,
but ORM-based so it runs in-process inside the plugin — no REST, no token.)
"""
import csv
import io

COLS = ["MPN", "Manufacturer", "Supplier", "SPN", "Stock", "Price", "Currency", "ProductURL", "Photo"]


def build_offer_rows(supplier_label="InvenTree", media_base=""):
    from company.models import ManufacturerPart

    rows = []
    qs = ManufacturerPart.objects.select_related("part", "manufacturer").all()
    for mp in qs.iterator():
        part = mp.part
        mpn = (mp.MPN or "").strip()
        if not mpn or part is None or not part.active:
            continue

        # internal price (rolled-up part pricing), if computed
        price = ""
        pricing = getattr(part, "pricing", None)
        if pricing is not None and getattr(pricing, "overall_min", None) is not None:
            price = pricing.overall_min

        img = ""
        if getattr(part, "image", None):
            try:
                img = part.image.url
            except Exception:
                img = ""

        rows.append({
            "MPN": mpn,
            "Manufacturer": mp.manufacturer.name if mp.manufacturer else "",
            "Supplier": supplier_label,
            "SPN": part.IPN or "",
            "Stock": part.total_stock,                       # Decimal on-hand quantity
            "Price": price,
            "Currency": "",
            "ProductURL": part.link or "",
            "Photo": (media_base.rstrip("/") + img) if (img and media_base) else img,
        })
    rows.sort(key=lambda r: r["MPN"])
    return rows


def offers_csv_bytes(supplier_label="InvenTree", media_base=""):
    """Return the offer feed as UTF-8-BOM, ';'-delimited CSV bytes (Altium/Excel friendly)."""
    rows = build_offer_rows(supplier_label, media_base)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, delimiter=";")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8-sig"), len(rows)
