#!/usr/bin/env python
# coding: utf-8

import os
import requests
import csv
import re
from bs4 import BeautifulSoup
import pandas as pd
import datetime
from datetime import date

team_urls = pd.read_csv("Spiele_Links.csv")
outfile = "All_games_from_fussball_de.csv"
numOfGames = 0
print(len(team_urls))
# erzeuge definition
# rufe alle links aus Spiele_links.csv auf um für jede Mannschaft die noch stattfindenden Spiele zu extrahieren
for idx in range(0, len(team_urls)):
    # load url
    url = team_urls["url"][idx]
    response = requests.get(url)
    df = pd.DataFrame()

    # BeautifulSoup HTML-Dokument aus dem Quelltext parsen
    soup = BeautifulSoup(response.text, "html.parser")

    # Tabelle mit den Spielen aus dem HTML-Dokument extrahieren
    table = soup.find("div", {"id": "id-team-matchplan-table"})

    # extract id of team i.e. B1, C2,...
    team = team_urls["team"][idx]
    print(team)

    try:
        # Datum und Liga auslesen (befindet sich in jeder 3. Zeile ab 2. Zeile)
        for data in table.find_all("tbody"):
            rows = data.find_all("tr")
            dates = list()
            times = list()
            teams = list()
            kw = list()
            for i in range(1, len(rows), 3):
                # entfernt Sonderzeichen wie Zeilenumbruch (n) und Tab (t)
                date = rows[i].find("td", class_="column-date")  # rows[i].text
                cleanString = re.sub(r"\ \|", ",", date.text)
                cleanString = re.sub(r" ", "", cleanString)
                splitted = cleanString.split(",")

                # Datum wird extrahiert um die KW auszurechnen und Datum und Uhrzeit separat abzuspeichern
                try:
                    date_split = splitted[1].split(".")
                except:
                    continue

                datum = datetime.date(
                    int(date_split[2]) + 2000, int(date_split[1]), int(date_split[0])
                )
                kw.append(datum.isocalendar()[1])
                dates.append(splitted[1])
                times.append(splitted[2])
                # add team id
                teams.append(team)

            # Listen mit Datum, Uhrzeit und Team-ID werden in einer Tabelle gespeichert
            df = pd.DataFrame(
                list(zip(dates, times, teams)), columns=["Datum", "Zeit", "Team"]
            )
            df.insert(len(df.columns), "KW", kw)

            if df.shape[0] > 0:
                # Gegner (Fußballvereine) auslesen (befindet sich in jeder 3. Zeile ab 3. Zeile)
                for data in table.find_all("tbody"):
                    rows = data.find_all("tr")
                    # 1. Mannschaft (Heim)
                    club1 = list()
                    # 2. Mannschaft (auswärts)
                    club2 = list()
                    for i in range(2, len(rows), 3):
                        # entfernt Sonderzeichen wie Zeilenumbruch (n) und Tab (t)
                        # print(rows[i].text)
                        removedSpace = re.sub(r"\n", "", rows[i].text)
                        removedSpace = re.sub(r"\t", "", removedSpace)
                        removedSpace = re.sub(r":", ";", removedSpace)
                        splitted = removedSpace.split(";")
                        club1.append(splitted[0])
                        club2.append(splitted[1][0:-1])

                # Abspeichern der Heim und Gast-Mannschaft in der Tabelle mit den Spieldaten
                df.insert(len(df.columns), "Heim", club1)
                df.insert(len(df.columns), "Gast", club2)

                # Logo von den Mannschaften auslesen (befindet sich in jeder 3. Zeile ab 2. Zeile)
                for data in table.find_all("tbody"):
                    rows = data.find_all("tr")
                    logos_home = list()
                    logos_guest = list()
                    for i in range(2, len(rows), 3):
                        # entfernt Sonderzeichen wie Zeilenumbruch (n) und Tab (t)
                        logo = rows[i].find_all(
                            "div", class_="club-logo"
                        )  # rows[i].text

                        logo_link = re.findall(r"//(\S+)\">", str(logo))
                        logos_home.append(logo_link[0])
                        logos_guest.append(logo_link[1])

                # Logo-URLs in der Tabelle abspeichern
                df.insert(len(df.columns), "Logo Heim", logos_home)
                df.insert(len(df.columns), "Logo Gast", logos_guest)

                # Alle Links zum Spiel und zu den Mannschaften auf fussball.de auslesen
                links = table.find_all("a")
                homeLinks = list()
                guestLinks = list()
                spielLinks = list()
                for i in range(2, len(links), 6):
                    homeLinks.append(links[i].get("href"))
                    guestLinks.append(links[i + 1].get("href"))
                    spielLinks.append(links[i + 2].get("href"))

                # Links zur Gesamttabelle hinzufügen
                df.insert(len(df.columns), "home_link", homeLinks)
                df.insert(len(df.columns), "guest_link", guestLinks)
                df.insert(len(df.columns), "Spiel", spielLinks)

            numOfGames += df.shape[0]

            # Gesamttabelle als csv abspeichern
            # wenn 1. Link, dann wird alte csv-Datei überschrieben
            # ansonsten werden die Tabellen einfach hinten dran gehängt, so dass sich am Ende alle Spiele
            # von allen Mannschaften in einer Datei befinden
            if idx == 0:
                df.to_csv(outfile, index=False)
            else:
                df.to_csv(outfile, mode="a", index=False, header=False)

    except:
        print("no data")
