#!/usr/bin/env python
# coding: utf-8

import re
import requests
import time
from urllib.parse import urlparse, parse_qs, unquote_plus
from bs4 import BeautifulSoup
import pandas as pd
import datetime

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9",
}
SAISON = "2526"
HTML_PARSER = "html.parser"
ABI_TEAM = "SGM ABI"
ABI_TEAM_REGEX = r"SGM.*ABI.*"


def get_team_platz(soup, team_url):
    """Tabellenplatz, Spiele, Tore und Punkte abrufen.
    Gibt (platz, spiele, tore, punkte) zurück oder ('','','','') wenn nicht gefunden."""
    try:
        liga_link = soup.find("a", href=re.compile(r"/spieltagsuebersicht/"))
        if not liga_link:
            return "", "", "", ""
        staffel_match = re.search(r"/staffel/([^/\"?#]+)", liga_link["href"])
        if not staffel_match:
            return "", "", "", ""
        staffel_id = staffel_match.group(1)

        team_id_match = re.search(r"team-id/([^/&#!]+)", team_url)
        if not team_id_match:
            return "", "", "", ""
        team_id = team_id_match.group(1)

        table_url = (
            f"https://www.fussball.de/ajax.team.table/-/saison/{SAISON}"
            f"/staffel/{staffel_id}/team-id/{team_id}"
        )
        resp = requests.get(table_url, headers=HEADERS, timeout=10)
        table_soup = BeautifulSoup(resp.text, HTML_PARSER)
        tbl = table_soup.find("table")
        if not tbl:
            return "", "", "", ""
        for row in tbl.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) >= 10 and "ABI" in cells[2].get_text():
                platz = cells[1].get_text(strip=True).rstrip(".")
                spiele = cells[3].get_text(strip=True)
                tore = cells[7].get_text(strip=True)
                punkte = cells[9].get_text(strip=True)
                return platz, spiele, tore, punkte
    except Exception:
        pass
    return "", "", "", ""


def get_full_table_rows(staffel_id, team_id):
    """Volle Ligatabelle als HTML-Tabellenzeilen abrufen. ABI-Zeile wird hervorgehoben."""
    try:
        table_url = (
            f"https://www.fussball.de/ajax.team.table/-/saison/{SAISON}"
            f"/staffel/{staffel_id}/team-id/{team_id}"
        )
        resp = requests.get(table_url, headers=HEADERS, timeout=10)
        tbl_soup = BeautifulSoup(resp.text, HTML_PARSER)
        tbl = tbl_soup.find("table")
        if not tbl:
            return "", ""
        rows_html = ""
        for row in tbl.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) < 10:
                continue
            is_abi = "ABI" in cells[2].get_text()
            tr_style = ' style="background-color:#e8f1fb;font-weight:bold"' if is_abi else ""
            platz = cells[1].get_text(strip=True).rstrip(".")
            mannschaft = re.sub(ABI_TEAM_REGEX, ABI_TEAM, cells[2].get_text(strip=True))
            sp = cells[3].get_text(strip=True)
            tore = cells[7].get_text(strip=True)
            pkt = cells[9].get_text(strip=True)
            rows_html += f"""    <tr{tr_style}>
      <td style="padding:5px 7px;text-align:center;border-bottom:1px solid #e0e0e0">{platz}</td>
      <td style="padding:5px 7px;border-bottom:1px solid #e0e0e0">{mannschaft}</td>
      <td style="padding:5px 7px;text-align:center;border-bottom:1px solid #e0e0e0">{sp}</td>
      <td style="padding:5px 7px;text-align:center;border-bottom:1px solid #e0e0e0">{tore}</td>
      <td style="padding:5px 7px;text-align:center;border-bottom:1px solid #e0e0e0"><strong>{pkt}</strong></td>
    </tr>\n"""
        return rows_html
    except Exception:
        return "", ""


team_urls = pd.read_csv("Spiele_Links.csv")
outfile = "All_games_from_fussball_de.csv"
numOfGames = 0
print(len(team_urls))

file_created = False  # Fix: CSV-Append-Logik mit Flag
plaetze = {}        # {team: platz}
spiele_dict = {}    # {team: anzahl_spiele}
tore_dict = {}      # {team: tore}
punkte_dict = {}    # {team: punkte}
teams_mit_daten = set()  # Teams mit aktuellen Spieldaten
staffel_ids = {}   # {team: staffel_id}
team_ids_map = {}  # {team: team_id}

