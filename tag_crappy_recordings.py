# -*- coding: utf-8  -*-

import pywikibot
import sys

# Property values from Lingua Libre
p_type_of_issue = 'P33'  # (type of issue)
p_correct_language ='P34'
p_wrong_language ='P35'
type_of_issue_qids = ['Q593546',#wrong_language_code
                      'Q593593',#wrong_transcription
                      'Q593666']#audio_defect


test_qid = 'Q595275'

site = pywikibot.Site('lingualibre','lingualibre')
repo = site.data_repository()

def get_item(item_id):
    item = pywikibot.ItemPage(repo, item_id)
    item.get()
    return item

def claimQID(claim):
    return "Q"+str(claim.getTarget().getID(True))

def claim_already_present(item, p33_item, correct_language_qid, wrong_language_qid) -> bool:
    """
    Requires an item and the issue we are looking for and returns boolean
    Returns True is p_type_of_issue = p33_item is already present, False otherwise
    """

    item_dict = item.get()
    try:
        claims = item_dict['claims'][p_type_of_issue]
    except KeyError:
        return False

    found = False
    for claim in claims:
        # Check whether this value is already present for this claim
        # and whether qualifiers are present with the same values
        if claimQID(claim) == p33_item:
            found = True

    if not found:
        return False
            
    return True

def add_qualifier(claim, qualifier_property, qualifier_item):
    # Quit if qualifier (property and value) is already present
    if claim.has_qualifier(qualifier_property, qualifier_item):
        return False
        
    qualifier = pywikibot.Claim(repo, qualifier_property)
    qualifier.setTarget(qualifier_item)
    #print(f"Qualifier: {qualifier}")
    claim.addQualifier(qualifier, bot=True)
    return True

def process_data(filename):
    try:
        myfile = open(filename, "r")
    except:
        raise FileNotFoundError(f"{filename} does not exist")

    
    for line in myfile:
        # check for blank line
        if not line.strip():
            continue

        # skip comment lines
        if line[0:1] == "#":
            continue;
        
        words = line.split(',')
        QID = words[0].strip()
        type_of_issue_qid = words[1].strip()
        correct_language_qid = words[2].strip()
        wrong_language_qid = words[3].strip()

        # check for missing argument
        if not QID or not type_of_issue_qid:
            continue

        if type_of_issue_qid == "Q593546": #wrong language code
            if (not correct_language_qid or 
                not wrong_language_qid):
                print("language codes are missing for Q593546")
                continue
        
        # check whether type_of_issue_qid is in the list of known issues
        if type_of_issue_qid not in type_of_issue_qids:
            print(f"{type_of_issue_qid} is not a known element for {p_type_of_issue}")
            continue
            
        if type_of_issue_qid == "Q593546":  
            print(f"Processing {QID} -> {type_of_issue_qid} ({wrong_language_qid} -> {correct_language_qid})")
        else:
            print(f"Processing {QID} -> {type_of_issue_qid}")
        item = get_item(QID)
        already_present = False
        if claim_already_present(item, type_of_issue_qid, correct_language_qid, wrong_language_qid):
            print("already present!")
            already_present = True

        if not already_present:
            claim = pywikibot.Claim(repo, p_type_of_issue)
            target = get_item(type_of_issue_qid)
            claim.setTarget(target)
            item.addClaim(claim, bot=True, summary=f'Adding "type of issue" -> {type_of_issue_qid}')

            correct_language = get_item(correct_language_qid)
            add_qualifier(claim, p_correct_language, correct_language)
            
            wrong_language = get_item(wrong_language_qid)
            add_qualifier(claim, p_wrong_language, wrong_language)
        else:
            for claim in item.claims[p_type_of_issue]:
                # add qualifiers for wrong language code
                if claimQID(claim) == "Q593546": #wrong language code
                    correct_language = get_item(correct_language_qid)
                    add_qualifier(claim, p_correct_language, correct_language)
                    
                    wrong_language = get_item(wrong_language_qid)
                    add_qualifier(claim, p_wrong_language, wrong_language)
        
    myfile.close()   

    
def main():
    
    args = sys.argv
    if len(args) < 2:
        print("Please provide a filename that contains the list of QID to process")
        print("python3 ../core/pwb.py tag_crappy_recordings.py file.txt")
        return
    
    process_data(args[1])
    
if __name__ == "__main__":
    main()
