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

from pysqlite2 import dbapi2 as sqlite

class Database:
    def __init__(self, database_files={"MESH":"mesh.db", "Cell":"cell.db", 
                                       "Gene":"gene.db", 
                                       "Molecular Roles": "molecular_role.db",
                                       "Mycobacterium_Genes": "mtb_genes.db"}):

        ########################
        ## Creating Databases ##
        ########################
        #MESH database
        self.mesh_db_connection = sqlite.connect(database_files["MESH"])
        self.mesh_cursor = self.mesh_db_connection.cursor()
        self.mesh_cursor.execute("PRAGMA foreign_keys = ON;")

        #Cell database
        self.cell_db_connection = sqlite.connect(database_files["Cell"])
        self.cell_cursor = self.cell_db_connection.cursor()
        self.cell_cursor.execute("PRAGMA foreign_keys = ON;")

        #Gene database
        self.gene_db_connection = sqlite.connect(database_files["Gene"])
        self.gene_cursor = self.gene_db_connection.cursor()
        self.gene_cursor.execute("PRAGMA foreign_keys = ON;")

        #Molecular Role database
        self.molecular_roles_db_connection = sqlite.connect(database_files["Molecular Roles"])
        self.molecular_roles_cursor = self.molecular_roles_db_connection.cursor()
        self.molecular_roles_cursor.execute("PRAGMA foreign_keys = ON;")

        #Mycobacterium Gene database
        self.mtb_db_connection = sqlite.connect(database_files["Mycobacterium_Genes"])
        self.mtb_cursor = self.mtb_db_connection.cursor()
        self.mtb_cursor.execute("PRAGMA foreign_keys = ON;")


    ##########################
    ## Get Entries/Synonyms ##
    ##########################
    def get_mesh_entries(self):
        command = "select * from MESH_Synonyms;"
        try:
            mesh_entries_tmp = list(self.mesh_cursor.execute(command))
        except Exception as inst:
            print inst
            return []
    
        return mesh_entries_tmp


    def get_cell_entries(self):
        command = "select * from Cell_Synonyms;"
        try:
            cell_entries_tmp = list(self.cell_cursor.execute(command))
        except Exception as inst:
            print inst
            return []

        return cell_entries_tmp


    def get_molecular_role_entries(self):
        command = "select * from Molecular_role_Synonyms"
        try:
            roles_entries_tmp = list(self.molecular_roles_cursor.execute(command))                                                                                    
        except Exception as inst:
            print inst
            return []

        return roles_entries_tmp

    def get_mtb_gene_entries(self):
        command = "select * from Mycobacterium_Gene_Synonyms"
        try:                     
            mtb_genes_entries = list(\
                                    self.mtb_cursor.execute(command))                
        except Exception as inst:
            print inst
            return []

        return mtb_genes_entries


    def get_gene_entries(self):
        #command = "SELECT * FROM Gene_Synonyms WHERE (rowid BETWEEN ? AND ?);"
        command = "SELECT * FROM Gene_Synonyms;"
        try:
            #gene_entries = list(self.gene_cursor.execute(command,(start,end)))
            gene_entries = list(self.gene_cursor.execute(command))
        except:
            return []

        return gene_entries


    def get_terms_description(self, tag, terms):
        Ids = terms.keys()
        if tag == "MESH":
            if len(Ids) == 1:
                command = "select * from MESH_Terms where id is ?;"  
                try:
                    mesh_descriptions = list(self.mesh_cursor.execute(command, (Ids[0],)))
                except:
                    mesh_descriptions = []
            else:
                command = "select * from MESH_Terms where id in %s;" %str(tuple(Ids)) 
                try:
                    mesh_descriptions = list(self.mesh_cursor.execute(command))
                except:
                    mesh_descriptions = []

            for mesh_description in mesh_descriptions:
                description = ""
                Id = str(mesh_description[0])
                try: 
                    description = mesh_description[2].replace("\"","'").replace("&","and")
                    if description.find("MS:") != -1:
                        description = description[description.find("MS:")+4:]
                    else:
                        pass
                except Exception as inst: 
                    print inst
                    pass

                for term in terms[Id]:
                    term.description = description
                    term.main_concept = mesh_description[1]
            
            return terms

        elif tag == "Cell":
            if len(Ids) == 1:
                command = "select * from Cells where id is ?;" 
                try:
                    cell_descriptions = list(self.cell_cursor.execute(command, (Ids[0],)))
                except:
                    cell_descriptions = []
            else:
                command = "select * from Cells where id in %s;"  %str(tuple(Ids))
                try:
                    cell_descriptions = list(self.cell_cursor.execute(command))
                except:
                    cell_descriptions = []

            for cell_description in cell_descriptions:
                Id = cell_description[0]
                for term in terms[Id]:
                    term.description = cell_description[2]
                    term.main_concept = cell_description[1]

            return terms
        
        elif tag == "Gene":
            if len(Ids) == 1:
                command = "select * from Genes where id is ?;"  
                try:
                    gene_descriptions = list(self.gene_cursor.execute(command, (Ids[0],)))
                except:
                    gene_descriptions = []
            else:
                command = "select * from Genes where id in %s;"  %str(tuple(Ids))
                try:
                    gene_descriptions = list(self.gene_cursor.execute(command))
                except:
                    gene_descriptions = []

            for gene_description in gene_descriptions:
                Id = str(gene_description[0])
                for term in terms[Id]:
                    term.description = gene_description[3]
                    term.main_concept = gene_description[2]

            return terms

        elif tag == "Molecular_Role":
            if len(Ids) == 1:
                command = "select * from Molecular_roles where id is ?;"
                try: 
                    molecular_role_descriptions = list(self.molecular_roles_cursor.execute(command, (Ids[0],)))
                except:
                    molecular_role_descriptions = []
            else:    
                command = "select * from Molecular_roles where id in %s;" %str(tuple(Ids))
                try: 
                    molecular_role_descriptions = list(self.molecular_roles_cursor.execute(command))
                except:
                    molecular_role_descriptions = []

            for molecular_role_description in molecular_role_descriptions:
                Id = molecular_role_description[0]
                for term in terms[Id]:
                    term.description = molecular_role_description[2]
                    term.main_concept = molecular_role_description[1]

            return terms

        elif tag == "Mtb_Gene":
            if len(Ids) == 1:
                command = "select * from Mycobacterium_Genes where id is ?;"
                try:
                    mtb_genes_descriptions = list(self.mtb_cursor.execute(command, (Ids[0],)))
                except Exception as inst:
                    print inst 
                    mtb_genes_descriptions = []
            else:    
                command = "select * from Mycobacterium_Genes where id in %s;" %str(tuple(Ids))
                try:
                    mtb_genes_descriptions = list(self.mtb_cursor.execute(command))
                except Exception as inst:
                    print inst 
                    mtb_genes_descriptions = []

            for mtb_genes_description in mtb_genes_descriptions:
                Id = mtb_genes_description[0]
                for term in terms[Id]:
                    term.description = mtb_genes_description[2]
                    term.main_concept = mtb_genes_description[1]

            return terms


    ###########################
    ##Get single descriptions##
    ###########################
    def get_mesh_descriptions(self,Id):
        command = "select * from MESH_Terms where id is ?"
        mesh_annotations = list(self.mesh_cursor.execute(command, (Id,)))
        if mesh_annotations:
            mesh_annotations_list = list(mesh_annotations[0])
            try: 
                annotations = mesh_annotations_list[2].replace("\"","'").replace("&","and")
                if mesh_annotations_list[2].find("MS:") != -1:
                    annotations = annotations[annotations.find("MS:")+4:]
                else:
                    pass

                mesh_annotations_list[2] = annotations

            except Exception as inst: 
                print inst, " ??? database line 179"
            return mesh_annotations_list
        else:
            return ["None","None","None"]

    def get_cell_descriptions(self,Id):
        command = "select * from Cells where id is ?"
        try: 
            cell_annotation = list(self.cell_cursor.execute(command, (Id,)))
        except Exception as inst:
            print inst
            cell_annotation =[["None","None","None"]]
    
        return cell_annotation[0]

    def get_gene_descriptions(self,Id):
        command = "select * from Genes where id is ?"
        try:
            gene_annotation = list(self.gene_cursor.execute(command, (Id,)))
        except Exception as inst:
            print inst
            gene_annotation =[["None","None","None"]]
   
        return gene_annotation[0]
        
    def get_molecular_role_descriptions(self,Id):
        command = "select * from Molecular_roles where id is ?"
        try:
            molecular_role_annotations = list(self.molecular_role_cursor.execute(command, (Id,)))
        except Exception as inst:
            print inst
            molecular_role_annotations =[["None","None","None"]]
    
        return molecular_role_annotations[0]

    def get_mtb_gene_descriptions(self,Id):
        command = "select * from Mycobacterium_Genes where id is ?"
        try:
            mtb_genes_annotations = list(self.mtb_cursor.execute(command, (Id,)))
        except Exception as inst:
            print inst
            mtb_genes_annotations =[["None","None","None"]]
    
        return mtb_genes_annotations[0]
    ###########################

