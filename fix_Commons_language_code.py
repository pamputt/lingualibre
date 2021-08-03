# -*- coding: utf-8  -*-

import pywikibot
import re
import requests
import json
from sparql import Sparql

DEBUG = True


ENDPOINT = "https://lingualibre.org/bigdata/namespace/wdq/sparql"
BASEQUERY = """
SELECT DISTINCT
    ?record ?file ?language ?typeIssue
	?targetLanguage ?usedLanguage
	?targetLanguageWikidataID ?usedLanguageWikidataID
WHERE {
  ?record prop:P2  entity:Q2 .
  ?record prop:P3  ?file .
  ?record prop:P4  ?language .
  ?record prop:P33 entity:Q593546 .

  ?record llp:P33 ?issueStatement .
  ?issueStatement llq:P34 ?targetLanguage .
  ?issueStatement llq:P35 ?usedLanguage .

  ?targetLanguage prop:P12 ?targetLanguageWikidataID .
  ?usedLanguage prop:P12 ?usedLanguageWikidataID .

  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
  }
#filters
}"""


siteLL = pywikibot.Site('lingualibre','lingualibre')
repoLL = siteLL.data_repository()

siteCommons = pywikibot.Site('commons','commons')
repoCommons = siteCommons.data_repository()

def text_replace(text, toreplace, replacedby):
    newtext=""
    
    for line in text.split('\n'):
        found = re.match(f"\s*\|\s*languageId\s*\=\s*{toreplace}", line)
        
        if found:
            line = re.sub(f'{toreplace}', f'{replacedby}', line)
            
        newtext += line + "\n"
        
    return newtext


def get_records(query):
    sparql = Sparql(ENDPOINT)
    print("Requesting data")
    raw_records = sparql.request(query)
    print("Request done")
    records = []
    for record in raw_records:
        records += [
            {
                "id": sparql.format_value(record, "record"),
                "file": "File:"+sparql.format_value(record, "file"),
                "language": sparql.format_value(record, "language"),
                "targetLang": sparql.format_value(record, "targetLanguage"),
                "usedLang": sparql.format_value(record, "usedLanguage"),
                "targetLangWD": sparql.format_value(record, "targetLanguageWikidataID"),
                "usedLangWD": sparql.format_value(record, "usedLanguageWikidataID"),
            }
        ]
    print(f"Found {len(records)} records.")
    return records


def modify_Commons(record):
    pageCommons = None
    if DEBUG:
        pageCommons = pywikibot.Page(siteLL, 'User:Pamputt/bot_test')
    else:
        pageCommons = pywikibot.Page(siteCommons, record["file"])

    if DEBUG:
        print("COMMONS")
        print(pageCommons.get()) #print the wikicode
    
    oldtext = pageCommons.get()
    newtext = text_replace(oldtext, record["usedLangWD"], record["targetLangWD"])
    if newtext == oldtext:
        return

    if DEBUG:
        print(f"\n{newtext}\n")

    pageCommons.text=newtext
    pageCommons.save("Fix wrong language code")

    
def modify_LinguaLibre(record):
    item = None
    if DEBUG: 
        item = pywikibot.ItemPage(siteLL, "Q595275")
    else:
        item = pywikibot.ItemPage(siteLL, record["id"])  # a repository item
        
    data = item.get()  # get all item data from repository for this item

    if DEBUG:
        print('\nLINGUALIBRE')
        print(data) #print item content


    if not item.claims: # no statements found in this item
        return
    if 'P4' not in item.claims: # property P4 not found in this item
        return
    for claim in item.claims['P4']: # mind that item.claims['P4'] is a list of all P599 claims over which you want to loop here
        targetItem = pywikibot.ItemPage(siteLL, record["targetLang"])
        if claim.getTarget() == targetItem: # claim is target language, skip
            print(f"The current language ({claim.getTarget().title()}) is already the target language ({record['targetLang']})")
            continue
        usedLangItem = pywikibot.ItemPage(siteLL, record["usedLang"])
        if claim.getTarget() == usedLangItem:
            claim.changeTarget(targetItem)
        else:
            print(f"The current language ({claim.getTarget().title()}) is different than the used language ({record['usedLang']})")


    
def process_data():

    # Get the informations of all the records
    filters = ""
    records = get_records(BASEQUERY.replace("#filters", filters))
    counter = 0
    for record in records:
        if DEBUG:
            print(record)

        modify_Commons(record)
       
        modify_LinguaLibre(record)

        counter = counter+1
        if DEBUG and counter > 0:
            break
    

   
def main():
    process_data()
    
              
if __name__ == "__main__":
    main()
