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

from pysqlite2 import dbapi2 as sqlite

class Database:
    def __init__(self, database_file="mesh.db"):
        self.db_connection = sqlite.connect(database_file)
        self.cursor = self.db_connection.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")

    def get_mesh_entries(self):
        mesh_entries = list(self.cursor.execute("select * from mesh_entries_table"))
        mesh_entries = [(x[0].lower(), x[1]) for x in mesh_entries]
        return mesh_entries

    def get_mesh_descriptions(self,ui):
        mesh_annotations = list(self.cursor.execute("select * from mesh_table where ui is ?", (ui,)))
        if mesh_annotations:
            mesh_annotations_list = list(mesh_annotations[0])
            try: 
                annotations = mesh_annotations_list[2].replace("\"","'").replace("&","and")
                if mesh_annotations_list[2].find("MS:") != -1:
                    annotations = annotations[annotations.find("MS:")+4:]
                else:
                    pass

                mesh_annotations_list[2] = annotations

            except: 
                print "\n\n****", mesh_annotations_list
    
            return mesh_annotations_list
        else:
            return ["None","None","None"]

