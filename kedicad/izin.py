"""Consent before anything is sent to the AI service.

WHY. The FreeCAD Addon Index rules for AI addons (Addon-Academy PR #61):
before any request reaches a remote AI service the addon asks for consent
INSIDE FreeCAD — a README notice is not enough — and the request names the
service and EVERY kind of data sent, including what is sent automatically.
Consent is asked again when the service or the kinds of data change.

HOW. Consent is stored as a SIGNATURE of the exact text the user agreed to
(service + data kinds). Change either and the stored signature no longer
matches, so the question comes back by itself — nobody has to remember to
bump a version number.

TWO DOORS, ONE RULE. The panel asks (ui/dock.py) and the transport refuses
to start claude.exe without it (transport.KaliciTransport.tur_gonder). The
second check is what makes this a guarantee: an automatic turn (code ran ->
results go back) also goes through the transport, and so would any future
path we forget to wire to the dialog.

No Qt here: the logic is tested headless (tests/test_yukleme_fc.py).
"""

from __future__ import annotations

import hashlib

from . import config

SERVIS = "Anthropic, through the Claude Code CLI installed on this computer"

# EVERY kind of data that leaves the machine. Derived from the code, not from
# memory: conversation.gonder (request + serializer.belge_metni), gorunum
# (screenshots) and the automatic turn after a run (output, errors,
# verification). If a new kind is sent, it MUST be added here — that also
# changes the signature and asks the user again.
VERI_TURLERI = (
    "your messages to the assistant",
    "a text description of the open document: its name and file path, "
    "object names, labels and types, sizes, positions and selected objects",
    "screenshots of the 3D view, when the assistant checks its work visually",
    "after you run code: its printed output, error messages and tracebacks, "
    "and the results of KediCAD's geometry checks",
    "the earlier messages of the same chat (the conversation continues)",
)

# What is NOT sent — said plainly, because it is the user's next question.
GONDERILMEYENLER = (
    "files on your disk (the assistant has no file access)",
    "anything while the panel is closed or before you agree",
)


def imza() -> str:
    """Short hash of the exact service + data kinds the user agrees to."""
    metin = SERVIS + "\n" + "\n".join(VERI_TURLERI)
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()[:16]


def verildi_mi() -> bool:
    return config.metin("Consent") == imza()


def ver() -> None:
    config.yaz("Consent", imza())


def geri_al() -> None:
    config.yaz("Consent", "")


def soru_metni() -> str:
    """The text of the consent dialog (plain text, also used in tests)."""
    satirlar = [
        "KediCAD sends your requests to an AI service so it can answer them.",
        "",
        "Service: " + SERVIS + ".",
        "",
        "What is sent:",
    ]
    satirlar += ["  • " + t for t in VERI_TURLERI]
    satirlar += ["", "What is not sent:"]
    satirlar += ["  • " + t for t in GONDERILMEYENLER]
    satirlar += [
        "",
        "Code the assistant writes runs only when you press Run, with your "
        "full permissions. Documents can contain hidden instructions written "
        "by someone else, so read the code before you run it.",
        "",
        "Anthropic's privacy policy applies to this data. You can withdraw "
        "consent at any time from the KediCAD menu.",
        "",
        "Allow KediCAD to send this data to Anthropic?",
    ]
    return "\n".join(satirlar)


REDDEDILDI = ("Nothing was sent. KediCAD needs your consent before it can "
              "send a request to Anthropic; it will ask again with your next "
              "message.")