for idx in range(0, len(team_urls)):
    # Inaktive Teams überspringen
    if str(team_urls.get("aktiv", {}).get(idx, 1)) == "0":
        continue

    # load url
    url = team_urls["url"][idx]
    response = requests.get(url, headers=HEADERS)
    df = pd.DataFrame()

    # BeautifulSoup HTML-Dokument aus dem Quelltext parsen
    soup = BeautifulSoup(response.text, HTML_PARSER)

    # Tabelle mit den Spielen aus dem HTML-Dokument extrahieren
    table = soup.find("div", {"id": "id-team-matchplan-table"})

    # extract id of team i.e. B1, C2,...
    team = team_urls["team"][idx]
    print(team)

    # Staffel-ID und Team-ID für spätere Ligatabellen-Abfrage speichern
    liga_link_main = soup.find("a", href=re.compile(r"/spieltagsuebersicht/"))
    if liga_link_main:
        sm = re.search(r"/staffel/([^/\"?#]+)", liga_link_main["href"])
        if sm:
            staffel_ids[team] = sm.group(1)
    tm = re.search(r"team-id/([^/&#!]+)", url)
    if tm:
        team_ids_map[team] = tm.group(1)

    # Tabellenplatz und Spielanzahl abrufen (nutzt bereits geladene soup)
    platz, spiele, tore, punkte = get_team_platz(soup, url)
    if platz:
        print(f"  → Platz {platz} ({spiele} Sp., {tore} Tore, {punkte} Pkt.)")

    try:
        # Datum und Liga auslesen (befindet sich in jeder 3. Zeile ab 2. Zeile)
        for data in table.find_all("tbody"):
            rows = data.find_all("tr")
            dates = []
            times = []
            teams = []
            kw = []
            club1 = []
            club2 = []
            logos_home = []
            logos_guest = []

            prev_date = None  # Fix: prev_date initialisieren

            for i in range(1, len(rows), 3):
                # Datum + Zeit auslesen
                date_cell = rows[i].find(
                    "td", class_="column-date"
                )  # Fix: kein shadowing mehr
                cleanString = date_cell.text.replace(" |", ",").replace(" ", "")
                splitted = cleanString.split(",")

                if len(splitted) == 3:
                    date_split = splitted[1].split(".")
                    datum = datetime.date(
                        int(date_split[2]) + 2000,
                        int(date_split[1]),
                        int(date_split[0]),
                    )
                    kw.append(datum.isocalendar()[1])
                    dates.append(splitted[1])
                    times.append(splitted[2].encode("utf-8").decode("utf-8"))
                    prev_date = splitted  # Fix: nur setzen wenn vollständig
                elif prev_date is not None:  # Fix: Guard gegen undefined prev_date
                    date_split = prev_date[1].split(".")
                    datum = datetime.date(
                        int(date_split[2]) + 2000,
                        int(date_split[1]),
                        int(date_split[0]),
                    )
                    kw.append(datum.isocalendar()[1])
                    dates.append(prev_date[1])
                    times.append(splitted[0].encode("utf-8").decode("utf-8"))
                else:
                    # Erste Zeile ohne vollständiges Datum – überspringen
                    continue

                teams.append(team)  # Fix: nur einmal anhängen (war doppelt)

                # Gegner auslesen aus der nächsten Zeile (i+1)
                j = i + 1
                if j < len(rows):
                    removedSpace = (
                        rows[j]
                        .text.replace("\n", "")
                        .replace("\t", "")
                        .replace(":", ";")
                    )
                    splitted_clubs = removedSpace.split(";")
                    club1.append(re.sub(ABI_TEAM_REGEX, ABI_TEAM, splitted_clubs[0]))
                    club2.append(re.sub(ABI_TEAM_REGEX, ABI_TEAM, splitted_clubs[1][0:-1]))

                    # Logos auslesen
                    logo = rows[j].find_all("div", class_="club-logo")
                    logo_link = re.findall(r"//(\S+)\">", str(logo))
                    logos_home.append(logo_link[0])
                    logos_guest.append(logo_link[1])

            # Listen mit Datum, Uhrzeit und Team-ID werden in einer Tabelle gespeichert
            df = pd.DataFrame(
                list(zip(dates, times, teams)), columns=["Datum", "Zeit", "Team"]
            )
            df.insert(len(df.columns), "KW", kw)

            if df.shape[0] > 0:
                df.insert(len(df.columns), "Heim", club1)
                df.insert(len(df.columns), "Gast", club2)
                df.insert(len(df.columns), "Logo Heim", logos_home)
                df.insert(len(df.columns), "Logo Gast", logos_guest)

                # Alle Links zum Spiel und zu den Mannschaften auf fussball.de auslesen
                links = table.find_all("a")
                homeLinks = []
                guestLinks = []
                spielLinks = []
                for i in range(2, len(links), 6):
                    homeLinks.append(links[i].get("href"))
                    guestLinks.append(links[i + 1].get("href"))
                    spielLinks.append(links[i + 2].get("href"))

                df.insert(len(df.columns), "home_link", homeLinks)
                df.insert(len(df.columns), "guest_link", guestLinks)
                df.insert(len(df.columns), "Spiel", spielLinks)

            numOfGames += df.shape[0]

            # Fix: CSV-Append-Logik mit Flag statt idx == 0
            if not file_created:
                df.to_csv(outfile, index=False)
                file_created = True
            else:
                df.to_csv(outfile, mode="a", index=False, header=False)

        # Platz nur speichern wenn Team aktuelle Spieldaten hat
        if df.shape[0] > 0:
            teams_mit_daten.add(team)
            plaetze[team] = platz
            spiele_dict[team] = spiele
            tore_dict[team] = tore
            punkte_dict[team] = punkte

    except Exception as e:  # Fix: kein nackter except mehr
        print(f"no data for {team}: {e}")

