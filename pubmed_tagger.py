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
import xml_tools, entrez, tools
from term import Term, Term_Hunter
from database import Database
##for debugging
from xml.etree.ElementTree import dump #debuging
import time#, os,sys #debuging

class PubMed_Tagger:
    def get_glade_widgets(self):
        """
        Load all widgets from the glade xml file that are listed at 'widget_names'
        """
        widget_names = ["main_window", "abstract_textview","title_textview",   #main_window
                        "annotation_entry", "pmid_entry", "active_term_entry", #main_window
                        "current_annotation_entry","preprocess_checkbutton",   #main_window 
                        "pmid_button","annotate_button", "untag_button",       #main_window
                        "reload_tags_button", "tags_combo",                    #main_window
                        "pmid_label", "journal_label", "year_label",           #main_window
                        "save_button", "open_button",                          #main_window
                        "annotation_window_button",                            #main_window
                        "filechooser_window", "filechooser_ok_button",         #filechooser_window
                        "filechooser_cancel_button",                           #filechooser_window
                        "message_window", "message_label", "message_ok_button",#message_Window
                        "annotation_erase_button", "annotation_treeview"       #annotation_window
                        ]

        for widget_name in widget_names:
            setattr(self, "_" + widget_name, self.xml_glade.get_widget(widget_name))

    ###### Interface events ###########

    def close_main_window(self, *args):
        "Close the Pubmed Tagger"
        gtk.main_quit()

    def close_message_window(self, *args):
        "Close the message_window"
        self._message_window.hide()
        return 1

    def show_message(self,message):
        self._message_label.set_text(message)
        self._message_window.show()

    def show_annotation_window(self,*args):
        self._annotation_window.show()
        
    def on_filechooser_ok_button_clicked(self, *args):
        """
        Get the active filename in the filechooser_window and 
        load its data using xml_tools.load_annotated_xml function
        """
        self._filechooser_window.hide()
        filename = self._filechooser_window.get_filename()
        self.current_open_file = filename
        data,tags = xml_tools.load_annotated_xml(filename)
        if not data:
           self.show_message("PubMed Tagger was not able to parse %s" %filename)
           return 0

        self._update_interface(data, textbuffer=True)       
        self.update_annotation_liststore(tags)
        self.tag_text(tags)

    def close_filechooser_window(self, *args):
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
        #TODO: this method could be better organized
        pmid = self._pmid_entry.get_text()
        pre_process = self._preprocess_checkbutton.get_active()
        #Check if the input has a valid PMID
        try:
            int(pmid)
        except:
            self.show_message("Ops! Check if you provided a valid PMID")
            return 0

        self.current_open_file = pmid + ".xml"
        raw_ncbi_xml= entrez.get_abstract_from_ncbi(pmid, self.current_open_file)
        data = xml_tools.get_data_from_ncbi_xml(self.current_open_file)

        #just display the raw abstract, withou any preprocessing
        if data and not pre_process:
            self._clear_interface() 
            self._update_interface(data)

        #automaticaly recognize MESH terms and display the annotated abstract
        elif data and pre_process:
            self.show_message("This can take a few seconds. Do not close the program")           
            #get mesh terms from database
            abstract_text = xml_tools.get_abstract_text_from_etree(data)
            abstract_text = tools.translate_greek2latin(abstract_text)

            #recognize MESH terms automatically
            annotated_filename = "annotated_" + self.current_open_file
            self.current_open_file = annotated_filename
            self.create_annotated_abstract_xml(raw_ncbi_xml,
                                               abstract_text, 
                                               annotated_filename)
            #load annotated xml          
            data,tags = xml_tools.load_annotated_xml(annotated_filename)

            if not data:
               self.show_message("PubMed Tagger was not able to parse %s" %annotated_filename)
               return 0

            self._clear_interface() 
            self._update_interface(data, textbuffer=True)       
            self.tag_text(tags)
            self.update_annotation_liststore(tags)



    def on_untag_button_clicked(self, *args):
        try:
            x_iter,y_iter = self.active_term_bounds
            x = x_iter.get_offset()
        except:
            self.show_message("No annotated term selected")
            return 0

        self._remove_tag_from_annotation_treeview(x)
        tags = x_iter.get_tags()
        for tag in tags:
            #removig tag from the textbuffer
            self.remove_tag(tag, self._abstract_textview, (x_iter, y_iter))
        

    def on_save_button_clicked(self, *args):
        textbuffer = self._abstract_textview.get_buffer()
        start,end = textbuffer.get_bounds()
        #if there is no text on abstract_textview,
        #cancel saving and emit warning
        if len(textbuffer.get_text(start,end)) == 0:
            self.show_message("There is no text to be saved")
            return
        xml_tools.save_annotated_abstract(self.current_open_file, textbuffer)


    def on_annotation_button_clicked(self, *args):
        attribute_name = self.get_active_text_in_combobox(self._tags_combo)
        attribute_value = self._annotation_entry.get_text() #MESH number if TAG is MESH
        text = self._active_term_entry.get_text().strip()
        if not text:
            self.show_message("There is no selected term to tag")
            return 0

        if attribute_value:
            pygtk_tag = str(attribute_name + ' Annotation="' + attribute_value + '"')
            self.insert_tag(pygtk_tag, self._abstract_textview, self.active_term_bounds)
            x,y = self.active_term_bounds           
            Id, heading, ann = self.db.get_mesh_descriptions(attribute_value)
            self.annotation_liststore.append([text, x.get_offset(), 
                                              y.get_offset(),attribute_name, 
                                              attribute_value,
                                              heading, ann])            

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

    ########### Functions for the Annotation Treeview #############
    def update_annotation_liststore(self, tags):
        self.annotation_liststore.clear()
        textbuffer = self._abstract_textview.get_buffer() 
        #TODO: Parallel this work
        descriptions = {"MESH":{},"Cell":{}, "Gene":{}, "Molecular_Role":{}} 
        #these loops feed the description dictionary
        #each key, recieve a dictionary as value
        #this values is like {"id":[term1,term2]}
        for tag, bounds in tags.items():
            for bound in bounds:
                #getting terms informations
                term_start_iter = textbuffer.get_iter_at_mark(bound[0])
                term_end_iter = textbuffer.get_iter_at_mark(bound[1])
                text = textbuffer.get_text(term_start_iter,term_end_iter)
                start = term_start_iter.get_offset()
                end = term_end_iter.get_offset()
                term_ids = tag.split("=")[1].replace("\"", "").split("|")
                tag_name = tag.split("Annotation")[0].strip()
                for term_id in term_ids: 
                    if term_id in descriptions[tag_name].keys():
                        descriptions[tag_name][term_id].append(Term(text,start,end,term_id,tag_name))
                    else:
                        descriptions[tag_name][term_id] = [Term(text,start,end,term_id,tag_name)]

        #Given the descriptions dictionary, get the terms annotations 
        for tag, terms_dict in descriptions.items():
            annotated_terms = self.db.get_terms_description(tag, terms_dict)            
            for term in annotated_terms.values():
                for term_position in term:
                    data = (term_position.term, term_position.start, 
                            term_position.end, term_position.tag, 
                            term_position.id, term_position.main_concept, 
                            term_position.description)

                    self.annotation_liststore.append(data)

  
    def on_annotation_erase_button_clicked(self, *args):
        model, selections = self._annotation_treeview.get_selection().get_selected_rows()
        iters = [model.get_iter(selection) for selection in selections]
        tags = []
        for path in iters:
            tags.append((model.get_value(path, 1),
                         model.get_value(path, 2),
                         model.get_value(path, 3),
                         model.get_value(path, 4)))

            model.remove(path)

        textbuffer = self._abstract_textview.get_buffer()
        for tag in tags:
            tag_name = '%s Annotation="%s"' % (str(tag[2]),str(tag[3]))
            start =  textbuffer.get_iter_at_offset(tag[0])
            end = textbuffer.get_iter_at_offset(tag[1])
            textbuffer.remove_tag_by_name(tag_name, start, end)

    def _remove_tag_from_annotation_treeview(self,x):
        self._annotation_treeview.get_selection().select_all()
        model, selections = self._annotation_treeview.get_selection().get_selected_rows()
        iters = [model.get_iter(selection) for selection in selections]
        lines = []
        for path in iters:
            if model.get_value(path, 1) == x:
                model.remove(path)
            else:
                pass
        self._annotation_treeview.get_selection().unselect_all()


    ############# AbstractTextView Functions ##################
    #**Erasing tags**##
    def remove_tag(self, tag, textview, bounds):
        """
        Given a tag_name, a textview, and a tuple with the bounds of a
        term, remove the specified tag
        """
        textbuffer = textview.get_buffer()
        textbuffer.remove_tag(tag, bounds[0], bounds[1])
        self._remove_tag_from_annotation_treeview(bounds[0].get_offset())


    #**Inserting Tags**##
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

        print "Number of tags added (textbuffer): ", tags_added  #for debugging
        
    #**Loading tags**#       
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
    def _set_textview_text(self, textview, text):
        textbuffer = textview.get_buffer()
        textbuffer.set_text(text)


    def _compare_tags(self,model,i1,i2):
        """
        This functions is designed to sort the annotation_treeview
        """
        if model.get_value(i1,1) == model.get_value(i1,1):
            data1 = model.get_value(i1,2)
            data2 = model.get_value(i2,2)
        else:
            data1 = model.get_value(i1,1)
            data2 = model.get_value(i2,1)

        return cmp(data1, data2)    


    def _update_interface(self, data, textbuffer=False, *args):
        self._clear_interface()
        if textbuffer:
            self._abstract_textview.set_buffer(data["article_abstract"])
        else:
            text = xml_tools.get_abstract_text_from_etree(data) 
            self._set_textview_text(self._abstract_textview, text)

        self._set_textview_text(self._title_textview,
                               data["article_title"].text)
        self._pmid_label.set_text(data["pmid"])
        self._journal_label.set_text(data["journal_title"])
        self._year_label.set_text(data["publication_year"])

    def _clear_interface(self):
        """
        Clear all labels and textviews
        """
        self._set_textview_text(self._abstract_textview,"")
        self._set_textview_text(self._title_textview,"")
        self._pmid_label.set_text("")
        self._journal_label.set_text("")
        self._year_label.set_text("")


    def create_annotated_abstract_xml(self,ncbi_xml, abstract, annotated_filename):
        """Recieves:
           - Abstract from Pubmed in xml format (ncbi_xml),
           - The abstract itself as string (abstract), - TODO: Check is str
           - A name for the file where the annotated xml should be saved.    
           Do:
           - Recognize terms in the abstract and save it as a xml in pubmed format
        """  
        timei = time.time() #for code optimization 
        found_terms = []
        #recognizing Cell_Terms
        cell_terms = self.db.get_cell_entries()
        if cell_terms:
            cell_term_hunter = Term_Hunter(abstract, "Cell")        
            found_terms += cell_term_hunter.recognize_terms(cell_terms)
        print "Cells: ", time.time() - timei
        #Recognizing Molecular Role Terms
        molecular_role_terms = self.db.get_molecular_role_entries()
        if molecular_role_terms:
            molecular_role_term_hunter = Term_Hunter(abstract, "Molecular_Role")        
            found_terms += molecular_role_term_hunter.recognize_terms(molecular_role_terms)
        print "Molecular role: ", time.time() - timei
        #recognizing Genes_Terms
        gene_terms = self.db.get_gene_entries()#first_rowid, last_rowid)
        if gene_terms:
            gene_term_hunter = Term_Hunter(abstract, "Gene") 
            found_terms += gene_term_hunter.recognize_terms(gene_terms)
        print "Genes: ", time.time() - timei
        """
        gene_synonyms_number = 347940 
        first_rowid = 1
        last_rowid = 100000
        while last_rowid <= gene_synonyms_number:           
            partial_gene_terms = self.db.get_gene_entries(first_rowid, last_rowid)
            found_terms += gene_term_hunter.recognize_terms(partial_gene_terms)
            del(partial_gene_terms)#releasing memory
            gc.collect()
            first_rowid = last_rowid +1
            if last_rowid < gene_synonyms_number + 100000:
                last_rowid  += 100000
            else:
                last_rowid = gene_synonyms_number
        """
        #recognizing MESH_Terms
        mesh_terms = self.db.get_mesh_entries()            
        if mesh_terms:
            mesh_term_hunter = Term_Hunter(abstract, "MESH")
            found_terms += mesh_term_hunter.recognize_terms(mesh_terms)
        print "MESH: ", time.time() - timei
        filtered_found_terms = mesh_term_hunter.filter_terms(found_terms)        
        print "Getting and recognizing terms all databases took (secs): ", time.time() - timei

        xml_annotated_abstract = xml_tools.abstract2xml(abstract, filtered_found_terms)        
        xml_tools.replace_etree_element(ncbi_xml.findall(".//Abstract")[0], 
                                        xml_annotated_abstract)
        #print "The resulting XML: \n", dump(xml_annotated_abstract)        
        ncbi_xml.write(annotated_filename)
        print "Finished: ", time.time() - timei

    ######## Constructor ########
    def __init__ (self):
        """Pubmed Tagger is an app to make text annotation easier"""
        #threading.Thread.__init__(self)    
        self.xml_glade= gtk.glade.XML("gui/interface.glade")
        # --- Dicionario com as funcoes callback ---
        funcoes_callback = {
            "on_pmid_button_clicked":self.on_pmid_button_clicked,
            "on_untag_button_clicked": self.on_untag_button_clicked,
            "on_annotation_button_clicked":self.on_annotation_button_clicked,
            "on_save_button_clicked": self.on_save_button_clicked,
            "on_open_button_clicked": self.on_open_button_clicked,
            "on_close_button_clicked": self.close_main_window,
            "on_reload_tags_button_clicked": self.load_tags,
            "on_copy_clipboard": self.on_copy_clipboard,
            "on_cursor_movement_detected": self.on_cursor_movement_detected,
            "on_filechooser_ok_button_clicked": self.on_filechooser_ok_button_clicked,
            "on_filechooser_cancel_button_clicked": self.close_filechooser_window,
            "on_message_ok_button_clicked" : self.close_message_window,
            "on_annotation_erase_button_clicked": self.on_annotation_erase_button_clicked,
                           }

        self.get_glade_widgets()
        self._main_window.show()
        self.xml_glade.signal_autoconnect(funcoes_callback)
        self._main_window.connect("delete-event", self.close_main_window)
        self._message_window.connect("delete-event", self.close_message_window)

        self._current_annotation_entry.modify_base(gtk.STATE_NORMAL, 
                                       gtk.gdk.color_parse("yellow"))
        #Setting treeview and liststore
        self._annotation_treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.annotation_liststore = gtk.ListStore(str,int,int,str,str, str,str)
        self.annotation_liststore.set_sort_func(1, self._compare_tags)
        self.annotation_liststore.set_sort_column_id(1,gtk.SORT_ASCENDING)
        self._annotation_treeview.set_model(self.annotation_liststore)
        ##Creating treeview columns, cellrenderer and packing them
        self.term_column = gtk.TreeViewColumn('Term')
        self.term_cell = gtk.CellRendererText()
        self.term_column.pack_start(self.term_cell, True)
        self.term_column.set_attributes(self.term_cell,markup=0)

        self.start_column = gtk.TreeViewColumn('Start')
        self.start_cell = gtk.CellRendererText()
        self.start_column.pack_start(self.start_cell, True)
        self.start_column.set_attributes(self.start_cell,markup=1)

        self.end_column = gtk.TreeViewColumn('End')
        self.end_cell = gtk.CellRendererText()
        self.end_column.pack_start(self.end_cell, True)
        self.end_column.set_attributes(self.end_cell,markup=2)

        self.tag_column = gtk.TreeViewColumn('Tag')
        self.tag_cell = gtk.CellRendererText()
        self.tag_column.pack_start(self.tag_cell, True)
        self.tag_column.set_attributes(self.tag_cell,markup=3)

        self.term_id_column = gtk.TreeViewColumn('Term ID')
        self.term_id_cell = gtk.CellRendererText()
        self.term_id_column.pack_start(self.term_id_cell, True)
        self.term_id_column.set_attributes(self.term_id_cell,markup=4)

        self.heading_column = gtk.TreeViewColumn('Heading')
        self.heading_cell = gtk.CellRendererText()
        self.heading_column.pack_start(self.heading_cell, True)
        self.heading_column.set_attributes(self.heading_cell,markup=5)

        self.annotation_column = gtk.TreeViewColumn('Annotation')
        self.annotation_cell = gtk.CellRendererText()
        self.annotation_column.pack_start(self.annotation_cell, True)
        self.annotation_column.set_attributes(self.annotation_cell,markup=6)

        ##Appending treeview columns
        self._annotation_treeview.append_column(self.term_column)
        self._annotation_treeview.append_column(self.start_column)
        self._annotation_treeview.append_column(self.end_column)
        self._annotation_treeview.append_column(self.tag_column)
        self._annotation_treeview.append_column(self.term_id_column)
        self._annotation_treeview.append_column(self.heading_column)
        self._annotation_treeview.append_column(self.annotation_column)

        self.current_open_file = ""
        self.tag_colors = {}
        self._clear_interface()
        self._pmid_entry.set_text("21720558")#Type a valid PMID to download")
        self.load_tags()
        self.active_term_bounds = ()
        self.db = Database()
        

if __name__ == "__main__":              
    PubMed_Tagger()
    gtk.main()

