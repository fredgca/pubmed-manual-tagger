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
#    along with PubMed Manual Tagger.  If not, see <http://www.gnu.org/licenses/>.

import multiprocessing 
from string import find, lower, ascii_lowercase as left_lts    
#import time,sys,os,gc #debugging

common_words = ("was", "what", "with", "where", "when", "can", "and", "its",
                "this", "will", "had", "have", "age", "end", "key", "act")

tag_priorities = {"Cell":5,
                  "Molecular_Role":4,
                  "Gene": 3,
                  "MESH": 1,
                  "Mtb_Gene": 2}

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

def find_terms(terms):
    """
    Given a list of tuples, each containing a term and its id
    return a list of terms found in the global variable abstract lower
    """
    #print "\nfind_terms", tag, terms[:10]
    right_lts = left_lts.replace("s", "").replace("e", "")
    local_tag =  tag
    local_abstract_lenght = abstract_lenght
    local_abstract_lower = abstract_lower + "  " # the " " is to avoid IndexError
    term_positions = []
    for entry_id in terms:
        entry, Id = entry_id[0], entry_id[1]
        entry_length = len(entry)
        if entry_length < 2:
            continue    
        ###Search terms using find method
        right_char, left_char = "  "," "
        term_start_position = find(abstract_lower, entry)
        term_end_position = term_start_position + entry_length
        while term_start_position < local_abstract_lenght and \
              term_start_position != -1: 
            if term_start_position !=  0: 
                term_end_position = term_start_position + entry_length
                left_char = abstract_lower[term_start_position-1]           
                if term_end_position+1 < local_abstract_lenght:
                    #for checking whether the word is the last of the sentence                
                    right_char = abstract_lower[term_end_position] + \
                                 abstract_lower[term_end_position+1]                                      
                else:
                    right_char = "xx"
            
            else:
                if term_end_position < local_abstract_lenght:
                    #for checking whether the word is the last of the sentence                
                    right_char = abstract_lower[term_end_position] + \
                                 abstract_lower[term_end_position+1]                   
                    left_char = " "
                else:
                    right_char = "xx"
        
            if right_char[0] not in right_lts and left_char not in left_lts:
                if right_char == "es":
                    term_positions.append(Term(entry, term_start_position, 
                                               term_end_position+2, Id, local_tag))

                elif right_char == "s ":
                    term_positions.append(Term(entry, term_start_position, 
                                               term_end_position+1, Id, local_tag))

                elif right_char[0] == " ":
                    term_positions.append(Term(entry, term_start_position, 
                                               term_end_position, Id, local_tag))

                else:
                    pass

            term_start_position = find(abstract_lower, entry, 
                                       term_start_position+1)
            
    return term_positions



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

    def recognize_terms(self,all_terms, parallel = 0):
        """
        Recieve a list with tuples (mesh_term, id), an abstract(str), and a tag for it
        return a list of Terms, sorted by start_tem_position
        """
        if parallel:
            #parallel version
            all_terms_lenght = len(all_terms)
            #divide all_terms in 64 parts
            sliced_all_terms = [all_terms[x:x + all_terms_lenght/64] 
                                for x in xrange(0,all_terms_lenght, all_terms_lenght/64)]
            pool = multiprocessing.Pool() 
            found_terms = pool.map_async(find_terms, sliced_all_terms).get() 
            pool.close()
            pool.join() 
            found_terms = [term for terms in found_terms
                                for term in terms]
        else:
            found_terms = find_terms(all_terms)  
  
        return found_terms

    def filter_terms2(self, found_terms):
        """
        Given a list of Terms, remove 'subterms', likely 
        false-positives, and merge different identifications 
        for the same term.
        """
        #Filter 'subterms', like cell inside a t-cell
        filtered_terms_1 = []            
        for term_1 in found_terms:
            if term_1.term not in common_words:
                remove = 0 
                for term_2 in found_terms:
                    #Check if term_1 is a subterm of term_2
                    if term_1 in term_2:
                        remove = 1
                        break

                if not remove: filtered_terms_1.append(term_1)
            else:
                pass

        #recognizing diferent meanings for the same term        
        term2meanings = {}
        meaning2synonyms ={}
        for term in filtered_terms_1:
            if (term.start, term.end) in term2meanings.keys():
                term2meanings[(term.start, term.end)].append((term.id, term))
            else:
                term2meanings[(term.start, term.end)] = [(term.id, term)]

            if term.id in meaning2synonyms.keys():
                meaning2synonyms[term.id].append(term.term)
            else:
                meaning2synonyms[term.id] = [term.term]

        #print "See which terms are ambiguous"
        #for x,y in term2meanings.items():
        #    print x,y

        #print "\n\n\nmeaning2synonyms", meaning2synonyms, "\n\n\n***********"

        #selecting most probable meaning
        probable_meanings = []
        for term, meanings in term2meanings.items():
            if len(meanings) == 1:
                probable_meanings.append(meanings[0][1])
            else:            
                probable = []
                #find the meaning with the greatest number of synonyms found in 
                #the text
                current_n_syns = 0
                current_meaning = []
                current_term_by_semantics = []
                for meaning in meanings:
                    list_of_syns = meaning2synonyms[meaning[0]]
                    if len(set(list_of_syns)) > current_n_syns:
                        current_n_syns = len(set(list_of_syns))
                        current_meaning = [meaning[1]]
                    elif len(set(list_of_syns)) == current_n_syns:
                        current_meaning.append(meaning[1])
                    else:
                        pass
                    #try to make the disambiguation by semantic type
                    if not current_term_by_semantics:
                        current_term_by_semantics.append(meaning[1])
                    else:
                        if tag_priorities[meaning[1].tag] < \
                           tag_priorities[current_term_by_semantics[0].tag]:
                            current_term_by_semantics = [meaning[1]]
                        elif tag_priorities[meaning[1].tag] == \
                             tag_priorities[current_term_by_semantics[0].tag]:
                            current_term_by_semantics.append(meaning[1])
                        else:
                            pass

                #check if number of synonyms solved the problem
                if len(current_meaning) == 1:
                    #print "\nBy Synonyms number: ", current_meaning, meanings
                    probable_meanings.append(current_meaning[0])
                else:
                    #try to make the disambiguation by semantic type
                    if len(current_term_by_semantics) == 1:
                        probable_meanings.append(current_term_by_semantics[0])
                        #print "\nBy Semantic type: ", current_term_by_semantics[0], meanings

                    #by now, just pick the first
                    #TODO: look for other informations, like term co-ocurrence    
                    else:                
                        probable_meanings.append(current_term_by_semantics[0])
                        #print "\nJust the first: ", \
                        #      current_term_by_semantics[0], meanings

                        pass
    

        sorted_meanings = sorted(probable_meanings, key=lambda term: term.start)
        #print "\nfiltered_terms_1 ", len(sorted(filtered_terms_1, key=lambda term: term.start)), 
        #print "sorted_meanings ", len(sorted_meanings)

        return sorted_meanings
