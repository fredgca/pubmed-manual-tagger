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

import gtk
import xml.etree.ElementTree as etree
from term import Term

def get_data_from_ncbi_xml(filename):
    """
    Given a filename for a NCBI xml, returns a dictionary
    with pmid, journal_title, article_title, article_abstract, 
    publication_year
    """
    data = {}
    try:
        abstract = etree.parse(filename)
    except:
        return None
            
    data["pmid"] = abstract.findall(".//PMID")[0].text # a string
    data["journal_title"] = abstract.findall(".//Title")[0].text # a string
    data["article_title"] = abstract.findall(".//ArticleTitle")[0] # A elementTree element
    data["article_abstract"] = abstract.findall(".//AbstractText") # A list of elementTree elements
    data["publication_year"] = abstract.findall(".//PubDate")[0].getchildren()[0].text #a string
    return data


def get_abstract_text_from_etree(data):
    """
    Given a dictionary like that retured by get_data_from_ncbi_xml,
    return a string with abstract text
    """
    abstract = unicode("")
    for abstract_section in data["article_abstract"]:
        if len(abstract) == 0:
            abstract += unicode(abstract_section.text)
        else:
            abstract += " " + unicode(abstract_section.text)

    return abstract

def load_annotated_xml(xml_filename):
    """
    Given the name of a xml containing a NCBI abstract,
    with AbstractText annotated by Pubmed Tagger
    Create a Gtk.TextBuffer with the 'marked' abstract, 
    return it and a dictionary like {tags: (mark_stat, mark_end)}
    """
    tags = {}
    textbuffer = gtk.TextBuffer()
    data = get_data_from_ncbi_xml(xml_filename)
    if data:
        annotated_abstract_list = data["article_abstract"]
    else:    
        return None, None

    tags_found = 0
    for annotated_abstract in annotated_abstract_list:
        if annotated_abstract_list.index(annotated_abstract) != 0:
            textbuffer.insert(textbuffer.get_end_iter(), " ")

        if annotated_abstract.text:
            if not annotated_abstract.text.isspace(): 
                textbuffer.insert(textbuffer.get_end_iter(),\
                                  annotated_abstract.text)

        tags_found += len(list(annotated_abstract)) ########Debuging
        for child in list(annotated_abstract):        
            tag = child.tag
            attr_name = child.attrib.keys()[0]
            attr_value = child.attrib[attr_name]
            text = child.text
            tail = child.tail
            pygtk_tag_name = '%s %s="%s"' %(tag, attr_name, attr_value)
            if text: 
                end_iter = textbuffer.get_end_iter()
                textmark_before = textbuffer.create_mark(None, end_iter, True)               
                textbuffer.insert(end_iter,text)
                new_end_iter = textbuffer.get_end_iter()
                textmark_after = textbuffer.create_mark(None, new_end_iter, True)       
                if pygtk_tag_name.startswith("MESH") or \
                   pygtk_tag_name.startswith("Cell") or \
                   pygtk_tag_name.startswith("Molecular_Role") or \
                   pygtk_tag_name.startswith("Mtb_Gene") or \
                   pygtk_tag_name.startswith("Gene"):
                    if pygtk_tag_name in tags.keys():
                        tags[pygtk_tag_name].append((textmark_before, textmark_after))
                    else:
                        tags[pygtk_tag_name] = [(textmark_before, textmark_after)]

            if tail:
                textbuffer.insert(textbuffer.get_end_iter(),tail)

    
    print "Tags found: ", tags_found #for debugging
    data["article_abstract"] = textbuffer
    return data, tags

def replace_etree_element(original, new):
    """
    A internal function to replace a subelement of
    a elementTree
    """
    original.clear()
    original.text = new.text
    original.tail = new.tail
    original.tag = new.tag
    original.attrib = new.attrib
    original[:] = new[:]

