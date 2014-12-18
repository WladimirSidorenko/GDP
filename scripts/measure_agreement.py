#!/usr/bin/env python2.7

"""
Script for measuring agreeement on RST corpus.

USAGE:
script_name [OPTIONS] src_dir anno_dir1 anno_dir2
"""

##################################################################
# Libraries
from rst import RSTForrest, TSV_FMT

import argparse
import glob
import os
import sys

##################################################################
# Variables and Constants
ENCODING = "utf-8"

# indices used for cpmputing kappa statistics
OVERLAP1_IDX = 0
TOTAL1_IDX = 1
OVERLAP2_IDX = 2
TOTAL2_IDX = 3

# constants specifying which RST elements should be tested
SEGMENTS = "segments"
CHCK_SEGMENTS = 1
NUCLEARITY = "nuclearity"
CHCK_NUCLEARITY = 2
RELATIONS = "relations"
CHCK_RELATIONS = 4
ALL = "all"
CHCK_ALL = 7

# auxiliary elements
DUMMY_AGRMT_DIC = {}
ACTIVE_KEYS = set()             # set of elements whose statistics should be computated

# statistics dictionaries
FILE_KAPPA_STAT = {}            # kappa statistics for each file

##################################################################
# Methods
def _read_anno_file(a_anno_fname, a_rst, a_fmt):
    """
    Read annotation file and update corresponding RST forrest.

    @param a_anno_fname - name of the 1-st file containing annotation
    @param a_rst - RST forrest to be populated from the given file
    @param a_fmt - format of input lines

    @return \c void
    """
    print >> sys.stderr, "Processing file '" + a_anno_fname + "'"
    with open(a_anno_fname) as ifile:
        fields = {}
        for line in ifile:
            a_rst.parse_line(line.decode(ENCODING), a_fmt)

def output_agreement(a_kappa_stat = KAPPA_STAT, a_header = "total"):
    """

    """
    pass

def measure_segment_agreement(a_argmnt_stat, a_rsttree1, a_rsttree2):
    """
    Measure agreement of two RST trees on segment boundaries.

    @param a_argmnt_stat - list containing relevant agreement statistics
    @param a_rsttree1 - RST tree from 1-st annotation
    @param a_rsttree2 - RST tree from 1-st annotation

    @return \c void

    """
    pass

def measure_nuclearity_agreement(a_argmnt_stat, a_rsttree1, a_rsttree2):
    """
    Measure agreement of two RST trees on nuclearity status  of EDUs.

    @param a_argmnt_stat - list containing relevant agreement statistics
    @param a_rsttree1 - RST tree from 1-st annotation
    @param a_rsttree2 - RST tree from 1-st annotation

    @return \c void

    """
    pass

def measure_relations_agreement(a_argmnt_stat, a_rsttree1, a_rsttree2):
    """
    Measure agreement of two RST trees on relation types between EDUs.

    @param a_argmnt_stat - list containing relevant agreement statistics
    @param a_rsttree1 - RST tree from 1-st annotation
    @param a_rsttree2 - RST tree from 1-st annotation

    @return \c void

    """
    pass

def _measure_agreement(a_argmnt_stat, a_rsttree1, a_rsttree2, a_chck_flags)
    """
    Measure agreement of two RST trees.

    @param a_argmnt_stat - dictionary with agreement statistics to be updated
    @param a_rsttree1 - RST tree from 1-st annotation
    @param a_rsttree2 - RST tree from 2-nd annotation
    @param a_chck_flags - flags specifying which elements should be tested

    @return \c void

    """
    if a_chck_flags & CHCK_SEGMENTS:
        measure_segment_agreement(a_argmnt_stat[SEGMENTS], a_rsttree1, a_rsttree2)
    if a_chck_flags & CHCK_NUCLEARITY:
        measure_nuclearity_agreement(a_argmnt_stat[NUCLEARITY], a_rsttree1, a_rsttree2)
    if a_chck_flags & CHCK_RELATIONS:
        measure_relations_agreement(a_argmnt_stat[RELATIONS], a_rsttree1, a_rsttree2)