print("number of games: " + str(numOfGames))

# Tabellenplätze und Spielanzahl in Spiele_Links.csv speichern
team_urls["Platz"] = team_urls["team"].map(plaetze).fillna("")
team_urls["Spiele"] = team_urls["team"].map(spiele_dict).fillna("")
team_urls["Tore"] = team_urls["team"].map(tore_dict).fillna("")
team_urls["Punkte"] = team_urls["team"].map(punkte_dict).fillna("")
# Staffel wird NICHT überschrieben – manuell in Spiele_Links.csv pflegen
team_urls.to_csv("Spiele_Links.csv", index=False)

# Gesamtübersicht aller ABI-Teams gruppiert nach Kategorie (A/B/C/D × Junioren/Juniorinnen)
def team_gruppe(name):
    buchstabe = name[0]
    return f"{buchstabe}-Juniorinnen" if "J-innen" in name else f"{buchstabe}-Junioren"

gruppen = {}         # {gruppe: [(team_name, platz, spiele, staffel), ...]}
gruppen_url = {}     # {gruppe: fussball_url}
ad_teams = team_urls[
    team_urls["team"].str[0].isin(list("ABCD")) &
    (team_urls.get("aktiv", pd.Series(1, index=team_urls.index)).astype(str) != "0")
]
for _, row in ad_teams.iterrows():
    team_name = row["team"]
    gruppe = team_gruppe(team_name)
    platz = str(row.get("Platz", "")).strip()
    sp = str(row.get("Spiele", "")).strip()
    stfl = str(row.get("Staffel", "")).strip()
    gruppen.setdefault(gruppe, []).append((team_name, platz, sp, stfl))
    fussball_url = str(row.get("url", "")).strip().rstrip("#!/")
    if fussball_url and gruppe not in gruppen_url:
        gruppen_url[gruppe] = fussball_url

rows_html = ""
for _, row in ad_teams.iterrows():
    tname = row["team"]
    p = str(row.get("Platz", "")).strip()
    sp = str(row.get("Spiele", "")).strip()
    tore = str(row.get("Tore", "")).strip()
    pkt = str(row.get("Punkte", "")).strip()
    keine_spiele = sp in ("", "0")
    platz_text = f'<span class="abi-platz-badge">{p}</span>' if (p and not keine_spiele) else "–"
    spiele_text = sp if sp else "–"
    tore_text = tore if (tore and not keine_spiele) else "–"
    pkt_text = f"<strong>{pkt}</strong>" if (pkt and not keine_spiele) else "–"
    fussball_url = str(row.get("url", "")).strip().rstrip("#!/")
    team_cell = f'<a href="{fussball_url}" target="_blank" rel="noopener">{tname}</a>' if fussball_url else tname
    tr_style = " style='color:#bbb'" if keine_spiele else ""
    rows_html += (
        f"\t<tr{tr_style}>\n\t\t<td>{team_cell}</td>\n"
        f"\t\t<td style='text-align:center'>{spiele_text}</td>\n"
        f"\t\t<td style='text-align:center'>{tore_text}</td>\n"
        f"\t\t<td style='text-align:center'>{pkt_text}</td>\n"
        f"\t\t<td style='text-align:center'>{platz_text}</td>\n\t</tr>\n"
    )

