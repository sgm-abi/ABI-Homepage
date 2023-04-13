#!/usr/bin/env python
# coding: utf-8

# In[8]:


import requests
import csv
import re
from bs4 import BeautifulSoup
import pandas as pd
import datetime
from datetime import date


# In[58]:

team_urls = pd.read_csv('Spiele_Links.csv')

for idx in range(0,len(team_urls)):

    url = team_urls['url'][idx]
    response = requests.get(url)

    #BeautifulSoup HTML-Dokument aus dem Quelltext parsen
    soup= BeautifulSoup(response.text, 'html.parser')

    #Tabelle aus dem HTML-Dokument extrahieren
    table = soup.find('div', {"id":'id-team-matchplan-table'})
    #print(table)

    team=team_urls['team'][idx]
    print(team)
    
    #Datum und Liga auslesen (befindet sich in jeder 3. Zeile ab 2. Zeile)
    for data in table.find_all('tbody'):
        rows = data.find_all('tr')
        dates = list()
        times = list()
        teams = list()
        kw = list()
        for i in range(1,len(rows),3):
            #entfernt Sonderzeichen wie Zeilenumbruch (n) und Tab (t)
            date = rows[i].find('td', class_='column-date') #rows[i].text
            cleanString = re.sub(r'\ \|',',', date.text)
            cleanString = re.sub(r' ', '', cleanString)
            #removedSpace = re.sub(r'\t', '', removedSpace)
            splitted= cleanString.split(',')
            date_split = splitted[1].split('.')
            datum = datetime.date(int(date_split[2])+2000, int(date_split[1]), int(date_split[0]))
            kw.append(datum.isocalendar()[1])
            dates.append(splitted[1])
            times.append(splitted[2])
            teams.append(team)
            
    df = pd.DataFrame(list(zip(dates,times,teams)),columns=['Datum','Zeit','Team'])
    df.insert(len(df.columns), 'KW', kw)
    df


    # In[62]:


    #Club und Logo auslesen (befindet sich in jeder 3. Zeile ab 3. Zeile)
    for data in table.find_all('tbody'):
        rows = data.find_all('tr')
        club1 = list()
        club2 = list()
        for i in range(2,len(rows),3):
            #entfernt Sonderzeichen wie Zeilenumbruch (n) und Tab (t)
            #print(rows[i].text)
            removedSpace = re.sub(r'\n', '', rows[i].text)
            removedSpace = re.sub(r'\t', '', removedSpace)
            removedSpace = re.sub(r':', ';', removedSpace)
            splitted = removedSpace.split(';')
            club1.append(splitted[0])
            club2.append(splitted[1][0:-1])

    df.insert(len(df.columns), "Heim", club1)
    df.insert(len(df.columns), "Gast", club2)


    # In[63]:


    #Datum und Liga auslesen (befindet sich in jeder 3. Zeile ab 2. Zeile)
    for data in table.find_all('tbody'):
        rows = data.find_all('tr')
        logos_home = list()
        logos_guest= list()
        for i in range(2,len(rows),3):
            #entfernt Sonderzeichen wie Zeilenumbruch (n) und Tab (t)
            logo = rows[i].find_all('div', class_="club-logo") #rows[i].text
            
            logo_link = re.findall(r'//(\S+)\">', str(logo))
            logos_home.append(logo_link[0])
            logos_guest.append(logo_link[1])
            
    #found = re.search('AAA(.+?)ZZZ', string).group(1)

    df.insert(len(df.columns), 'Logo Heim', logos_home)
    df.insert(len(df.columns), 'Logo Gast', logos_guest)


    # In[64]:


    df


    # In[65]:


    links = table.find_all('a')
    homeLinks = list();
    guestLinks = list();
    spielLinks = list();
    for i in range(2, len(links),6):
        homeLinks.append(links[i].get('href'))
        guestLinks.append(links[i+1].get('href'))
        spielLinks.append(links[i+2].get('href'))
    df.insert(len(df.columns), "home_link", homeLinks)
    df.insert(len(df.columns), 'guest_link', guestLinks)
    df.insert(len(df.columns), 'Spiel', spielLinks)
    df


    # In[66]:


    #merge columns to table
    if (idx==0):
        df.to_csv('out.csv', index=False)
    else:
        df.to_csv('out.csv', mode='a', index=False, header=False)





