import pywikibot
from pywikibot import pagegenerators
import wikitextparser as wtp

site = pywikibot.Site('fr','wiktionary')
repo = site.data_repository()

def get_entries_in_category():
    cat = pywikibot.Category(site,'Homographes non homophones en français')
    entries = pagegenerators.CategorizedPageGenerator(cat)
    #for entry in entries:
    #    print(f"--- {entry} ---\n{entry.text}")
    return entries

def extract_french_section(wikicode):
    content =""
    is_french_section = False
    for line in wikicode.split("\n"):
        
        if "=={{langue|fr}}==" in line.replace(" ",""):
            is_french_section = True
            
        if ("=={{langue|" in line.replace(" ","") and
            not "fr}}==" in line.replace(" ","")):
            is_french_section = False

        if is_french_section:
            content += line +"\n"
            
    return content

def simplify_def(nature, definition):
    if "Pluriel de" in definition :
        word = definition[definition.find("[[")+2:definition.find("]]")]
        if "|" in word:
            word = word[word.find("|")+1:]                        
        return "(pluriel de " + word + ")"

    elif ("personne du singulier d" in definition or
        "personne du pluriel de" in definition):
        word = definition[definition.find("[[")+2:definition.find("]]")]
        if "|" in word:
            word = word[word.find("|")+1:]                       
        return "(forme conjuguée de " + word + ")"

    elif nature == "nom":
        return "(nom commun)"

    else:
        print(f"No simplified definition have been created for {definition} ({nature})")

    return ""
        
def get_pronunciation_and_definition(wikicode):
    pron_and_def = dict()
    pron_and_nature = dict()
    nature = ""
    pron = ""
    definition = ""
    
    for line in wikicode.split("\n"):
        # Get the word nature (noun, verb, etc.)
        if ("=={{S|" in line.replace(" ","") and
            "}}==" in line.replace(" ","")):
            pos1 = line.find("{{S|")
            pos2 = line.find("|fr", pos1)
            nature = line[pos1+4:pos2]

        # Get the pronunciation 
        if "{{pron|" in line and nature:
            pos1 = line.find("{{pron|")
            pos2 = line.find("|fr}}", pos1)
            pron = line[pos1+7:pos2]

        # Get the definition
        if "#" in line and not "#*" in line and pron:
            definition = line[line.find("#")+1:]

        if definition:
            pron_and_nature[pron] = nature
            pron_and_def[pron] = definition
            nature = ""
            pron = ""
            definition = ""

    return pron_and_nature, pron_and_def
            
def update_list():
    entries = get_entries_in_category()
    for entry in entries:
        wikicode = entry.text
        french_section = extract_french_section(wikicode)
        pron_and_nature, pron_and_def = get_pronunciation_and_definition(french_section)
        #print(f" >>> {entry} <<<\n")

        # Check whether at least two different pronunciations have been found
        if len(pron_and_nature)<2 or len(pron_and_def)<2:
            print(f"PROBLEM: {entry}\n")
            for item in pron_and_nature.items():
                print(item)
            print("END PROBLEM")

        '''
        for (p1,n), (p2,d) in zip(pron_and_nature.items(), pron_and_def.items()):
            print(f"{p1}/{p2} -> {n} ... {d} -> «{simplify_def(n,d)}»")
        '''
        
def main():
    update_list()
    
if __name__ == "__main__":
    main()