stand_alle = datetime.datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")
alle_teams_html = f"""<style>
.at-widget {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0.8em 0; }}
.at-titel {{ font-size: 15px; font-weight: 700; color: #1159af; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 2px solid #1159af; }}
.at-table {{ width: 100%; border-collapse: collapse; font-size: 15px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
.at-table thead tr {{ background-color: #1159af; color: #fff; }}
.at-table thead th {{ padding: 7px 9px; text-align: left; font-weight: 600; font-size: 15px; }}
.at-table tbody tr {{ border-bottom: 1px solid #e0e0e0; }}
.at-table tbody tr:nth-child(even) {{ background-color: #f7f7f7; }}
.at-table tbody td {{ padding: 6px 9px; font-size: 15px; }}
.at-platz-badge {{ display: inline-block; min-width: 24px; text-align: center; padding: 2px 5px; border-radius: 4px; font-size: 13px; font-weight: bold; background: #1159af; color: #fff; }}
.at-quelle {{ font-size: 12px; color: #aaa; margin-top: 5px; text-align: right; }}
</style>
<div class="at-widget">
  <div class="at-titel">📊 Tabellenplätze ABI-Teams</div>
  <table class="at-table">
    <thead><tr><th>Team</th><th style="text-align:center">Sp</th><th style="text-align:center">Tore</th><th style="text-align:center">Pkt</th><th style="text-align:center">Platz</th></tr></thead>
    <tbody>
{rows_html}    </tbody>
  </table>
  <p class="at-quelle"><a href="https://www.fussball.de" target="_blank" rel="noopener">fussball.de</a> &nbsp;|&nbsp; Stand: {stand_alle}</p>
</div>"""

with open("alle_teams.html", "w", encoding="utf-8") as f:
    f.write(alle_teams_html)
print("alle_teams.html gespeichert")

df = pd.read_csv(outfile, sep=",")

# Spielort für Auswärtsspiele der Teams A–D von der Detailseite abrufen
def get_spielort(spiel_url):
    """Gibt (adresse, maps_url) zurück, z.B. ('Am Sportplatz 1, 74369 Löchgau', 'https://...')"""
    try:
        resp = requests.get(spiel_url)
        soup_spiel = BeautifulSoup(resp.text, HTML_PARSER)
        maps_link = soup_spiel.find("a", href=re.compile(r"google\.(de|com)/maps"))
        if maps_link:
            maps_url = maps_link["href"]
            params = parse_qs(urlparse(maps_url).query)
            adresse = re.sub(r",?\s*\d{5}\s*", ", ", unquote_plus(params.get("q", [""])[0])).strip(", ")
            return adresse, maps_url
    except Exception:
        pass
    return "", ""

# Zeitfenster: nächste 7 Tage ab heute
heute = datetime.date.today()
bis = heute + datetime.timedelta(days=7)

def in_zeitfenster(datum_str):
    try:
        d, m, y = datum_str.split(".")
        return heute <= datetime.date(int(y) + 2000, int(m), int(d)) <= bis
    except Exception:
        return False

spielorte_text = []
spielorte_url = []
for idx in df.index:
    team = df.loc[idx, "Team"]
    heim = str(df.loc[idx, "Heim"])
    is_ad_team = team[0] in "ABCD"
    in_naechste_kw = in_zeitfenster(str(df.loc[idx, "Datum"]))
    if is_ad_team and in_naechste_kw:
        print(f"Lade Spielort für {team}: {df.loc[idx, 'Spiel']}")
        adresse, maps_url = get_spielort(df.loc[idx, "Spiel"])
        spielorte_text.append(adresse)
        spielorte_url.append(maps_url)
        time.sleep(0.5)
    else:
        spielorte_text.append("")
        spielorte_url.append("")

df.insert(len(df.columns), "Spielort", spielorte_text)
df.insert(len(df.columns), "Spielort_URL", spielorte_url)
df.to_csv(outfile, index=False)

