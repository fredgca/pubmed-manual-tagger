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
import time,sys,os
import multiprocessing,gc
from string import find, lower, ascii_lowercase as lts    

common_words = ("was", "what", "with", "where", "when", "can", "and", "its")
class Term:
    """
    This class models general terms, like MESH term or Genes. 
    Each Term has the following attributes:
        - term 
        - start position in a given abstract
        - end position in a given abstract
        - id, a unique identifier
        - tag
        - description
        - main_concept
    """
    def __init__(self,term,start,end,Id,tag):
        self.term = term
        self.start = start
        self.end = end
        self.id = Id
        self.tag = tag
        self.description = ""
        self.main_concept = ""
        self.other_references = []

    def __contains__(self,item):
        if self.start <= item.start and\
           self.end >= item.end and \
           item.term in self.term and \
           item.term != self.term:
            return 1
        else:
            return 0

    def __eq__(self,item):
        """
        if self.start == item.start and \
           self.end == item.end:
            return 1
        else:
            return 0
        """

    def __str__(self):
        return "%s(%s,%s,%s)" %(self.term, self.start, self.tag, self.id)

    def __repr__(self):
        return "%s(%s,%s,%s)" %(self.term, self.start, self.tag, self.id)


class Term_Hunter:
    def __init__(self, current_abstract, current_tag):
        global tag,abstract_lenght, abstract_lower, abstract
        abstract = current_abstract
        tag = current_tag
        abstract_lenght = len(current_abstract)
        abstract_lower = lower(abstract)
        #self.tag = tag
        #abstract_lenght = len(abstract)
        #abstract_lower = abstract.lower()

    def find_term(self, entry_id):
        term_positions = []
        try:
            entry = entry_id[0].lower()
        except:
            print "Something wrong with this term? ", entry_id
            return []

        Id = entry_id[1]
        if len(entry) < 2:
            return term_positions

        ###Search terms using find method
        term_start_position = abstract_lower.find(entry)
        while term_start_position < abstract_lenght and term_start_position != -1: 
            if term_start_position !=  0: 
                term_end_position = term_start_position + len(entry)
                left_char = abstract_lower[term_start_position-1]
       
                #check whether the word is the last of the sentence                
                if term_end_position < abstract_lenght:
                    right_char = abstract_lower[term_end_position]                   
                else:
                    right_char = ""
        
                #check whether the term is part of larger word 
                if right_char not in lts and left_char not in lts:
                    term_positions.append(Term(entry, term_start_position, 
                                                        term_end_position, Id, tag))
 
            term_start_position = abstract_lower.find(entry,term_start_position+1)
        
        return term_positions
    

    def recognize_terms(self,all_terms):
        """
        Recieve a list with tuples (mesh_term, id), an abstract(str), and a tag for it
        return a list of Terms, sorted by start_tem_position
        """
        founds = 0
        all_terms_lenght = len(all_terms)
        sliced_all_terms = [all_terms[x:x + all_terms_lenght/64] #parallel version, divide all terms in 10
                            for x in xrange(0,all_terms_lenght, all_terms_lenght/64)] #divide all terms in 10
        timei = time.time()
        pool = multiprocessing.Pool() #parallel version
        found_terms = pool.map_async(find_terms, sliced_all_terms).get() #parallel version
        pool.close() #parallel version
        pool.join() #parallel version
        print time.time() - timei
#        found_terms = [] #serial version
#        for current_term in all_terms:#serial version         
#            found_terms += self.find_term(current_term) #serial version
    
        found_terms = [term for terms in found_terms #parallel version
                            for term in terms] #parallel version

        return found_terms

    def filter_terms(self, found_terms):
        """
        Given a list of Terms, remove 'subterms', likely 
        false-positives, and merge different identifications 
        for the same term.
        """
        tag_priorities = {"Cell":4 ,
                          "Molecular_Role":3 ,
                          "Gene": 2,
                          "MESH": 1}
        #Filter 'subterms', like cell inside a t-cell
        #and references to the same term
        filtered_terms_1 = []            
        for term_1 in found_terms:
            remove = 0 
            for term_2 in found_terms:
                #Check if term_1 is a subterm of term_2
                if term_1 in term_2:
                    remove = 1
                    #break  
                elif term_1.start == term_2.start and\
                     term_1.end == term_2.end:
                    if term_1.id == term_2.id:
                        i1 = found_terms.index(term_1)
                        i2 = found_terms.index(term_2)
                        if i1 < i2:
                            remove = 1
                            #break
                    else:
                        if tag_priorities[term_1.tag] > tag_priorities[term_2.tag]:                    
                            remove = 1                         
                            #break
                        elif tag_priorities[term_1.tag] < tag_priorities[term_2.tag]:
                            #add term_2 to the other_references of term_1
                            term_1.other_references.append(term_2)
                        elif tag_priorities[term_1.tag] == tag_priorities[term_2.tag]:
                            i1 = found_terms.index(term_1)
                            i2 = found_terms.index(term_2)
                            if i1 < i2:
                                remove = 1
                                #break
            if not remove: filtered_terms_1.append(term_1)

        #Filter putative false positives
        #This step is based on that recoginized terms with more than one 
        #synonyms used in the same abstract, it must be selected
        #otherwise, just if it is a long term
        found_entities = {}
        for term in filtered_terms_1:
            if term.id in found_entities.keys():
                if term.term in found_entities[term.id]:
                    pass
                else:
                    found_entities[term.id].append(term.term)
            else:
                    found_entities[term.id] = [term.term]
        
        filtered_terms_2 =[]
        for term in filtered_terms_1:
            if  len(term.term) > 2:
                if len(found_entities[term.id]) > 1:
                    filtered_terms_2.append(term)
                else:
                    if term.tag == "Gene" or "Molecular_Role": 
                        if len(term.term) > 2 and term.term not in common_words:
                            #TODO change this tuple with a "most frequent words" tuple  
                           filtered_terms_2.append(term)
                        else: 
                            pass
                    else:
                        filtered_terms_2.append(term)

        terms = sorted(filtered_terms_2, key=lambda term: term.start)
        return terms   
    

def find_terms(terms):
    local_tag =  tag
    local_abstract_lenght = abstract_lenght
    local_abstract_lower = abstract_lower
    term_positions = []
    for entry_id in terms:
        entry, Id = entry_id[0], entry_id[1]
        entry_length = len(entry)
        if entry_length < 2:
            continue    
        ###Search terms using find method
        term_start_position = find(abstract_lower, entry)
        while term_start_position < local_abstract_lenght and term_start_position != -1: 
            if term_start_position !=  0: 
                term_end_position = term_start_position + entry_length
                left_char = abstract_lower[term_start_position-1]           
                #check whether the word is the last of the sentence                
                if term_end_position < local_abstract_lenght:
                    right_char = abstract_lower[term_end_position]                   
                else:
                    right_char = ""
            
                #check whether the term is part of larger word 
                if right_char not in lts and left_char not in lts:
                    term_positions.append(Term(entry, term_start_position, 
                                                      term_end_position, Id, local_tag))
        
            term_start_position = find(abstract_lower, entry, term_start_position+1)
            
    return term_positions

