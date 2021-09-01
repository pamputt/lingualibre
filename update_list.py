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
    content = ""
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

def manual_definition(pron, nature):
    #Agni
    if pron == "aɡ.ni" and nature == "nom propre":
        return "(dieu hindou)"
    if pron == "a.ɲi" and nature == "nom":
        return "(peuple d'Afrique de l'Ouest)"

    #Aimes
    if pron == "ɛm" and nature == "prénom":
        return "(prénom masculin)"
    if pron == "ɛmz" and nature == "nom de famille":
        return "(nom de famille anglais)"

    #alien
    if pron == "a.ljɛ̃" and nature == "adjectif":
        return "(adjectif désuet)"
    if pron == "a.ljɛn" and nature == "nom":
        return "(extraterrestre)"

    #archée
    if pron == "aʁ.ʃe" and nature == "nom":
        return "(portée d'un arc)"
    if pron == "aʁ.ke" and nature == "nom":
        return "(microorganisme)"

    #archéen/archéens
    if pron == "aʁ.ke.ɛ̃":
        if nature == "adjectif":
            return "(relatif à l'Archéen)"
        if nature == "nom":
            return "(terme géologique)"
    if pron == "aʁ.ʃe.ɛ̃":
        if nature == "adjectif":
            return "(relatif à la commune française Arches)"
        if nature == "nom":
            return "(habitant d'Arches)"

    #archéenne/archéennes
    if pron == "aʁ.ke.ɛn" and nature == "adjectif":
        return "(relatif à l'Archéen)"
    if pron == "aʁ.ʃe.ɛn" and nature == "adjectif":
        return "(relatif à la commune française Arches)"

    #cimer
    if pron == "si.mɛʁ" and nature == "interfjection":
        return "(verlan de merci)"
    
    return None

def simplify_def(pron, nature, definition):
    #First, try to get a hard-coded definition
    manual_def = manual_definition(pron, nature)
    if manual_def:
        return manual_def
    
    elif "Pluriel de" in definition :
        word = definition[definition.find("[[")+2:definition.find("]]")]
        if "|" in word:
            word = word[word.find("|")+1:]                        
        return "(pluriel de " + word + ")"

    elif ("personne du singulier d" in definition or
          "personne du pluriel d" in definition):
        word = definition[definition.find("[[")+2:definition.find("]]")]
        if "|" in word:
            word = word[word.find("|")+1:]                       
        return "(forme conjuguée de " + word + ")"

    elif nature == "adjectif":
        return "(adjectif)"
    
    elif nature == "adjectif démonstratif":
        return "(adjectif démonstratif)"
    
    elif nature == "adverbe":
        return "(adverbe)"
    
    elif nature == "nom":
        return "(nom commun)"
    
    elif nature == "nom de famille":
        return "(nom de famille)"        
    
    elif nature == "prénom":
        if "masculin" in definition:
            return "(prénom masculin)"
        if "féminin" in definition:
            return "(prénom féminin)"
    
    elif nature == "verbe":
        return "(verbe)"

    else:
        print(f"No simplified definition have been created for {definition} ({nature})")

    return None
        
def get_pronunciation_and_definition(wikicode):
    pron_and_def = dict()
    pron_and_nature = dict()
    nature = ""
    prons = list()
    definition = ""
    
    for line in wikicode.split("\n"):
        # Get the word nature (noun, verb, etc.)
        if ("=={{S|" in line.replace(" ","") and
            "}}==" in line.replace(" ","")):
            pos1 = line.find("{{S|")
            pos2 = line.find("|fr", pos1)
            nature = line[pos1+4:pos2]

        # Get the pronunciation(s)
        if "{{pron|" in line and nature:
            pos1 = 0
            while line.find("{{pron|",pos1)>0:
                pos1 = line.find("{{pron|",pos1)
                pos2 = line.find("|fr}}", pos1)
                prons.append(line[pos1+7:pos2])
                pos1 = pos2

        # Get the definition
        if ("#" in line
            and not "#fr" in line
            and not "#*" in line
            and len(prons)>0):
            definition = line[line.find("#")+1:]

        if definition:
            for pron in prons:
                pron_and_nature[pron] = nature
                pron_and_def[pron] = definition
            nature = ""
            definition = ""
            prons.clear()

    return pron_and_nature, pron_and_def
            
def update_list():
    entries = get_entries_in_category()

    
    for entry in entries:
        wikicode = entry.text
        french_section = extract_french_section(wikicode)
        #print(f" >>> {french_section} <<<\n")
        
        pron_and_nature, pron_and_def = get_pronunciation_and_definition(french_section)
        print(f" >>> {entry} <<<\n")
        
        # Check whether at least two different pronunciations have been found
        if len(pron_and_nature)<2 or len(pron_and_def)<2:
            print(f"PROBLEM: {entry}\n")
            for item in pron_and_nature.items():
                print(item)
            print("END PROBLEM")
    
        
        for (p1,n), (p2,d) in zip(pron_and_nature.items(), pron_and_def.items()):
            if p1 != p2:
                print(f"{p1} and {p2} are different!")
                return;
            
            new_def = simplify_def(p1, n, d)
            if not new_def:
                new_def = manual_definition(p1,n)
            print(f"{p1}/{p2} -> {n} ... {d} -> «{new_def}»")
        
        
def main():
    update_list()
    
if __name__ == "__main__":
    main()