# Inline-Style-Konstanten für WordPress-Kompatibilität
S_TABLE = 'style="width:100%;border-collapse:collapse;font-size:14px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;text-align:left"'
S_THEAD_TR = 'style="background-color:#1159af!important;color:#fff!important"'
S_TH = 'style="padding:7px 9px;text-align:left!important;font-weight:600;background-color:#1159af!important;color:#fff!important;white-space:nowrap"'
S_TD = 'style="padding:6px 9px;vertical-align:middle;border-bottom:1px solid #e0e0e0"'
S_TD_DATE = 'style="padding:6px 9px;vertical-align:middle;border-bottom:1px solid #e0e0e0;white-space:nowrap"'
S_BADGE_HEIM = 'class="abi-badge-heim"'
S_BADGE_AUSW = 'class="abi-badge-ausw"'
S_TITEL = 'style="font-size:15px;font-weight:700;color:#1159af;margin-bottom:6px;padding-bottom:4px;border-bottom:2px solid #1159af"'
S_QUELLE = 'style="font-size:12px;color:#aaa;margin-top:5px;text-align:right"'

print(f"Generiere Aktuelle_Spiele.html ({heute} – {bis})")
kw_data = df[df["Datum"].apply(in_zeitfenster)].copy()
kw_data["_sort_datetime"] = pd.to_datetime(
    kw_data["Datum"] + " " + kw_data["Zeit"],
    format="%d.%m.%y %H:%M"
)
kw_data = kw_data.sort_values(by="_sort_datetime")
kw_data["Heim"] = kw_data["Heim"].replace(ABI_TEAM_REGEX, ABI_TEAM, regex=True)
kw_data["Gast"] = kw_data["Gast"].replace(ABI_TEAM_REGEX, ABI_TEAM, regex=True)

rows_html = ""
for ind in kw_data.index:
    heim = kw_data["Heim"][ind].replace("\u200b", "")
    gast = kw_data["Gast"][ind].replace("\u200b", "")
    is_heimspiel = heim == ABI_TEAM
    badge = f'<span {S_BADGE_HEIM}>Heim</span>' if is_heimspiel else f'<span {S_BADGE_AUSW}>Auswärts</span>'
    if is_heimspiel:
        heim_text = f"{heim} {kw_data['Team'][ind]}"
        gast_text = gast if len(gast) < 44 else f"{gast[:45]}..."
    else:
        heim_text = heim if len(heim) < 44 else f"{heim[:45]}..."
        gast_text = f"{gast} {kw_data['Team'][ind]}"
    spiellink = kw_data["Spiel"][ind]
    datum = kw_data["Datum"][ind]
    zeit = kw_data["Zeit"][ind].strip()
    spiel_text = f'<a href="{spiellink}" target="_blank">{heim_text} vs. {gast_text}</a>'
    spielort_text = kw_data["Spielort"][ind]
    spielort_url = kw_data["Spielort_URL"][ind]
    if isinstance(spielort_url, str) and spielort_url:
        spiel_text += f'<br><small>📍 <a href="{spielort_url}" target="_blank">{spielort_text}</a></small>'
    rows_html += f"""    <tr>
      <td {S_TD_DATE}>{datum} | {zeit}<br>{badge}</td>
      <td {S_TD}>{kw_data["Team"][ind]}</td>
      <td {S_TD}>{spiel_text}</td>
    </tr>\n"""

stand = heute.strftime("%d.%m.%Y")
aktuelle_spiele_html = f"""<!-- ABI Aktuelle Spiele -->
<div style="margin:1em 0;overflow-x:auto;text-align:left">
  <div {S_TITEL}>⚽ Aktuelle Spiele ({heute.strftime('%d.%m.')} – {bis.strftime('%d.%m.%y')})</div>
  <table {S_TABLE}>
    <thead>
      <tr {S_THEAD_TR}>
        <th {S_TH}>Datum</th>
        <th {S_TH}>Team</th>
        <th {S_TH}>Begegnung</th>
      </tr>
    </thead>
    <tbody>
{rows_html}    </tbody>
  </table>
  <p {S_QUELLE}>Stand: {stand}</p>
</div>"""

with open("Aktuelle_Spiele.html", "w", encoding="utf-8") as f:
    f.write(aktuelle_spiele_html)
print("Aktuelle_Spiele.html gespeichert")

with open("komplett_abi.html", "w", encoding="utf-8") as f:
    f.write(aktuelle_spiele_html + "\n\n" + alle_teams_html)
