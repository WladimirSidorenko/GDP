#!/usr/bin/env python2.7

##################################################################
# Libraries
import argparse
import os
import sys

##################################################################
# Variables and Constants
SEGMENTS = "segments"
CHCK_SEGMENTS = 1
NUCLEARITY = "nuclearity"
CHCK_NUCLEARITY = 2
RELATIONS = "relations"
CHCK_RELATIONS = 4

ENCODING = "utf-8"
FIELD_SEP = '\t'
VALUE_SEP = '\034'

KAPPA_STAT = {}
INTNID = "nid"
INTERNAL_RST = {}
EXTNID = "msgs2extnid"
EXTERNAL_RST = {}

##################################################################
# Methods
def _read_anno_file(a_anno_fname, a_chck_flags):
    """
    Read annotation file and return a dictionary of annotation elements.

    @param a_anno_fname - name of the 1-st file containing annotation
    @param a_chck_flags - flags specifying which elements should be checked

    @return \c void
    """
    with open(a_anno_fname) as ifile:
        fields = {}
        for line in ifile:
            line = line.decode(ENCODING)
            if not line:
                continue
            fields = line.split(FIELD_SEP)
            if fields[0] == EXTNID:
                for :
                    pass
            elif fields[0] == INTNID:
                for :
                    pass
            else:
                raise u"Unrecognized line format: {:s}".format(line).encode(ENCODING)

def output_agreement(a_kappa_stat = KAPPA_STAT, a_header = "total"):
    """

    """
    pass

def measure_agreement(a_src_fname, a_anno1_fname, a_anno2_fname, a_chck_flags):
    """
    Measure agreement of two files.

    @param a_src_fname - name of source file with original text
    @param a_anno1_fname - name of the 1-st file containing annotation
    @param a_anno2_fname - name of the 2-nd file containing annotation
    @param a_anno2_fname - name of the 2-nd file containing annotation
    @param a_chck_flags - flags specifying which elements should be checked

    @return \c void
    """
    pass

def main(argv):
    """
    Main method for measuring agreeement in RST corpus.

    @param argv - command line parameters

    @return \c 0 on SUCCESS non \c 0 otherwise
    """
    # define command line arguments
    aparser = argparse.ArgumentParser(description = "Script for measuring corpus agreement on RST.")
    # optional arguments
    aparser.add_argument("--type", help = """type of element (relation) for which to measure
the agreement""", choices = [SEGMENTS, NUCLEARITY, RELATIONS], type = str, action = "append")
    aparser.add_argument("--src-ptrn", help = "shell pattern of source files", type = str,
                         defaul = "*")
    aparser.add_argument("--anno-sfx", help = "extension of annotation files", type = str,
                         defaul = "")
    aparser.add_argument("--segment-chance", help = "extension of annotation files", type = int,
                         defaul = "")
    # mandatory arguments
    aparser.add_argument("src_dir", help = "directory with source files used for annotation")
    aparser.add_argument("anno1_dir", help = "directory with annotation files for first annotator")
    aparser.add_argument("anno2_dir", help = "directory with annotation files for second annotator")
    args = argparser.parse_args(argv)
    # iterate over each source file in `source` directory and find
    # corresponding annotation files
    chck_flags = 0
    if args.type:
        for itype in set(args.type):
            if itype == SEGMENTS:
                chck_flags |= CHCK_SEGMENTS
            elif itype == NUCLEARITY:
                chck_flags |= CHCK_NUCLEARITY
            elif itype == RELATIONS:
                chck_flags |= CHCK_RELATIONS
    else:
        chck_flags |= 7         # by default, measure agreement on all elements

    # process source and annotation files
    anno1_fname = ""
    anno2_fname = ""
    src_fname_base = ""
    for src_fname in glob.iglob(os.path.join(args.src_dir, args.src_ptrn)):
        if not os.path.isfile(src_fname):
            continue
        # check annotation files corresponding to the given source file
        src_fname_base = os.path.splitext(os.path.basename())[0]
        anno1_fname = os.path.join(args.anno1_dir, src_fname_base + args.anno_sfx)
        if not os.path.isfile(anno1_fname) or not os.access(anno1_fname, os.R_OK):
            continue
        anno2_fname = os.path.join(args.anno2_dir, src_fname_base + args.anno_sfx)
        if not os.path.isfile(anno2_fname) or not os.access(anno2_fname, os.R_OK):
            continue
        # measure agreement for the given annotation files
        measure_agreement(src_fname, anno1_fname, anno2_fname, chck_flags)
    output_agreement()
    return 0

##################################################################
# Main
if __name__ == "__main__":
    return main(sys.argv[1:])
