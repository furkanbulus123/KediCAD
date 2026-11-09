"""Eklentinin FreeCAD tarafindan yuklenebilirligini arayuzsuz dogrular.

    "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" tests\\test_yukleme_fc.py

Sinadigi seyler:
  * package.xml FreeCAD'in KENDI ayristiricisindan geciyor mu
  * Mod klasorundeki junction gorunuyor mu
  * Arayuz disi moduller FreeCAD'in Python 3.11'inde import edilebiliyor mu
    (3D_Models venv'i 3.12; buradaki kod ikisinde de calismali)

FreeCADGui gerektiren moduller (commands, ui.*) BILEREK sinanmiyor -
konsol modunda FreeCADGui yok.

NOT: freecadcmd icinde Qt import edilince sys.stdout yeniden yonlendiriliyor
ve print() ciktisi kayboluyor. Rapor bu yuzden DOSYAYA da yaziliyor:
tests/_son_rapor.txt
"""

import os
import sys
import traceback

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

# Testler GERCEK LOG/ klasorune yazmasin (bkz. sohbet_log modul basligi):
# olculdu, suite her kosusta oraya ~10 dosya birakiyordu ve kullanicinin
# gercek oturum gunlukleriyle karisiyordu.
os.environ["KEDICAD_LOG_DIR"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_gunlukler")

import FreeCAD as App

gecti = basarisiz = 0
_satirlar = []
RAPOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_son_rapor.txt")


def yaz(s):
    _satirlar.append(str(s))
    try:
        print(s)
    except Exception:
        pass


def kontrol(ad, kosul, ek=""):
    global gecti, basarisiz
    if kosul:
        gecti += 1
        yaz("  OK   %s" % ad)
    else:
        basarisiz += 1
        yaz("  HATA %s   %s" % (ad, ek))


def raporu_kaydet():
    with open(RAPOR, "w", encoding="utf-8") as f:
        f.write("\n".join(_satirlar) + "\n")


yaz("1) python surumu: %s" % sys.version.split()[0])
kontrol("FreeCAD Python 3.11", sys.version_info[:2] == (3, 11), sys.version_info[:2])

yaz("2) package.xml - FreeCAD'in kendi ayristiricisi")
try:
    m = App.Metadata(os.path.join(KOK, "package.xml"))
    kontrol("ayristi", True)
    kontrol("ad KediCAD", m.Name == "KediCAD", m.Name)
    kontrol("surum var", str(m.Version) != "", m.Version)
    icerik = m.Content
    kontrol("workbench icerigi var", "workbench" in icerik, list(icerik.keys()))
    wb = icerik["workbench"][0]
    kontrol("classname dogru", wb.Classname == "KediCADWorkbench", wb.Classname)
    kontrol("subdirectory kok", wb.Subdirectory in ("./", ".", "./\\", ".\\"),
            repr(wb.Subdirectory))
    kontrol("bu FreeCAD surumunu destekliyor", m.supportsCurrentFreeCAD())
except Exception:
    kontrol("ayristi", False, traceback.format_exc())

yaz("3) Mod klasorundeki junction")
mod = os.path.join(App.getUserAppDataDir(), "Mod")
hedef = os.path.join(mod, "KediCAD")
kontrol("user Mod dizini var", os.path.isdir(mod), mod)
kontrol("KediCAD gorunuyor", os.path.isdir(hedef), hedef)
kontrol("InitGui.py erisilebilir", os.path.isfile(os.path.join(hedef, "InitGui.py")))

yaz("4) arayuz disi modul importlari")
for ad in ("kedicad", "kedicad.log", "kedicad.config", "kedicad.locate",
           "kedicad.execution.blocks", "kedicad.execution.executor",
           "kedicad.context.serializer", "kedicad.transport.framing"):
    try:
        __import__(ad)
        kontrol(ad, True)
    except Exception:
        kontrol(ad, False, traceback.format_exc(limit=2))

yaz("5) PySide (QtCore) FreeCAD icinde")
try:
    from PySide import QtCore  # noqa: F401
    kontrol("PySide shim calisiyor", True)
    import kedicad.transport.process  # noqa: F401
    import kedicad.transport.transport  # noqa: F401
    kontrol("transport modulleri import edildi", True)
except Exception:
    kontrol("PySide/transport", False, traceback.format_exc(limit=3))

yaz("5b) ust serit modulu (kullanici 'ust menu yok' dedi)")
try:
    from kedicad import commands as _kmd
    from kedicad.ui import ust_menu as _ust
    kontrol("ust_menu import edildi", True)
    kontrol("QAction bulundu (PySide6'da QtGui'ye tasindi)",
            _ust.QAction is not None)
    # Ust serit artik komutlarin HEPSINI degil, yalnizca paneli acani
    # gosteriyor. Kullanici: "sadece logosu gozuksun", "AI ile geri al
    # falan gozukmesin". Bu yuzden kontrol "esitlik" degil "ALT KUME":
    # ust seritteki her komut kayitli olmali, ama her kayitli komut ust
    # seritte olmak zorunda degil.
    kayitli = {a for a, _ in _kmd.KOMUTLAR}
    kontrol("ust serit komutlari kayitli komutlarin alt kumesi",
            set(_ust._KOMUT_ADLARI) <= kayitli,
            (_ust._KOMUT_ADLARI, sorted(kayitli)))
    kontrol("ust seritte YALNIZCA paneli acan komut var",
            tuple(_ust._KOMUT_ADLARI) == ("KediCAD_ShowPanel",),
            _ust._KOMUT_ADLARI)
    # Geri al komutu KAYBOLMADI - workbench'in kendi menusunde duruyor.
    kontrol("geri al komutu hala kayitli (workbench menusunde)",
            "KediCAD_UndoLastAIChange" in kayitli, sorted(kayitli))
    # Metin degil logo gosterilecek: ikon dosyasi gercekten bulunmali,
    # yoksa ikon-only cubukta tiklanamaz bir bosluk olur.
    import os as _os
    _ikon_yolu = _os.path.join(KOK, "resources", "icons", "kedicad.svg")
    kontrol("logo dosyasi var (ikon-only cubugun tek anlatimi)",
            _os.path.exists(_ikon_yolu), _ikon_yolu)
    # GUI yok: yerlestir() PATLAMADAN sessizce ertelemeli.
    _ust.yerlestir()
    kontrol("GUI yokken yerlestir() patlamiyor", True)
    kontrol("tazeleme fonksiyonu var (menu cubugu yeniden kuruluyor)",
            callable(getattr(_ust, "_tazele", None)))
    # Addon Index: eklentinin araç cubugu kendi workbench'inde kalmali.
    # Her yerdeki kedi dugmesi artik ISTEGE BAGLI, varsayilan KAPALI.
    from kedicad import config as _ayar
    kontrol("ShowEverywhere varsayilani KAPALI",
            _ayar.VARSAYILAN.get("ShowEverywhere") is False,
            _ayar.VARSAYILAN.get("ShowEverywhere"))
    kontrol("ayar komutu kayitli (KediCAD menusunde)",
            "KediCAD_ShowEverywhere" in kayitli, sorted(kayitli))
    kontrol("ayar komutu workbench arac cubugunda DEGIL",
            "KediCAD_ShowEverywhere" not in _kmd.ARAC_CUBUGU, _kmd.ARAC_CUBUGU)
    kontrol("ayar komutu isaretlenebilir (Checkable)",
            "Checkable" in dict(_kmd.KOMUTLAR)["KediCAD_ShowEverywhere"]
            .GetResources())
    _ust.kaldir()
    _ust._tazele()
    kontrol("GUI yokken kaldir()/_tazele() patlamiyor", True)
    _initgui = open(_os.path.join(KOK, "InitGui.py"), encoding="utf-8").read()
    kontrol("InitGui sys.path'e eklemiyor (Addon Index kurali)",
            "sys.path.insert" not in _initgui
            and "sys.path.append" not in _initgui)
    kontrol("InitGui ust seridi ayara bagli kuruyor",
            'bayrak("ShowEverywhere")' in _initgui)
except Exception:
    kontrol("ust serit modulu", False, traceback.format_exc(limit=3))

# Ad degisikligi (v0.3.0, CADdy -> KediCAD): eski ayarlar bir kez tasinir.
# Gercek kullanici ayarlarina DOKUNMAMAK icin gecici gruplarla sinanir.
yaz("5c) eski ad altindaki ayarlar tasiniyor mu")
try:
    from kedicad import config as _ayar
    _mod = App.ParamGet("User parameter:BaseApp/Preferences/Mod")
    for _g in ("KediCADTestEski", "KediCADTestYeni", "KediCADTestYeni2"):
        _mod.RemGroup(_g)
    _eski = _mod.GetGroup("KediCADTestEski")
    _eski.SetString("Model", "sonnet")
    _eski.SetBool("ShowEverywhere", True)
    _eski.SetInt("PanelYuzde", 33)
    _yeni = _mod.GetGroup("KediCADTestYeni")
    _n = _ayar.eski_ayarlari_tasi(App, _yeni, "KediCADTestEski")
    kontrol("uc ayar tasindi", _n == 3, _n)
    kontrol("degerler ayni", _yeni.GetString("Model") == "sonnet"
            and _yeni.GetBool("ShowEverywhere") is True
            and _yeni.GetInt("PanelYuzde") == 33, _yeni.GetContents())
    _yeni.SetString("Model", "opus")
    kontrol("yeni grup doluyken tekrar tasimiyor",
            _ayar.eski_ayarlari_tasi(App, _yeni, "KediCADTestEski") == 0
            and _yeni.GetString("Model") == "opus")
    _bos = _mod.GetGroup("KediCADTestYeni2")
    kontrol("eski grup yoksa olusturmuyor",
            _ayar.eski_ayarlari_tasi(App, _bos, "KediCADTestYok") == 0
            and not _mod.HasGroup("KediCADTestYok"))
    for _g in ("KediCADTestEski", "KediCADTestYeni", "KediCADTestYeni2"):
        _mod.RemGroup(_g)
except Exception:
    kontrol("ayar tasima", False, traceback.format_exc(limit=3))

# Addon Index AI kurallari (Addon-Academy #61): veri gondermeden ONCE
# FreeCAD icinde izin; kullanicinin kendi Claude kurulumu oturuma sizmaz.
yaz("5d) veri paylasim izni ve CLI yalitimi")
try:
    from kedicad import config as _ayar, izin as _izin
    _onceki = _ayar.metin("Consent")
    try:
        kontrol("izin varsayilani BOS (verilmemis)",
                _ayar.VARSAYILAN.get("Consent") == "")
        _ayar.yaz("Consent", "")
        kontrol("izin yokken verildi_mi False", _izin.verildi_mi() is False)
        _izin.ver()
        kontrol("ver() sonrasi True", _izin.verildi_mi() is True)
        _eski_turler = _izin.VERI_TURLERI
        _izin.VERI_TURLERI = _eski_turler + ("yeni bir veri turu",)
        kontrol("veri turu degisince izin YENIDEN soruluyor",
                _izin.verildi_mi() is False)
        _izin.VERI_TURLERI = _eski_turler
        kontrol("ayni metne donunce yine gecerli", _izin.verildi_mi() is True)
        _izin.geri_al()
        kontrol("geri_al() sonrasi False", _izin.verildi_mi() is False)
        _soru = _izin.soru_metni()
        kontrol("soru servisi adiyla soyluyor", "Anthropic" in _soru)
        kontrol("soru HER veri turunu sayiyor",
                all(t in _soru for t in _izin.VERI_TURLERI))
        kontrol("ekran goruntusu ve dosya yolu acikca yaziyor",
                "screenshots" in _soru and "file path" in _soru)
        kontrol("izni geri alma komutu kayitli",
                "KediCAD_WithdrawConsent" in kayitli, sorted(kayitli))
        kontrol("InitGui menude geri alma komutu var",
                "KediCAD_WithdrawConsent" in _initgui)

        # Transport kapisi: izin yokken claude.exe BASLAMAZ, tur hata ile biter.
        from PySide import QtCore as _QC
        _app = _QC.QCoreApplication.instance() or _QC.QCoreApplication([])
        from kedicad.transport import transport as _T
        _t = _T.KaliciTransport()
        _sonuclar = []
        _t.tur_bitti.connect(_sonuclar.append)
        _t.tur_gonder("merhaba")
        kontrol("izin yokken tur reddedildi",
                len(_sonuclar) == 1 and _sonuclar[0].hata_mi
                and _sonuclar[0].aciklama == _izin.REDDEDILDI,
                [getattr(s, "aciklama", s) for s in _sonuclar])
        kontrol("izin yokken claude.exe baslamadi",
                not _t._proc.calisiyor_mu())
        kontrol("reddedilen tur transport'u mesgul birakmadi",
                not _t.mesgul_mu())

        _argv = _t._argv()
        kontrol("MCP sunuculari kapali (--strict-mcp-config)",
                "--strict-mcp-config" in _argv and "--mcp-config" not in _argv)
        kontrol("kullanici ayarlari yuklenmiyor (--setting-sources project)",
                "--setting-sources" in _argv
                and _argv[_argv.index("--setting-sources") + 1] == "project")
        kontrol("model araclari hala kapali (--tools '')",
                _argv[_argv.index("--tools") + 1] == "")
        _brief = _argv[_argv.index("--append-system-prompt-file") + 1]
        kontrol("brief dosya olarak veriliyor ve var",
                _os.path.isfile(_brief) and _brief.endswith("CLAUDE.md"), _brief)
        _ortam = _t._proc._ortam()
        kontrol("CLAUDE.md otomatik yukleme kapali",
                _ortam.value("CLAUDE_CODE_DISABLE_CLAUDE_MDS") == "1")
        kontrol("otomatik hafiza kapali",
                _ortam.value("CLAUDE_CODE_DISABLE_AUTO_MEMORY") == "1")
        _gd = str(_ayar.gecici_dizini())
        kontrol("ekran goruntusu klasoru eklentinin icinde",
                _gd.startswith(str(_ayar.eklenti_dizini())), _gd)
    finally:
        _ayar.yaz("Consent", _onceki)
except Exception:
    kontrol("izin / yalitim", False, traceback.format_exc(limit=4))

yaz("6) claude.exe bulunabiliyor mu")
try:
    from kedicad import locate
    yol = locate.claude_exe()
    kontrol("bulundu", os.path.isfile(str(yol)), yol)
    yaz("     %s" % yol)
except Exception as e:
    kontrol("bulundu", False, str(e))

yaz("7) belge serilestirici")
try:
    from kedicad.context import serializer
    doc = App.newDocument("SerTest")
    k = doc.addObject("Part::Box", "Kutu")
    k.Length = 12
    doc.recompute()
    metin = serializer.belge_metni(doc)
    kontrol("<document> uretti", metin.startswith("<document>"))
    kontrol("nesneyi listeledi", "Kutu" in metin and "Part::Box" in metin)
    kontrol("olcu var", "12" in metin, metin[:300])
    kontrol("butce icinde", len(metin) < serializer.BUTCE)
    App.closeDocument(doc.Name)
except Exception:
    kontrol("serilestirici", False, traceback.format_exc(limit=3))

yaz("")
yaz("%d gecti, %d basarisiz" % (gecti, basarisiz))
raporu_kaydet()
if basarisiz:
    sys.exit(1)