print("komplett_abi.html gespeichert")

# Per-Team komplett HTML generieren (Spiele + Ligatabelle)
S_TH_LIG = 'style="padding:6px 7px;text-align:left;font-weight:600;background-color:#1159af!important;color:#fff!important;font-size:13px"'
S_TH_LIG_C = 'style="padding:6px 7px;text-align:center;font-weight:600;background-color:#1159af!important;color:#fff!important;font-size:13px"'

for _, row in ad_teams.iterrows():
    tname = row["team"]
    if tname not in staffel_ids or tname not in team_ids_map:
        continue

    # Gefilterte Spiele für dieses Team
    team_spiele = kw_data[kw_data["Team"] == tname]
    team_rows_html = ""
    for ind in team_spiele.index:
        heim = team_spiele["Heim"][ind].replace("\u200b", "")
        gast = team_spiele["Gast"][ind].replace("\u200b", "")
        is_heimspiel = heim == ABI_TEAM
        badge = f'<span {S_BADGE_HEIM}>Heim</span>' if is_heimspiel else f'<span {S_BADGE_AUSW}>Auswärts</span>'
        if is_heimspiel:
            heim_text = f"{heim} {tname}"
        else:
            heim_text = heim if len(heim) < 44 else f"{heim[:45]}..."
        if is_heimspiel:
            gast_text = gast if len(gast) < 44 else f"{gast[:45]}..."
        else:
            gast_text = f"{gast} {tname}"
        spiellink = team_spiele["Spiel"][ind]
        datum = team_spiele["Datum"][ind]
        zeit = team_spiele["Zeit"][ind].strip()
        spiel_text = f'<a href="{spiellink}" target="_blank">{heim_text} vs. {gast_text}</a>'
        spielort_text = team_spiele["Spielort"][ind]
        spielort_url = team_spiele["Spielort_URL"][ind]
        if isinstance(spielort_url, str) and spielort_url:
            spiel_text += f'<br><small>📍 <a href="{spielort_url}" target="_blank">{spielort_text}</a></small>'
        team_rows_html += f"""    <tr>
      <td {S_TD_DATE}>{datum} | {zeit}<br>{badge}</td>
      <td {S_TD}>{spiel_text}</td>
    </tr>\n"""

    if not team_rows_html:
        team_rows_html = '    <tr><td colspan="2" style="padding:8px;color:#aaa;text-align:center">Keine Spiele in den nächsten 7 Tagen</td></tr>\n'

    spiele_html = f"""<!-- Spiele {tname} -->
<div style="margin:0.8em 0;overflow-x:auto;text-align:left">
  <div {S_TITEL}>⚽ Nächste Spiele – {tname}</div>
  <table {S_TABLE}>
    <thead>
      <tr {S_THEAD_TR}>
        <th {S_TH}>Datum</th>
        <th {S_TH}>Begegnung</th>
      </tr>
    </thead>
    <tbody>
{team_rows_html}    </tbody>
  </table>
  <p {S_QUELLE}>Stand: {heute.strftime("%d.%m.%Y")}</p>
</div>"""

    # Volle Ligatabelle
    liga_rows = get_full_table_rows(staffel_ids[tname], team_ids_map[tname])
    liga_html = ""
    if liga_rows:
        liga_html = f"""
<!-- Ligatabelle {tname} -->
<div style="margin:0.8em 0;overflow-x:auto;text-align:left">
  <div {S_TITEL}>📊 Ligatabelle – {tname}</div>
  <table style="width:100%;border-collapse:collapse;font-size:13px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif">
    <thead>
      <tr style="background-color:#1159af!important;color:#fff!important">
        <th {S_TH_LIG_C}>Pl.</th>
        <th {S_TH_LIG}>Mannschaft</th>
        <th {S_TH_LIG_C}>Sp</th>
        <th {S_TH_LIG_C}>Tore</th>
        <th {S_TH_LIG_C}>Pkt</th>
      </tr>
    </thead>
    <tbody>
{liga_rows}    </tbody>
  </table>
  <p {S_QUELLE}><a href="https://www.fussball.de" target="_blank">fussball.de</a> &nbsp;|&nbsp; Stand: {heute.strftime("%d.%m.%Y, %H:%M Uhr")}</p>
</div>"""

    filename = f"komplett_{tname.replace('/', '-').replace(' ', '_')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(spiele_html + liga_html)
    print(f"{filename} gespeichert")
