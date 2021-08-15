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
    ?record ?file ?language 
    ?speaker ?transcription ?typeIssue
    ?targetLanguage ?usedLanguage
    ?targetLanguageWikidataID ?usedLanguageWikidataID
WHERE {
  ?record prop:P2  entity:Q2 .
  ?record prop:P3  ?file .
  ?record prop:P4  ?language .
  ?record prop:P5  ?speaker .
  ?record prop:P7  ?transcription .
  OPTIONAL {?record prop:P33 entity:Q593546 .}

  OPTIONAL {?record llp:P33 ?issueStatement .}
  OPTIONAL {?issueStatement llq:P34 ?targetLanguage .}
  OPTIONAL {?issueStatement llq:P35 ?usedLanguage .}

  OPTIONAL {?targetLanguage prop:P12 ?targetLanguageWikidataID .}
  OPTIONAL {?usedLanguage prop:P12 ?usedLanguageWikidataID .}

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
                "speaker": sparql.format_value(record, "speaker"),
                "transcription": sparql.format_value(record, "transcription"),
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
    
    oldtext = pageCommons.get()
    newtext = text_replace(oldtext, record["usedLangWD"], record["targetLangWD"])
    if newtext == oldtext:
        return

    if DEBUG:
        print("COMMONS")
        print(pageCommons.get()) #print the wikicode
        print(f"\n{newtext}\n")

    pageCommons.text=newtext
    pageCommons.save("Fix wrong language code")

    
def modify_LinguaLibre(record):
    p_language = "P4"
    p_type_of_issue = "P33"
    p_target_language = "P34"
    p_used_language = "P35"
    
    item = None
    if DEBUG: 
        item = pywikibot.ItemPage(siteLL, "Q595275") # sandbox item
    else:
        item = pywikibot.ItemPage(siteLL, record["id"])  # a repository item
        
    data = item.get()  # get all item data from repository for this item

    if DEBUG:
        print('\nLINGUALIBRE')
        print(data) #print item content


    if not item.claims: # no statements found in this item
        return

    # Modifying the language
    if p_language not in item.claims: # property P4 (language) not found in this item
        return
    
    for claim in item.claims[p_language]: # item.claims['P4'] is a list of all P4 claims over which one wants to loop here
        targetItem = pywikibot.ItemPage(siteLL, record["targetLang"])
        if claim.getTarget() == targetItem: # claim is target language, skip
            print(f"The current language ({claim.getTarget().title()}) is already the target language ({record['targetLang']})")
            continue
        usedLangItem = pywikibot.ItemPage(siteLL, record["usedLang"])
        if claim.getTarget() == usedLangItem:
            claim.changeTarget(targetItem)
        else:
            print(f"The current language ({claim.getTarget().title()}) is different than the used language ({record['usedLang']})")


    # Removing P33
    if p_type_of_issue not in item.claims: # property P33 (type of issue) not found in this item
        return
    
    for claim in item.claims[p_type_of_issue]: # item.claims['P33'] is a list of all P33 claims over which one wants to loop here
        # Check whether qualifiers are the good ones
        if not claim.has_qualifier(p_used_language, record["usedLang"]):
            return 
        if not claim.has_qualifier(p_target_language, record["targetLang"]):
            return
        item.removeClaims(claim) #Removing claim

    # Modifying the label
    # TODO: modify label to take into account language code modification
    # Example: "audio record - fra - Darmo117 (Darmo117)"
    # -> "audio record - eng - Darmo117 (Darmo117)"
            
def get_correct_recording(record):

    transcription = record["transcription"]
    speaker = record["speaker"]

    # Look for recordings that have:
    #* the same speaker
    #* the same transcription
    #* the language that is equal to the target language of the erroneous recording
    sparql = Sparql(ENDPOINT)
    filters = ""
    filters+= "FILTER( ?speaker = entity:" + speaker + ") ."
    filters+= "FILTER( ?transcription = '" + transcription + "' ) ."
    filters+= "FILTER( ?targetLanguage = ?language ) ."
    query = BASEQUERY.replace("#filters", filters)
    
    raw_records = sparql.request(query)
    if len(raw_records) == 1:
        return raw_records[0]

    return None


def delete_on_Commons(record_to_delete, correct_record):
    print(f"Ask for {record_to_delete['file']} to be deleted on Wikimedia Commons!")

    pageCommons = None
    if DEBUG:
        pageCommons = pywikibot.Page(siteLL, 'User:Pamputt/bot_test')
    else:
        pageCommons = pywikibot.Page(siteCommons, record["file"])

    old_text = pageCommons.get()
    if old_text.find("{{Speedydelete") != -1:
        print("Deletion already taken into account")
        return
        
    targetLangWD = record_to_delete["targetLangWD"]
    usedLangWD = record_to_delete["usedLangWD"]
    
    sparql = Sparql(ENDPOINT)
    correct_file = sparql.format_value(correct_record, "file")

    delete_text = '{{Speedydelete |1=Erroneous language ("' + usedLangWD + '" instead of "' + targetLangWD + '"). '
    delete_text += 'A file with the correct language (and correct name) is available [[:File:' + correct_file + '|here]] (same speaker, same word).}}\n'

    new_text = delete_text + old_text

    if DEBUG:
        print(f"\n{new_text}\n")

    pageCommons.text=new_text
    pageCommons.save("speedy deletion")
    

def delete_on_LinguaLibre(record_to_delete, correct_record):
    print(f"Delete {record_to_delete['id']} on Lingua Libre")

    item = None
    if DEBUG: 
        item = pywikibot.ItemPage(siteLL, "Q595275") # sandbox item
    else:
        item = pywikibot.ItemPage(siteLL, record["id"])  # a repository item

    p_duplicate_item = "P37"
    correct_id = sparql.format_value(correct_record, "record")
    
    claim = pywikibot.Claim(siteLL, p_duplicate_item)
    target = pywikibot.ItemPage(siteLL, correct_id)
    claim.setTarget(target)
    item.addClaim(claim)

    
def process_data():

    # Get the informations of all the records
    filters = ""
    records = get_records(BASEQUERY.replace("#filters", filters).replace("OPTIONAL {","").replace(".}","."))
    counter = 0
    for record in records:
        if DEBUG:
            print(record)

        # Check if a recording by the same speaker and with the same name
        # but with a correct language already exists
        # Get None if not
        correct_record = get_correct_recording(record)
        if correct_record:
            delete_on_Commons(record, correct_record)
            delete_on_LinguaLibre(record, correct_record)
            continue

        modify_Commons(record)
       
        modify_LinguaLibre(record)

        counter = counter+1
        if DEBUG and counter > 0:
            break


def main():
    process_data()


if __name__ == "__main__":
    main()
