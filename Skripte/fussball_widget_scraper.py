#!/usr/bin/env python3
"""
fussball_widget_scraper.py
==========================
Scrapt von fussball.de:
  1. Nächste Spiele der SGM ABI (mehrere Teams)
  2. Aktuelle Ligatabelle (mit Hervorhebung von ABI)

Lädt die fertigen HTML-Dateien per SFTP auf IONOS hoch.
Zugangsdaten werden aus Umgebungsvariablen gelesen (GitHub Secrets).

Abhängigkeiten:
    pip install requests beautifulsoup4 paramiko
"""

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import html as html_module
import paramiko

# ── Konfiguration ──────────────────────────────────────────────────────────────

TEAMS = [
    {
        "name": "A-Junioren ABI",
        "team_id": "011MIB1QNG000000VTVG0001VTR8C1K7",
        "output": "komplett_A.html",
    },
    {
        "name": "B-Junioren ABI",
        "team_id": "01OQR89UAC000000VV0AG80NVU94JLT0",
        "output": "komplett_B.html",
    },
    {
        "name": "C-Junioren ABI",
        "team_id": "020CNNEK1G000000VS548984VS7EIAOE",
        "output": "komplett_C.html",
    },
    {
        "name": "D1-Junioren ABI",
        "team_id": "011MICMDO8000000VTVG0001VTR8C1K7",
        "output": "komplett_D1.html",
    },
    {
        "name": "D2-Junioren ABI",
        "team_id": "011MIBO1P0000000VTVG0001VTR8C1K7",
        "output": "komplett_D2.html",
    },
]

SAISON = "2526"
MAX_SPIELE = 5
OUR_TEAM_FRAGMENT = "ABI"

# SFTP-Konfiguration – Werte kommen aus Umgebungsvariablen (GitHub Secrets)
SFTP_HOST = os.environ.get("SFTP_HOST", "home680099039.1and1-data.host")
SFTP_PORT = int(os.environ.get("SFTP_PORT", "22"))
SFTP_USER = os.environ.get("SFTP_USER", "u89169696")
SFTP_PASS = os.environ.get("SFTP_PASS", "")

# Zielverzeichnis auf dem IONOS-Server (Pfad anpassen!)
# Typischer IONOS-Pfad: /var/www/vhosts/deinedomain.de/httpdocs/abi-widgets/
SFTP_REMOTE_DIR = os.environ.get("SFTP_REMOTE_DIR", "/abi-widgets/")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9",
}

# ── Gemeinsames CSS ────────────────────────────────────────────────────────────

SHARED_CSS = """
<style>
/* ── ABI Widgets allgemein ── */
.abi-widget {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
  font-size: 0.92em;
  margin: 1.2em 0;
}
.abi-widget-titel {
  font-size: 1em;
  font-weight: 700;
  color: #1159af;
  margin-bottom: 0.5em;
  padding-bottom: 4px;
  border-bottom: 2px solid #1159af;
}
.abi-table {
  width: 100%;
  border-collapse: collapse;
}
.abi-table thead tr {
  background-color: #1159af;
  color: #fff;
}
.abi-table thead th {
  padding: 7px 9px;
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
}
.abi-table tbody tr {
  border-bottom: 1px solid #e0e0e0;
}
.abi-table tbody tr:nth-child(even) {
  background-color: #f7f7f7;
}
.abi-table tbody td {
  padding: 6px 9px;
  vertical-align: middle;
}
.abi-table a {
  color: #1159af;
  text-decoration: none;
}
.abi-table a:hover { text-decoration: underline; }

.abi-badge {
  display: inline-block;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 0.75em;
  font-weight: bold;
}
.abi-badge-heim { background: #cfe2ff; color: #0c3780; }
.abi-badge-ausw { background: #fff3cd; color: #856404; }

.abi-unser-team {
  background-color: #e8f1fb !important;
  font-weight: bold;
}
.abi-unser-team td { color: #1159af; }

.abi-platz-badge {
  display: inline-block;
  min-width: 24px;
  text-align: center;
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: bold;
  background: #1159af;
  color: #fff;
}

.abi-quelle {
  font-size: 0.75em;
  color: #aaa;
  margin-top: 5px;
  text-align: right;
}

.abi-table-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
@media (max-width: 600px) {
  .abi-widget { font-size: 0.82em; }
  .abi-table thead th,
  .abi-table tbody td { padding: 4px 5px; }
  .abi-table .col-g,
  .abi-table .col-u,
  .abi-table .col-v { display: none; }
  .abi-table .col-sep { display: none; }
}
</style>
"""