print("number of games: " + str(numOfGames))

df = pd.read_csv(outfile, sep=",")
df.head()
weeks = sorted(df.KW.unique())

for kw in weeks:
    print("generate table " + str(kw))
    filename = "Spiele_KW_" + str(kw) + ".html"
    # extract data from current calendar week
    kw_data = df.loc[df["KW"] == kw]
    # sort data by date and time
    kw_data = kw_data.sort_values(by=["Datum", "Zeit"])
    kw_data["Heim"] = kw_data["Heim"].replace(r"SGM.*ABI.*", "SGM ABI", regex=True)
    kw_data["Gast"] = kw_data["Gast"].replace(r"SGM.*ABI.*", "SGM ABI", regex=True)

    # write head of table in html
    table_head = '<table id="Spiele">\n'
    table_head += "\t<caption>Spiele der " + str(kw) + ". KW</caption>\n"
    table_head += "\t<tr>\n"
    table_head += "\t\t<th>Datum</th>\n"
    table_head += "\t\t<th>ABI Team</th>\n"
    table_head += "\t\t<th>Heim</th>\n"
    table_head += "\t\t<th>Gast</th>\n"
    table_head += "\t\t<th>Ergebnis</th>\n"
    table_head += "\t</tr>"
    # print(table_head)
    f = open(filename, "w")
    f.write(table_head)
    f.close()
    kw_data.head()

    f = open(filename, "a")
    for ind in kw_data.index:
        html_line = "\t<tr>\n"
        html_line += (
            "\t\t<td>" + kw_data["Datum"][ind] + ", " + kw_data["Zeit"][ind] + "</td>\n"
        )
        html_line += "\t\t<td>" + kw_data["Team"][ind] + "</td>\n"
        if kw_data["Heim"][ind] == "SGM ABI":
            print("Heimspiel")
            html_line += (
                "\t\t<td>"
                + '<a href="'
                + kw_data["home_link"][ind]
                + '" target="_blank" class="ABI">'
                + kw_data["Heim"][ind].replace("\u200b", "")
                + "</a></td>\n"
            )
        else:
            player = kw_data["Heim"][ind]
            player = player if len(player) < 15 else f"{player[0:14]}..."
            html_line += (
                "\t\t<td>"
                + '<a href="'
                + kw_data["home_link"][ind]
                + '" target="_blank">'
                + player.replace("\u200b", "")
                + "</a></td>\n"
            )
        if kw_data["Gast"][ind] == "SGM ABI":
            html_line += (
                "\t\t<td>"
                + '<a href="'
                + kw_data["guest_link"][ind]
                + '" target="_blank" class="ABI">'
                + kw_data["Gast"][ind].replace("\u200b", "")
                + "</a></td>\n"
            )
        else:
            player = kw_data["Gast"][ind]
            player = player if len(player) < 15 else f"{player[0:14]}..."
            html_line += (
                "\t\t<td>"
                + '<a href="'
                + kw_data["guest_link"][ind]
                + '" target="_blank" >'
                + player.replace("\u200b", "")
                + "</a></td>\n"
            )
        html_line += (
            "\t\t<td>"
            + '<a href="'
            + kw_data["Spiel"][ind]
            + '" target="_blank">link</a>'
            + "</td>\n"
        )
        html_line += "\t</tr>\n"

        f.write(html_line)
    f.write("</table>")
    f.close()