def measure_agreement(a_src_fname, a_anno1_fname, a_anno2_fname, a_chck_flags):
    """
    Measure agreement of two files.

    @param a_src_fname - name of source file with original text
    @param a_anno1_fname - name of the 1-st file containing annotation
    @param a_anno2_fname - name of the 2-nd file containing annotation
    @param a_chck_flags - flags specifying which elements should be tested

    @return \c void

    """
    global FILE_KAPPA_STAT
    # read input file
    messages = {}
    fields = []
    with open(a_src_fname) as ifile:
        for line in ifile:
            line = line.decode(ENCODING).strip()
            if not line:
                continue
            fields = line.split(FIELD_SEP)
            messages[fields[0]] = fields[1]
    # read first annotation file
    rstForrest1 = RSTForrest()
    _read_anno_file(a_anno1_fname, rstForrest1, TSV_FMT)
    # read second annotation file
    rstForrest2 = RSTForrest()
    _read_anno_file(a_anno2_fname, rstForrest2, TSV_FMT)
    # perform neccessary agreement tests
    skip = False
    agrmt_dic = fname2agrmt[a_src_fname] = DUMMY_AGRMT_DIC.copy()
    for k in active_keys:
        agrmt_dic[k] = 0
    for msg_id, msg in messages.iteritems():
        skip = False
        if msg_id not in rstForrest1.msgid2tree:
            print >> sys.stderr, "WARNING: Message {:s} not annotated by 1-st annotator".format(msg_id)
            skip = True
        if msg_id not in rstForrest2.msgid2tree:
            print >> sys.stderr, "WARNING: Message {:s} not annotated by 2-nd annotator".format(msg_id)
            skip = True
        if skip:
            continue
        _measure_agreement(agrmt_dic, rstForrest1.msgid2tree[msg_id], \
                               rstForrest2.msgid2tree[msg_id], a_chck_flags)

def main(argv):
    """
    Main method for measuring agreeement in RST corpus.

    @param argv - command line parameters

    @return \c 0 on SUCCESS non \c 0 otherwise
    """
    global ENCODING, active_keys
    # define command line arguments
    argparser = argparse.ArgumentParser(description = "Script for measuring corpus agreement on RST.")
    # optional arguments
    argparser.add_argument("-e", "--encoding", help = """encoding of input document""",
                         type = str, default = "utf-8")
    argparser.add_argument("--type", help = """type of element (relation) for which to measure
the agreement""", choices = [SEGMENTS, NUCLEARITY, RELATIONS, ALL], type = str, default = ALL, action = "append")
    argparser.add_argument("--src-ptrn", help = "shell pattern of source files", type = str,
                         default = "*")
    argparser.add_argument("--anno-sfx", help = "extension of annotation files", type = str,
                         default = "*")
    argparser.add_argument("--segment-chance", help = "extension of annotation files", action = "store_true")
    # mandatory arguments
    argparser.add_argument("src_dir", help = "directory with source files used for annotation")
    argparser.add_argument("anno1_dir", help = "directory with annotation files for first annotator")
    argparser.add_argument("anno2_dir", help = "directory with annotation files for second annotator")
    args = argparser.parse_args(argv)
    # set parameters
    ENCODING = args.encoding
    chck_flags = 0
    if args.type:
        for itype in set(args.type):
            if itype == SEGMENTS:
                chck_flags |= CHCK_SEGMENTS
            elif itype == NUCLEARITY:
                chck_flags |= CHCK_NUCLEARITY
            elif itype == RELATIONS:
                chck_flags |= CHCK_RELATIONS
            elif itype == ALL:
                chck_flags |= CHCK_ALL
    else:
        chck_flags |= CHCK_ALL # by default, measure agreement on all elements

    # generate active keys for statistics dictionary
    if chck_flags & CHCK_SEGMENTS:
        active_keys.add(SEGMENTS)
    if chck_flags & CHCK_NUCLEARITY:
        active_keys.add(NUCLEARITY)
    if chck_flags & CHCK_RELATIONS:
        active_keys.add(RELATIONS)

    # iterate over each source file in `source` directory and find
    # corresponding annotation files
    anno1_fname = ""
    anno2_fname = ""
    src_fname_base = ""

    for src_fname in glob.iglob(os.path.join(args.src_dir, args.src_ptrn)):
        if not os.path.isfile(src_fname) or not os.access(src_fname, os.R_OK):
            continue
        # check annotation files corresponding to the given source file
        src_fname_base = os.path.splitext(os.path.basename(src_fname))[0]
        anno1_fname = ""
        anno1_fnames = glob.glob(os.path.join(args.anno1_dir, src_fname_base + args.anno_sfx))
        if anno1_fnames:
            anno1_fname = anno1_fnames[0]
        if not os.path.isfile(anno1_fname) or not os.access(anno1_fname, os.R_OK):
            continue

        anno2_fname = ""
        anno2_fnames = glob.glob(os.path.join(args.anno2_dir, src_fname_base + args.anno_sfx))
        if anno2_fnames:
            anno2_fname = anno2_fnames[0]
        if not os.path.isfile(anno2_fname) or not os.access(anno2_fname, os.R_OK):
            continue

        # measure agreement for the given annotation files
        measure_agreement(src_fname, anno1_fname, anno2_fname, chck_flags)
    output_agreement()
    return 0

##################################################################
# Main
if __name__ == "__main__":
    main(sys.argv[1:])