# ── Hilfsfunktionen ────────────────────────────────────────────────────────────


def fetch(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.text


def jetzt() -> str:
    return datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")


# ── Spielplan ─────────────────────────────────────────────────────────────────


def parse_spiele(raw_html: str, max_spiele: int) -> list[dict]:
    soup = BeautifulSoup(raw_html, "html.parser")
    spiele = []
    current_datum = current_zeit = current_wettb = ""

    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        cell_text = [c.get_text(strip=True) for c in cells]

        if len(cells) >= 3 and re.match(
            r"(Mo|Di|Mi|Do|Fr|Sa|So),\s+\d{2}\.\d{2}\.\d{2}", cell_text[0]
        ):
            current_datum = cell_text[0]
            current_zeit = next(
                (t for t in cell_text[1:] if re.match(r"\d{1,2}:\d{2}$", t)), ""
            )
            continue

        links = row.find_all("a", href=re.compile(r"/mannschaft/"))
        if len(links) >= 2 and current_datum:
            heim = re.sub(r"SGM.*ABI.*", "SGM ABI", links[0].get_text(strip=True))
            gast = re.sub(r"SGM.*ABI.*", "SGM ABI", links[1].get_text(strip=True))
            spiel_tag = row.find("a", href=re.compile(r"/spiel/"))
            link = spiel_tag["href"] if spiel_tag else "#"
            if link.startswith("/"):
                link = "https://www.fussball.de" + link

            spiele.append(
                {
                    "datum": current_datum,
                    "zeit": current_zeit,
                    "wettb": current_wettb,
                    "heim": heim,
                    "gast": gast,
                    "link": link,
                    "heimspiel": OUR_TEAM_FRAGMENT in heim,
                }
            )
            if len(spiele) >= max_spiele:
                break

    return spiele


def get_staffel_id(team_id: str) -> str:
    try:
        url = f"https://www.fussball.de/ajax.team.next.games/-/mode/PAGE/team-id/{team_id}"
        raw = fetch(url)
        soup = BeautifulSoup(raw, "html.parser")
        liga_link = soup.find("a", href=re.compile(r"/spieltagsuebersicht/"))
        if liga_link:
            m = re.search(r"/staffel/([^/\"?#]+)", liga_link["href"])
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""


def render_spiele(spiele: list[dict], team_name: str, team_id: str) -> str:
    rows = ""
    for sp in spiele:
        badge = (
            '<span class="abi-badge abi-badge-heim">Heim</span>'
            if sp["heimspiel"]
            else '<span class="abi-badge abi-badge-ausw">Auswärts</span>'
        )
        h = html_module.escape
        rows += f"""
    <tr>
      <td style="white-space:nowrap">{h(sp['datum'])}<br>{badge}</td>
      <td>{h(sp['heim'])}</td>
      <td class="col-sep" style="text-align:center;color:#aaa">–</td>
      <td>{h(sp['gast'])}</td>
      <td><a href="{sp['link']}" target="_blank" rel="noopener">➜</a></td>
    </tr>"""

    return f"""<!-- ABI Nächste Spiele Widget -->
<div class="abi-widget">
  <div class="abi-widget-titel">⚽ Nächste Spiele – {html_module.escape(team_name)}</div>
  <div class="abi-table-wrap">
  <table class="abi-table">
    <thead>
      <tr>
        <th>Datum</th>
        <th>Heimteam</th><th class="col-sep"></th><th>Gastteam</th><th></th>
      </tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
  </div>
  <p class="abi-quelle">
    <a href="https://www.fussball.de/mannschaft/sgm-sc-ilsfeld-abstatt-beilstein-heinriet-abi-i-sc-ilsfeld-wuerttemberg/-/saison/{SAISON}/team-id/{team_id}"
       target="_blank" rel="noopener">fussball.de</a>
    &nbsp;|&nbsp; Stand: {jetzt()}
  </p>
</div>
<!-- Ende Nächste Spiele -->"""


# ── Tabelle ───────────────────────────────────────────────────────────────────


def parse_tabelle(raw_html: str) -> list[dict]:
    soup = BeautifulSoup(raw_html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    eintraege = []
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) < 9:
            continue

        platz = cells[1].get_text(strip=True).rstrip(".")
        team_tag = cells[2].find("a")
        if not team_tag:
            continue
        full_text = cells[2].get_text(" ", strip=True)
        parts = full_text.split("  ")
        team = parts[-1].strip() if len(parts) > 1 else full_text.strip()

        spiele = cells[3].get_text(strip=True)
        siege = cells[4].get_text(strip=True)
        unent = cells[5].get_text(strip=True)
        nieder = cells[6].get_text(strip=True)
        torv = cells[7].get_text(strip=True)
        punkte = cells[9].get_text(strip=True)

        eintraege.append(
            {
                "platz": platz,
                "team": team,
                "sp": spiele,
                "g": siege,
                "u": unent,
                "v": nieder,
                "torv": torv,
                "pkt": punkte,
                "unser": OUR_TEAM_FRAGMENT in team,
            }
        )

    return eintraege


def render_tabelle(eintraege: list[dict], staffel_name: str, staffel_id: str) -> str:
    rows = ""
    for e in eintraege:
        unser_class = ' class="abi-unser-team"' if e["unser"] else ""
        platz_badge = (
            f'<span class="abi-platz-badge">{e["platz"]}</span>'
            if e["unser"]
            else e["platz"] + "."
        )
        h = html_module.escape
        rows += f"""
    <tr{unser_class}>
      <td style="text-align:center">{platz_badge}</td>
      <td>{h(e['team'])}</td>
      <td style="text-align:center">{e['sp']}</td>
      <td class="col-g" style="text-align:center">{e['g']}</td>
      <td class="col-u" style="text-align:center">{e['u']}</td>
      <td class="col-v" style="text-align:center">{e['v']}</td>
      <td style="text-align:center">{e['torv']}</td>
      <td style="text-align:center"><strong>{e['pkt']}</strong></td>
    </tr>"""

    tabelle_url = (
        f"https://www.fussball.de/spieltagsuebersicht/-/staffel/{staffel_id}"
        if staffel_id
        else "https://www.fussball.de"
    )

    return f"""<!-- ABI Ligatabelle Widget -->
<div class="abi-widget">
  <div class="abi-widget-titel">📊 {html_module.escape(staffel_name)}</div>
  <div class="abi-table-wrap">
  <table class="abi-table">
    <thead>
      <tr>
        <th style="text-align:center">Pl.</th>
        <th>Mannschaft</th>
        <th style="text-align:center">Sp</th>
        <th class="col-g" style="text-align:center">G</th>
        <th class="col-u" style="text-align:center">U</th>
        <th class="col-v" style="text-align:center">V</th>
        <th style="text-align:center">Tore</th>
        <th style="text-align:center">Pkt</th>
      </tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
  </div>
  <p class="abi-quelle">
    <a href="{tabelle_url}"
       target="_blank" rel="noopener">fussball.de</a>
    &nbsp;|&nbsp; Stand: {jetzt()}
  </p>
</div>
<!-- Ende Ligatabelle -->"""


# ── SFTP-Upload ────────────────────────────────────────────────────────────────


def sftp_upload(local_files: list[str]):
    """Lädt alle lokalen HTML-Dateien per SFTP auf IONOS hoch."""
    if not SFTP_PASS:
        print("⚠️  SFTP_PASS nicht gesetzt – Upload übersprungen")
        return

    print(f"\n📤 SFTP-Upload nach {SFTP_HOST}{SFTP_REMOTE_DIR} …")
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    try:
        transport.connect(username=SFTP_USER, password=SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # Verzeichnis anlegen falls nicht vorhanden (Fehler ignorieren wenn schon da)
        try:
            sftp.mkdir(SFTP_REMOTE_DIR)
            print(f"  📁 Verzeichnis angelegt: {SFTP_REMOTE_DIR}")
        except Exception:
            pass  # Ordner existiert bereits – alles gut

        for local_path in local_files:
            filename = os.path.basename(local_path)
            remote_path = SFTP_REMOTE_DIR.rstrip("/") + "/" + filename
            print(f"  → Versuche Upload: {remote_path}")
            sftp.put(local_path, remote_path)
            print(f"  ✅ Hochgeladen: {filename} → {remote_path}")

        sftp.close()
    finally:
        transport.close()

    print("📤 Upload abgeschlossen\n")


# ── Hauptprogramm ──────────────────────────────────────────────────────────────


def main():
    print("📡 Hole Daten von fussball.de …\n")

    stand_kommentar = f"<!-- Generiert: {jetzt()} -->\n"
    saved_files = []

    for team in TEAMS:
        team_id = team["team_id"]
        team_name = team["name"]
        output_file = team["output"]

        print(f"── {team_name} ──────────────────────────────────────────────────")

        print("  → Ermittle Staffel-ID …")
        staffel_id = get_staffel_id(team_id)
        if staffel_id:
            print(f"     ✅ Staffel-ID: {staffel_id}")
        else:
            print("     ⚠️  Staffel-ID nicht gefunden")

        print("  → Nächste Spiele …")
        try:
            url_next = f"https://www.fussball.de/ajax.team.next.games/-/mode/PAGE/team-id/{team_id}"
            raw_spiele = fetch(url_next)
            spiele = parse_spiele(raw_spiele, MAX_SPIELE)
            if spiele:
                print(f"     ✅ {len(spiele)} Spiel(e) gefunden")
                for sp in spiele:
                    icon = "🏠" if sp["heimspiel"] else "✈️ "
                    print(f"        {icon} {sp['datum']}  {sp['heim']} – {sp['gast']}")
            else:
                print("     ⚠️  Keine Spiele geparst")
            html_spiele = render_spiele(spiele, team_name, team_id)
        except Exception as e:
            print(f"     ❌ Fehler: {e}")
            html_spiele = ""

        print("  → Ligatabelle …")
        try:
            url_table = (
                f"https://www.fussball.de/ajax.team.table/-/saison/{SAISON}"
                f"/staffel/{staffel_id}/team-id/{team_id}"
            )
            raw_table = fetch(url_table)
            eintraege = parse_tabelle(raw_table)
            if eintraege:
                print(f"     ✅ {len(eintraege)} Teams gefunden")
                for e in eintraege:
                    marker = " ◀ ABI" if e["unser"] else ""
                    print(f"        {e['platz']:>2}. {e['team'][:45]:<45} {e['pkt']} Pkt{marker}")
            else:
                print("     ⚠️  Tabelle konnte nicht geparst werden")
            html_tabelle = render_tabelle(eintraege, team_name, staffel_id)
        except Exception as e:
            print(f"     ❌ Fehler: {e}")
            html_tabelle = ""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(stand_kommentar + SHARED_CSS + "\n" + html_spiele + "\n" + html_tabelle)
        saved_files.append(output_file)
        print(f"  💾 Gespeichert: {output_file}\n")

    # SFTP-Upload aller generierten Dateien
    sftp_upload(saved_files)

    print("─── Fertig ──────────────────────────────────────────────────────────")
    for fname in saved_files:
        print(f"   {fname}")


if __name__ == "__main__":
    main()