def save_annotated_abstract(filename, textbuffer):
    """
    Given the file name of a saved NCBI abstract (xml) 
    and a gtk.textbuffer containing an annotated abstract with gtk.tags, 
    replace the current Abstract Element with the content of the textbuffer.
    The tags in the textbuffer are saved as XML elements.
    """
    start,end = textbuffer.get_bounds()
    #Creating the new XML Element
    Abstract = etree.Element("Abstract")
    AbstractText = etree.SubElement(Abstract, "AbstractText")
    #Iterating over the textbuffer
    next_tag_iter = start.copy()
    has_other_tag = next_tag_iter.forward_to_tag_toggle(None)
    children_tags = []
    if not start.begins_tag() and has_other_tag:
        AbstractText.text = textbuffer.get_text(start,next_tag_iter)
        start = next_tag_iter.copy()
    elif not start.begins_tag() and not has_other_tag:
        AbstractText.text = textbuffer.get_text(start,end)
        start = next_tag_iter.copy()

    while has_other_tag:
        tags = start.get_tags()
        tag = tags[0].get_property("name").split("Annotation")
        tag_name = tag[0].strip()
        tag_attribute = tag[1].split("=")[1].strip().replace("\"", "")
        next_tag_iter = start.copy()
        next_tag_iter.forward_to_tag_toggle(None)
        tail_tag_iter = next_tag_iter.copy()
        has_other_tag = tail_tag_iter.forward_to_tag_toggle(None)
        if has_other_tag:
            children_tags.append(etree.SubElement(AbstractText, tag_name,
                                 attrib = {"Annotation": tag_attribute}))
            children_tags[-1].text = textbuffer.get_text(start, next_tag_iter)
            children_tags[-1].tail = textbuffer.get_text(next_tag_iter, tail_tag_iter)

        else:
            children_tags.append(etree.SubElement(AbstractText, tag_name,
                                 attrib = {"Annotation": tag_attribute}))
            children_tags[-1].text = textbuffer.get_text(start, next_tag_iter)
            children_tags[-1].tail = textbuffer.get_text(next_tag_iter, textbuffer.get_end_iter())

        start = tail_tag_iter.copy()           

    abstract_xml = etree.parse(filename)
    replace_etree_element(abstract_xml.findall(".//Abstract")[0], Abstract)
    abstract_xml.write(filename)


def abstract2xml(abstract, terms):
    """
    Given an abstract(str) and a list of Terms (class Term)
    Return an elementtree 'Abstract', with each term as an elementtree 
    tagged with 'MESH' and attribute MESH unique identifier
    TODO: this method is not storing all annotations when multiples are 
    added to the same term
    """
    Abstract = etree.Element("Abstract")
    AbstractText = etree.SubElement(Abstract, "AbstractText")
    AbstractText.text = abstract[0:int(terms[0].start)]
    #AbstractText.tail = abstract[int(terms[-1].end):]

    terms_elements = []
    for term in terms:
        #Get next and previous term.
        if terms.index(term) != len(terms)-1: 
            next_term = terms[terms.index(term)+1]
        else:
            next_term = Term("None", float("+inf"), float("+inf"), 0, "None")

        if terms.index(term) != 0:
            previous_term = terms[terms.index(term)-1]
        else:
            previous_term = Term("None", float("-inf"), float("-inf"), 0, "None")

        #TODO If three terms overlaps
        #if adjacent terms are not overlapping
        if next_term.start > term.end and term.start > previous_term.end:
            #print "if", terms.index(term), len(terms), next_term.start, term.end, term.term, term.id,#for debugging
            terms_elements.append(etree.SubElement(AbstractText, term.tag,
                                        attrib = {"Annotation": str(term.id)}))

            terms_elements[-1].text = abstract[term.start: term.end]
            if next_term.term != "None":
                terms_elements[-1].tail = abstract[term.end: next_term.start]
            else:
                terms_elements[-1].tail = abstract[term.end:]

            #print terms_elements[-1].text, terms_elements[-1].tail #for debugging

        #if the current term overlaps the precedent
        elif term.start < previous_term.end and term.end < next_term.start:
            #print "elif", terms.index(term), len(terms), term.start, previous_term.end, term.term, term.id, #for debugging
            annotation = "%s|%s" %(term.id, next_term.id)
            terms_elements.append(etree.SubElement(AbstractText, term.tag,
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




