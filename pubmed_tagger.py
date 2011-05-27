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


import pygtk, gtk.glade
import gtk
import gobject
import urllib2
import xml.etree.ElementTree as etree
import pre_processing
gtk.gdk.threads_init()

class PubMed_Tagger:
    def get_glade_widgets(self):
        """
        Load all widgets from the glade xml file that are listed at 'widget_names'
        """
        widget_names = ["main_window", "abstract_textview","title_textview",
                        "annotation_entry", "pmid_entry", "active_term_entry",
                        "current_annotation_entry",
                        "pmid_button","annotate_button", "untag_button",
                        "reload_tags_button", "tags_combo",
                        "pmid_label", "journal_label", "year_label",
                        "save_button", "open_button",
                        "filechooser_window", "filechooser_ok_button", 
                        "filechooser_cancel_button",
                        "message_window", "message_label", "message_ok_button",
                        "preprocess_checkbutton"
                        ]

        for widget_name in widget_names:
            setattr(self, "_" + widget_name, self.xml_glade.get_widget(widget_name))

    def close_window(self, *args):
        "Close the Pubmed Tagger"
        gtk.main_quit()

    def on_message_ok_button_clicked(self, *args):
        "Close the message_window"
        self._message_window.hide()
        return 1

    def show_message(self,message):
        self._message_label.set_text(message)
        self._message_window.show()

        
    def on_filechooser_ok_button_clicked(self, *args):
        """
        Get the active filename in the filechooser_window and 
        load its data using load_annotated_xml function
        """
        self._filechooser_window.hide()
        filename = self._filechooser_window.get_filename()
        self.current_open_file = filename
        self.load_annotated_xml(filename)

    def on_filechooser_cancel_button_clicked(self, *args):
        "Close the_filechooser_window"
        self._filechooser_window.hide()
    
    def on_open_button_clicked(self, *args):
        "Show the_filechooser_window"
        self._filechooser_window.show()

    def on_pmid_button_clicked(self, pmid,*args):
        """
        Given a PMID, resquest, download the abstract from NCBI, 
        save it in the current folder - as pmid_number.xml - 
        and load it on the interface for annotation
        """
        pmid = self._pmid_entry.get_text()
        pre_process = self._preprocess_checkbutton.get_active()
        try:
            int(pmid)
        except:
            self.show_message("Ops! Check if you provided a valid PMID")
            return 0

        #query = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=%s&retmode=xml&tool=pubmed_tagger_in_development" %pmid
        #result = urllib2.urlopen(query).read()        
        ####        
        output = pmid + ".xml"
        result_xml = etree.parse(output)#result)
        #self.current_open_file = output
        #output_file = open(output, "w")
        #output_file.write(result)
        #output_file.close()

        ####
        data = self.get_data_from_ncbi_xml(output)
        if data and not pre_process:
            self.update_interface(data)

        elif data and pre_process:
            #get abstract text
            self.show_message("This can take a few seconds. Do not close the program")
            abstract = self.get_abstract_text_from_etree(data)
            #recognize mesh terms automatically
            mesh_entries = pre_processing.get_mesh_entries()
            if not mesh_entries:
                self.show_message("Probably you don't have the MESH database in mesh.db file. Contact the developer for help")
                return 0                
            else:
                pass

            #the "".join(abstract) is just to pass a copy of abstract, instead of itself
            entries = pre_processing.recognize_mesh_entries(mesh_entries, "".join(abstract))
            #save annotated text in an xml
            xml_abstract = pre_processing.abstract2xml(abstract, entries)
            annotated_filename = "annotated_" + output
            self.replace_etree_element(result_xml.findall(".//Abstract")[0], xml_abstract)
            result_xml.write(annotated_filename)
            #load annotated xml
            self.load_annotated_xml(annotated_filename)

        else:
            self.show_message("PubMed Tagger was not able to parse %s" %output)

    def on_untag_button_clicked(self, *args):
        try:
            x,y = self.active_term_bounds
        except:
            self.show_message("No annotated term selected")
            return 0

        tags = x.get_tags()
        for tag in tags:
            self.remove_tag(tag, self._abstract_textview, (x, y))


    def on_save_button_clicked(self, *args):
        textbuffer = self._abstract_textview.get_buffer()
        start,end = textbuffer.get_bounds()
        #if there is no text on abstract_textview,
        #cancel saving and emit warning
        if len(textbuffer.get_text(start,end)) == 0:
            self.show_message("There is no text to be saved")
            return

        Abstract = etree.Element("Abstract")
        AbstractText = etree.SubElement(Abstract, "AbstractText")
        next_tag_iter = start.copy()
        has_other_tag = next_tag_iter.forward_to_tag_toggle(None)
        children_tags = []
        if not start.begins_tag() and has_other_tag:
            AbstractText.text = textbuffer.get_text(start,next_tag_iter)
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

           
        filename = self.current_open_file #".xml"
        abstract_xml = etree.parse(filename)
        self.replace_etree_element(abstract_xml.findall(".//Abstract")[0], Abstract)
        abstract_xml.write(filename)


    def on_annotation_button_clicked(self, *args):
        attribute_name = self.get_active_text_in_combobox(self._tags_combo)
        attribute_value = self._annotation_entry.get_text()
        text = self._active_term_entry.get_text().strip()
        if not text:
            self.show_message("There is no selected term to tag")
            return 0

        if attribute_value:
            pygtk_tag = str(attribute_name + ' Annotation="' + attribute_value + '"')
            self.insert_tag(pygtk_tag, self._abstract_textview, self.active_term_bounds)

        else: 
            pygtk_tag = str(attribute_name + ' Annotation=""')
            self.insert_tag(pygtk_tag, self._abstract_textview, self.active_term_bounds)

        #Clearing active term text and bounds
        self._active_term_entry.set_text("")
        self.active_term_bounds = (0,0)
        self._annotation_entry.set_text("")

    def on_copy_clipboard(self, *args):
        clipboard, bounds = self.get_selected_clipboard(self._abstract_textview)
        self._active_term_entry.set_text(clipboard)
        self.active_term_bounds = bounds[:]

    def on_cursor_movement_detected(self, *args):
        """
        Whenever the mouse moves over the abstract_textview
        returns the text annotation in case it tagged with a TextTag
        """
        x,y = self._abstract_textview.get_pointer()
        x_,y_ = self._abstract_textview.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT, x, y)
        tags = self._abstract_textview.get_iter_at_location(x, y).get_tags()
        if tags: 
            self._current_annotation_entry.set_text(tags[0].get_property("name"))
        else:
            self._current_annotation_entry.set_text("")

    def get_selected_clipboard(self, textview):
        """
        Get the selected text from a given textview and
        return the text, and return the Textiters of the text bounds
        """
        textbuffer = textview.get_buffer()
        start,end=textbuffer.get_selection_bounds()
        text = textbuffer.get_text(start, end)
        return (text,(start, end))


    def get_active_text_in_combobox(self,combobox):
        """
        Given a combobox, return its active text
        """
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None

        return model[active][0]

    ################# Parsers #######################    
    def load_annotated_xml(self,xml_filename):
        """
        Given the name of a xml containing a NCBI abstract,
        with AbstractText annotated by Pubmed Tagger
        Create a Gtk.TextBuffer with the 'marked' abstract, 
        pass it to the interface and tag the mars with
        tag_text function
        """
        tags = {}
        textbuffer = gtk.TextBuffer()
        data = self.get_data_from_ncbi_xml(xml_filename)
        if data:
            annotated_abstract_list = data["article_abstract"]
        else:
            self.show_message("PubMed Tagger was not able to parse %s" %xml_filename)
            return 0

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
                    if pygtk_tag_name in tags.keys():
                        tags[pygtk_tag_name].append((textmark_before, textmark_after))
                    else:
                        tags[pygtk_tag_name] = [(textmark_before, textmark_after)]

                if tail:
                    textbuffer.insert(textbuffer.get_end_iter(),tail)

            if annotated_abstract.tail:
                if not annotated_abstract.tail.isspace():
                    textbuffer.insert(textbuffer.get_end_iter(),\
                                      annotated_abstract.tail)

        print "Tags found: ", tags_found #for debugging
        data["article_abstract"] = textbuffer
        self.update_interface(data, textbuffer=True)       
        self.tag_text(tags)
        print textbuffer.get_text(textbuffer.get_bounds()[0],textbuffer.get_bounds()[1])

    def get_data_from_ncbi_xml(self,filename):
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


    def get_abstract_text_from_etree(self, data):
        abstract = ""
        for abstract_section in data["article_abstract"]:
            if len(abstract) == 0:
                abstract += abstract_section.text
            else:
                abstract += " " + abstract_section.text

        return abstract
        

    ########### Functions for the whole interface ###############
    def update_interface(self, data, textbuffer=False, *args):
        self.clear_interface()
        if textbuffer:
            self._abstract_textview.set_buffer(data["article_abstract"])
        else:
            text = self.get_abstract_text_from_etree(data) 
            self.set_textview_text(self._abstract_textview, text)

        self.set_textview_text(self._title_textview,
                               data["article_title"].text)
        self._pmid_label.set_text(data["pmid"])
        self._journal_label.set_text(data["journal_title"])
        self._year_label.set_text(data["publication_year"])

    def clear_interface(self):
        """
        Clear all labels and textviews
        """
        self.set_textview_text(self._abstract_textview,"")
        self.set_textview_text(self._title_textview,"")
        self._pmid_label.set_text("")
        self._journal_label.set_text("")
        self._year_label.set_text("")

    ############# Tags ##################
    def write_tag_on_textbuffer(self, textbuffer, textMark, opening_tag):
        """
        Check the existance of a TextTag in the given textbuffer at given textMark
        if it is true and is a openning tag, get its name and translate to xml format
        elif it is true and is a closing tag, translate to a closing tag in a xml format
        return the new textbuffer, and the current (or not) closing tag
        **deprecated**
        """
        current_tags = []
        textMark_iter = textbuffer.get_iter_at_mark(textMark)
        if textMark_iter.begins_tag(None) and not opening_tag:
            current_tags = textMark_iter.get_tags()
            opening_tag = current_tags[0].get_property("name")
            tag = '<%s>' %opening_tag
            textbuffer.insert(textMark_iter, tag)

        elif textMark_iter.ends_tag(None) and opening_tag:
            closing_tag = '</%s>' %opening_tag.split("Annotation")[0].strip()
            textbuffer.insert(textMark_iter, closing_tag)
            opening_tag = False

        return textbuffer, opening_tag

    def tag_text(self,tags):
        """
        """
        tags_added = 0
        textbuffer = self._abstract_textview.get_buffer()
        for tag, bounds_list in tags.items():
            for bounds in bounds_list:
                start = textbuffer.get_iter_at_mark(bounds[0])
                end = textbuffer.get_iter_at_mark(bounds[1])
                self.insert_tag(tag, self._abstract_textview, (start,end))
                tags_added +=1
        print "Tags added: ", tags_added  #for debugging

    def insert_tag(self, tag, textview, bounds):
        """
        Given a tag_name, a textview, and a tuple with the bounds of a
        term, tag the term
        """
        textbuffer = textview.get_buffer()
        tagtable = textbuffer.get_tag_table()
        if tagtable.lookup(tag):           
            textbuffer.apply_tag_by_name(tag, bounds[0], bounds[1])       
        else:
            xml_tag_name = tag.split(" ")[0]
            if xml_tag_name in self.tag_colors.keys():
                tag_color = self.tag_colors[xml_tag_name]
                textbuffer.create_tag(tag, background =tag_color)
                textbuffer.apply_tag_by_name(tag, bounds[0], bounds[1])

        
    def remove_tag(self, tag, textview, bounds):
        """
        Given a tag_name, a textview, and a tuple with the bounds of a
        term, remove the specified tag
        """
        textbuffer = textview.get_buffer()
        textbuffer.remove_tag(tag, bounds[0], bounds[1])

    def set_textview_text(self, textview, text):
        textbuffer = textview.get_buffer()
        textbuffer.set_text(text)

    def load_tags(self, *args):
        """
        Load tags described at tags.txt
        """
        self._tags_combo.get_model().clear()
        tags = [x.replace("\n","").split(",") \
                for x in open("tags.txt").readlines()]
        for tag in tags:            
            self._tags_combo.append_text(tag[0].strip())
            self.tag_colors[tag[0].strip()] = tag[1].strip()

        self._tags_combo.set_active(0)

    ######## Internal #########
    def replace_etree_element(self,original, new):
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

    ######## Constructor ########
    def __init__ (self):
        """Pubmed Tagger is an app to make text annotation easier"""
        self.xml_glade= gtk.glade.XML("gui/interface.glade")
        # --- Dicionario com as funcoes callback ---
        funcoes_callback = {
            "on_pmid_button_clicked":self.on_pmid_button_clicked,
            "on_untag_button_clicked": self.on_untag_button_clicked,
            "on_annotation_button_clicked":self.on_annotation_button_clicked,
            "on_save_button_clicked": self.on_save_button_clicked,
            "on_open_button_clicked": self.on_open_button_clicked,
            "on_close_button_clicked": self.close_window,
            "on_reload_tags_button_clicked": self.load_tags,
            "on_copy_clipboard": self.on_copy_clipboard,
            "on_cursor_movement_detected": self.on_cursor_movement_detected,
            "on_filechooser_ok_button_clicked": self.on_filechooser_ok_button_clicked,
            "on_filechooser_cancel_button_clicked": self.on_filechooser_cancel_button_clicked,
            "on_message_ok_button_clicked" : self.on_message_ok_button_clicked
                           }

        self.get_glade_widgets()
        self._main_window.show()
        self.xml_glade.signal_autoconnect(funcoes_callback)
        self._main_window.connect("delete-event", self.close_window)
        self._main_window.connect("delete-event", self.on_message_ok_button_clicked)
        self._current_annotation_entry.modify_base(gtk.STATE_NORMAL, 
                                       gtk.gdk.color_parse("yellow"))
        self.current_open_file = ""
        self.tag_colors = {}
        self.clear_interface()
        self._pmid_entry.set_text("21575226")#Type a valid PMID to download")
        self.load_tags()
        self.active_term_bounds = ()

if __name__ == "__main__":              
    PubMed_Tagger()
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()                  
