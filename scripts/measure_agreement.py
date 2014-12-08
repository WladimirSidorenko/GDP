#!/usr/bin/env python2.7

"""
Script for measuring agreeement of an RST corpus.

USAGE:
script_name [OPTIONS] src_dir anno_dir1 anno_dir2
"""

##################################################################
# Libraries
import argparse
import glob
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

SEGMENTS1 = {}
SEGMENTS2 = {}

##################################################################
# Methods
def _read_anno_file(a_anno_fname, a_chck_flags, a_rst):
    """
    Read annotation file and return a dictionary of annotation elements.

    @param a_anno_fname - name of the 1-st file containing annotation
    @param a_chck_flags - flags specifying which elements should be checked
    @param a_rst - RST tree to be populated from the given file

    @return \c void
    """
    with open(a_anno_fname) as ifile:
        fields = {}
        for line in ifile:
            a_rst.parse_tsv(line.decode(ENCODING))

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
    seg1 = {}
    msg_id = -1
    with open(a_anno1_fname) as ifile:
        for line in ifile:
            line = line.decode(ENCODING).strip()
            if not line:
                continue
            fields = line.split(FIELD_SEP)
            if fields[0] == INTNID and len(fields) > 16 and \
                    fields[4].split(VALUE_SEP)[1] == "text":
                msg_id = fields[2]
                if msg_id not in seg1:
                    seg1[msg_id] = []
                assert fields[15].split(VALUE_SEP)[0] == "offsets", "Wrong index of offset field"
                seg1[msg_id].append([int(v) for v in fields[15].split(VALUE_SEP)[1:]])
    # sort segmentations
    for msg_id in seg1:
        seg1[msg_id].sort(key = lambda el: el[0])
    # read second annotation file
    seg2 = {}
    with open(a_anno2_fname) as ifile:
        for line in ifile:
            line = line.decode(ENCODING).strip()
            if not line:
                continue
            fields = line.split(FIELD_SEP)
            if fields[0] == INTNID and len(fields) > 16 and \
                    fields[4].split(VALUE_SEP)[1] == "text":
                msg_id = fields[2]
                if msg_id not in seg2:
                    seg2[msg_id] = []
                assert fields[15].split(VALUE_SEP)[0] == "offsets", "Wrong index of offset field"
                seg2[msg_id].append([int(v) for v in fields[15].split(VALUE_SEP)[1:]])
    # sort segmentations
    for msg_id in seg2:
        seg2[msg_id].sort(key = lambda el: el[0])
    # compare segmentations
    for msg_id, msg in messages.iteritems():
        if (msg_id in seg1 and msg_id in seg2) or \
            (msg_id not in seg1 and msg_id not in seg2):
            print >> sys.stderr, "WARNING: Message {:s} segmented by only one annotator".format(msg_id)

        if msg_id not in seg1 or msg_id not in seg2:
            continue

        # check if both segmentations are equal
        if len(seg1[msg_id]) == len(seg2[msg_id]):
            for ((start1, end1),(start2, end2)) in zip(seg1[msg_id], seg2[msg_id]):
                if msg[start1:end1].strip() != msg[start2:end2].strip():
                    break
            else:
                continue

        print u"{:s}\t{:s}".format(msg_id, msg).encode(ENCODING)
        seg_start = seg_end = 0
        # print first segmentation
        for seg_start, seg_end in seg1[msg_id]:
            print u"{:s}<>".format(msg[seg_start:seg_end]).encode(ENCODING),
        print u"\n"
        # print second segmentation
        for seg_start, seg_end in seg2[msg_id]:
            print u"{:s}<>".format(msg[seg_start:seg_end]).encode(ENCODING),
        print u"\n"

def main(argv):
    """
    Main method for measuring agreeement in RST corpus.

    @param argv - command line parameters

    @return \c 0 on SUCCESS non \c 0 otherwise
    """
    global ENCODING
    # define command line arguments
    argparser = argparse.ArgumentParser(description = "Script for measuring corpus agreement on RST.")
    # optional arguments
    argparser.add_argument("-e", "--encoding", help = """encoding of input document""",
                         type = str, default = "utf-8")
    argparser.add_argument("--type", help = """type of element (relation) for which to measure
the agreement""", choices = [SEGMENTS, NUCLEARITY, RELATIONS], type = str, action = "append")
    argparser.add_argument("--src-ptrn", help = "shell pattern of source files", type = str,
                         default = "*")
    argparser.add_argument("--anno-sfx", help = "extension of annotation files", type = str,
                         default = "")
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
    else:
        chck_flags |= 7         # by default, measure agreement on all elements

    # iterate over each source file in `source` directory and find
    # corresponding annotation files
    anno1_fname = ""
    anno2_fname = ""
    src_fname_base = ""
    for src_fname in glob.iglob(os.path.join(args.src_dir, args.src_ptrn)):
        if not os.path.isfile(src_fname):
            continue
        # check annotation files corresponding to the given source file
        src_fname_base = os.path.splitext(os.path.basename(src_fname))[0]
        anno1_fname = glob.glob(os.path.join(args.anno1_dir, src_fname_base + args.anno_sfx) + \
                                    args.anno_sfx)[0]
        if not os.path.isfile(anno1_fname) or not os.access(anno1_fname, os.R_OK):
            continue
        anno2_fname = glob.glob(os.path.join(args.anno2_dir, src_fname_base + args.anno_sfx) + \
                                    args.anno_sfx)[0]
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
