
import requests
import csv
import re
from bs4 import BeautifulSoup
import pandas as pd

team_urls = pd.read_csv('Spiele_Links.csv')
print(len(team_urls))

for idx in range(1,len(team_urls), 1):
    
	print(len(team_urls))
	url = team_urls['url'][idx]
	response = requests.get(url)
    
	#BeautifulSoup HTML-Dokument aus dem Quelltext parsen
	soup= BeautifulSoup(response.text, 'html.parser')
    

