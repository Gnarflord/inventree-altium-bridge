"""Build the Altium Custom-Parts-Provider offer feed straight from the InvenTree ORM.

One row per manufacturer-part MPN. Column headers match the exact parameter names Altium's
Custom Parts Provider import expects, so the .PrtSync mapping is 1:1:

  Manufacturer Name, Manufacturer Part Number, Supplier, Supplier Part Number,
  Description, Product Photo URL, Quantity, Currency, Price

ORM-based so it runs in-process inside the plugin — no REST, no token.
Output is comma-delimited UTF-8 **without a BOM** (Altium mis-reads the BOM as part of the
first header, e.g. "ï»¿Manufacturer Name").
"""
import csv
import io

COLS = [
    "Manufacturer Name",
    "Manufacturer Part Number",
    "Supplier",
    "Supplier Part Number",
    "Description",
    "Product Photo URL",
    "Quantity",
    "Currency",
    "Price",
]


def build_offer_rows(supplier_label="InvenTree", media_base=""):
    from company.models import ManufacturerPart
    from part.models import PartInternalPriceBreak

    # lowest-quantity internal price per part -> (amount, ISO currency) for Price/Currency columns
    price_by_part = {}
    for ipb in PartInternalPriceBreak.objects.all().order_by("part_id", "quantity"):
        if ipb.part_id not in price_by_part:
            price_by_part[ipb.part_id] = (ipb.price.amount, str(ipb.price.currency))

    rows = []
    qs = ManufacturerPart.objects.select_related("part", "manufacturer").all()
    for mp in qs.iterator():
        part = mp.part
        mpn = (mp.MPN or "").strip()
        if not mpn or part is None or not part.active:
            continue

        price, currency = price_by_part.get(part.pk, ("", ""))

        img = ""
        if getattr(part, "image", None):
            try:
                img = part.image.url
            except Exception:
                img = ""

        rows.append({
            "Manufacturer Name": mp.manufacturer.name if mp.manufacturer else "",
            "Manufacturer Part Number": mpn,
            "Supplier": supplier_label,
            "Supplier Part Number": part.IPN or "",
            "Description": (mp.description or part.description or ""),  # per-MPN desc if present
            "Product Photo URL": (media_base.rstrip("/") + img) if (img and media_base) else img,
            "Quantity": part.total_stock,                              # Decimal on-hand quantity
            "Currency": currency,                                      # ISO code, e.g. USD/EUR
            "Price": price,
        })
    rows.sort(key=lambda r: r["Manufacturer Part Number"])
    return rows


def offers_csv_bytes(supplier_label="InvenTree", media_base=""):
    """Return the offer feed as comma-delimited UTF-8 (no BOM) CSV bytes.

    The csv module auto-quotes any field that contains a comma/quote/newline, so commas in
    descriptions stay safe.
    """
    rows = build_offer_rows(supplier_label, media_base)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, delimiter=",")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8"), len(rows)   # plain UTF-8, no BOM
