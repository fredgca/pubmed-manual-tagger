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

import urllib2
import xml.etree.ElementTree as etree

def get_abstract_from_ncbi(pmid, output):
    """
    Given a PMID, an output_filename, download the abstract from NCBI
    database, save and return it
    """
    query = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=%s&retmode=xml&tool=pubmed-manual-tagger_in_development" %pmid
    result = urllib2.urlopen(query).read()        
    output_file = open(output, "w")
    output_file.write(result)
    output_file.close()
    ncbi_xml = etree.parse(output)
    return ncbi_xml

