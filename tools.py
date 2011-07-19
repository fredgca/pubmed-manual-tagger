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

def translate_greek2latin(abstract):
    greek2latin = {u"\u03B1": "alpha", u"\u03B2": "beta", u"\u03B3": "gamma",
                   u"\u03B4": "delta", u"\u03BA": "kappa", u"\u03BB": "lambda",
                   u"\u03BB": "mu", u"\u03C3": "sigma"}

    for greek, latin in greek2latin.items():
        abstract = abstract.replace(greek,latin)

    return abstract

