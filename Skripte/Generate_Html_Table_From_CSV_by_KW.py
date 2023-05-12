#!/usr/bin/env python
# coding: utf-8

# In[1]:


import csv
import pandas as pd
import codecs


# In[22]:


df = pd.read_csv('out_new.csv', sep=",")
df.head()
weeks=sorted(df.KW.unique())

for kw in weeks:
    print("generate table " + str(kw))
    filename = "Spiele_KW_" + str(kw) + ".html"
    #extract data from current calendar week
    kw_data = df.loc[df['KW']==kw]
    #sort data by date and time
    kw_data = kw_data.sort_values(by=['Datum','Zeit'])

    #write head of table in html
    table_head = "<table id=\"Spiele\">\n"
    table_head += "\t<tr>\n"
    table_head += "\t\t<th>Datum</th>\n"
    table_head += "\t\t<th>ABI Team</th>\n"
    table_head += "\t\t<th>Heim</th>\n"
    table_head += "\t\t<th>Gast</th>\n"
    table_head += "\t\t<th>Ergebnis</th>\n"
    table_head += "\t</tr>"
    #print(table_head)
    f = open(filename, "w")
    f.write(table_head)
    f.close()
    kw_data.head()

    f = open(filename, "a")
    for ind in kw_data.index:
        html_line = "\t<tr>\n"
        html_line += "\t\t<td>" + df['Datum'][ind] + ", " + df['Zeit'][ind] + "</td>\n"
        html_line += "\t\t<td>" +  df['Team'][ind] + "</td>\n"
        html_line += "\t\t<td>" + "<a href=\"" + df['home_link'][ind] + "\" target=\"_blank\">" +  df['Heim'][ind].replace('\u200b','') + "</a></td>\n"
        html_line += "\t\t<td>" + "<a href=\"" + df['guest_link'][ind] + "\" target=\"_blank\">" +  df['Gast'][ind].replace('\u200b','') + "</a></td>\n"
        html_line += "\t\t<td>" + "<a href=\"" + df['Spiel'][ind] + "\" target=\"_blank\">link</a>" + "</td>\n"
        html_line += "\t</tr>\n"
        
        f.write(html_line)
    f.write("</table>")
    f.close()


    # In[18]:


    str(df['Gast'][3].replace('\u200b',''))


    # In[ ]:




