#    Copyright 2011 Frederico G. C. Arnoldi <fgcarnoldi /at/ gmail /dot/ com>
#
#    This file is part of PubMed Manual Tagger.
#
#    PubMed Manual Tagger is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    PubMed Manual Tagger is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with PubMed Tagger.  If not, see <http://www.gnu.org/licenses/>.
import time
import xml_tools
import xml.etree.ElementTree as etree
import multiprocessing
import itertools
from string import ascii_lowercase as lts    
from pysqlite2 import dbapi2 as sqlite

class Term:
    """
    This class models MESH terms. 
    Each Term has the following attributes:
        - term 
        - start position in a given abstract
        - end position in a given abstract
        - ui, the MESH unique identifier
    """
    def __init__(self,term,start,end,ui):
        self.term = term
        self.start = start
        self.end = end
        self.ui = ui

    def __contains__(self,item):
        if self.start <= item.start and\
           self.end >= item.end and \
           item.term in self.term and \
           item.term != self.term:
            return 1
        else:
            return 0

    def __str__(self):
        return "%s(%s)" %(self.term, self.start)

    def __repr__(self):
        return "%s(%s)" %(self.term, self.start)


def find_term(mesh_entry_ui):
    #mesh_entry_ui = data[0]
    #abstract_lower = data[1]
    #abstract_lenght = data[2]
    term_positions = []
    mesh_entry = mesh_entry_ui[0].lower()
    ui = mesh_entry_ui[1]
    ###Search MESH terms using find method
    term_start_position = abstract_lower.find(mesh_entry)
    while term_start_position < abstract_lenght and term_start_position != -1: 
        if term_start_position !=  0: 
            term_end_position = term_start_position + len(mesh_entry)
            #check whether the word is the first one of the sentence
            #if term_start_position == 0:                                           
            #    left_char = ""
            #else:
            left_char = abstract_lower[term_start_position-1]
   
            #check whether the word is the last of the sentence                
            if term_end_position < abstract_lenght:
                right_char = abstract_lower[term_end_position]                   
            else:
                right_char = ""
    
            #check whether the term is part of larger word 
            if right_char not in lts and left_char not in lts:
                term_positions.append(Term(mesh_entry, term_start_position, 
                                                    term_end_position, ui))
            #else:
            #    pass
        
        #else:
        #    pass
    
        term_start_position = abstract_lower.find(mesh_entry,term_start_position+1)
    
    return term_positions


def recognize_mesh_entries(mesh_entries, abstract):
    """
    Recieve a list with tuples (mesh_term, ui) and an abstract(str)
    return a list o Terms, sorted by start_tem_position
    """
    global abstract_lenght, abstract_lower
    abstract_lenght = len(abstract)
    abstract_lower = abstract.lower()
    founds = 0
    terms_find = []
    pool = multiprocessing.Pool()
    time_i = time.time()
    terms_find = pool.map_async(find_term, mesh_entries).get() 
                                                #[abstract_lower]*len(mesh_entries),
                                                #[abstract_lenght]*len(mesh_entries))).get()
    terms_find = [term for terms in terms_find 
                       for term in terms]# if term]
    print "Terms recognition took (secs): ", time.time() - time_i
    #Filter 'subterms'
    filtered_terms = []            
    for term_1 in terms_find:
        is_subset = 0 
        for term_2 in terms_find:
            if term_1 in term_2:
                is_subset = 1
                break

        if not is_subset: filtered_terms.append(term_1)

    terms = sorted(filtered_terms, key=lambda term: term.start)
    print "Number of total and filtered found: ", founds, len(terms) #for debugging
    return terms

def abstract2xml(abstract, terms):
    """
    Given an abstract(str) and a list of Terms (class Term)
    Return an elementtree 'Abstract', with each term as an elementtree 
    tagged with 'MESH' and attribute MESH unique identifier
    """
    Abstract = etree.Element("Abstract")
    AbstractText = etree.SubElement(Abstract, "AbstractText")
    AbstractText.text = abstract[0:int(terms[0].start)]
    AbstractText.tail = abstract[int(terms[-1].end):]

    terms_elements = []
      
    for term in terms:
        if terms.index(term) != len(terms)-1: 
            next_term = terms[terms.index(term)+1]
        else:
            next_term = Term("None", float("+inf"), float("+inf"), 0)

        if terms.index(term) != 0:
            previous_term = terms[terms.index(term)-1]
        else:
            previous_term = Term("None", float("-inf"), float("-inf"), 0)

        #TODO If three terms overlaps
        #if adjacent terms are not overlapping
        if next_term.start > term.end and term.start > previous_term.end:
            #print "if", terms.index(term), len(terms), next_term.start, term.end, term.term, term.ui,#for debugging
            tag_name = "MESH_automatic"
            terms_elements.append(etree.SubElement(AbstractText, "MESH",
                                        attrib = {"Annotation": term.ui}))

            terms_elements[-1].text = abstract[term.start: term.end]
            if next_term.term != "None":
                terms_elements[-1].tail = abstract[term.end: next_term.start]
            else:
                terms_elements[-1].tail = abstract[term.end:]

            #print terms_elements[-1].text, terms_elements[-1].tail #for debugging

        #if the current term overlaps the precedent
        elif term.start < previous_term.end and term.end < next_term.start:
            #print "elif", terms.index(term), len(terms), term.start, previous_term.end, term.term, term.ui, #for debugging
            tag_name = "MESH_automatic"
            annotation = "%s|%s" %(term.ui, next_term.ui)
            terms_elements.append(etree.SubElement(AbstractText, "MESH",
                                        attrib = {"Annotation": annotation}))
            terms_elements[-1].text = abstract[previous_term.start: term.end]
            if next_term.term != "None":
                terms_elements[-1].tail = abstract[term.end:next_term.start]
            else:
                terms_elements[-1].tail = abstract[term.end:]

            #print terms_elements[-1].text, terms_elements[-1].tail  #for debugging

        #if the current term overlaps the next
        elif term.start > previous_term.end and term.end > next_term.start:
            #print "******elif pass*****", term.term, next_term.term #for debugging
            pass

    return Abstract

def create_annotated_abstract_xml(ncbi_xml, abstract, mesh_entries, annotated_filename):
    terms = recognize_mesh_entries(mesh_entries, "".join(abstract))
    xml_annotated_abstract = abstract2xml(abstract, terms)
    xml_tools.replace_etree_element(ncbi_xml.findall(".//Abstract")[0], 
                                    xml_annotated_abstract)
    ncbi_xml.write(annotated_filename)
    

def get_mesh_entries():
    try:
        db_connection = sqlite.connect("mesh.db")
    except: 
        return 0
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    mesh_entries = list(cursor.execute("select * from mesh_entries_table"))
    mesh_entries = [(x[0].lower(), x[1]) for x in mesh_entries]
    return mesh_entries

