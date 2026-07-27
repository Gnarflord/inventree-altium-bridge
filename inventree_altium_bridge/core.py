"""InvenTree -> Altium bridge plugin.

Exports a Custom-Parts-Provider offer feed (per-MPN: our stock, IPN, price, currency, photo)
to an SMB share Altium reads; also served over HTTP at /plugin/altium-bridge/offers.csv.
"""
from django.http import HttpResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _

from . import ALTIUM_BRIDGE_VERSION
from .offers import offers_csv_bytes

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, ScheduleMixin, UrlsMixin


class AltiumBridgePlugin(SettingsMixin, ScheduleMixin, UrlsMixin, InvenTreePlugin):
    """Exports an Altium Custom-Parts-Provider offer feed from InvenTree."""

    AUTHOR = "Jan Wolf"
    DESCRIPTION = "Export an Altium Custom-Parts-Provider offer feed (stock/price/IPN) via SMB + HTTP."
    VERSION = ALTIUM_BRIDGE_VERSION
    MIN_VERSION = "0.16.0"

    NAME = "Altium Bridge"
    SLUG = "altium-bridge"
    TITLE = "InvenTree -> Altium Bridge"

    SETTINGS = {
        "SUPPLIER_LABEL": {
            "name": _("Supplier label"),
            "description": _("Name shown as the supplier tile in Altium (e.g. InvenTree)"),
            "default": "InvenTree",
        },
        "MEDIA_BASE": {
            "name": _("Media base URL"),
            "description": _("Prefix for relative part image paths in the Photo column"),
            "default": "",
        },
        "OFFERS_ENABLED": {
            "name": _("Export offer feed"), "description": _("Write offers.csv to the SMB share on schedule"),
            "default": True, "validator": bool,
        },
        "OFFERS_PATH": {
            "name": _("Offers file path"), "description": _("Path on the share for the offer CSV"),
            "default": "altium/v_altium_offers.csv",
        },
        # --- SMB target for the offer file ---
        "SMB_HOST": {"name": _("SMB host"), "description": _("SMB/CIFS server host or IP"), "default": ""},
        "SMB_SHARE": {"name": _("SMB share"), "description": _("Share name"), "default": ""},
        "SMB_USER": {"name": _("SMB user"), "default": ""},
        "SMB_PASSWORD": {"name": _("SMB password"), "default": "", "protected": True},
        "SMB_DOMAIN": {"name": _("SMB domain"), "default": ""},
    }

    # InvenTree background scheduler picks these up (django-q). Cadence in minutes.
    SCHEDULED_TASKS = {
        "export_offers": {"func": "export_offers", "schedule": "I", "minutes": 60},
    }

    # ---- offer feed export ---------------------------------------------------------
    def export_offers(self):
        if not self.get_setting("OFFERS_ENABLED"):
            return
        data, n = offers_csv_bytes(self.get_setting("SUPPLIER_LABEL"), self.get_setting("MEDIA_BASE"))
        from .smb import write_bytes
        target = write_bytes(
            self.get_setting("SMB_HOST"), self.get_setting("SMB_SHARE"), self.get_setting("OFFERS_PATH"),
            data, self.get_setting("SMB_USER"), self.get_setting("SMB_PASSWORD"), self.get_setting("SMB_DOMAIN"),
        )
        print(f"[altium-bridge] exported {n} offer rows -> {target}")

    # ---- HTTP: also serve the offer feed at /plugin/altium-bridge/offers.csv -------
    def setup_urls(self):
        return [path("offers.csv", self.view_offers, name="offers")]

    def view_offers(self, request):
        data, _n = offers_csv_bytes(self.get_setting("SUPPLIER_LABEL"), self.get_setting("MEDIA_BASE"))
        resp = HttpResponse(data, content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = "attachment; filename=v_altium_offers.csv"
        return resp
