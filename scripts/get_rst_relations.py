#!/usr/bin/env python

"""
Extract RST relations with a given relation name from the corpus

USAGE:
script_name [OPTIONS] src_dir anno_dir relation_name
"""

##################################################################
# Libraries
from rst import RSTForrest, FIELD_SEP, TREE_EXTERNAL, TREE_INTERNAL, TREE_ALL, XML_FMT

from collections import defaultdict, Counter
from itertools import chain
import argparse
import glob
import os
import sys
import xml.etree.ElementTree as ET

reload(sys)
sys.setdefaultencoding('utf8')

##################################################################
# Variables and Constants
ENCODING = "utf-8"

# indices used for copmputing kappa statistics
CONFUSION_IDX = 0
DIFF_IDX = 1
NONE = "none"
SEG = "segment"
NONSEG = "nonsegment"
NUCLEUS = "nucleus"
SATELLITE = "satellite"
RELNAME = "relname"


##################################################################
# Methods
def _get_subtrees(a_rsttrees):
    """
    Obtain all subtrees from a given tree.

    @param a_rsttrees - RST trees to obtain subtrees from

    @return list of 2-tuples with tree offsets and subtrees
    """
    ret = []
    for irsttree in a_rsttrees:
        for subtree in irsttree.get_subtrees():
            ret.append(((subtree.start, subtree.end), subtree))
    return ret


def _get_messages(a_thread, a_start_id, a_msgid2txt, a_msgid2discid):
    """
    Populate dictionary of messages

    @param a_thread - XML element representing whole thread
    @param a_start_id - serial number to start the numbering of
                        messages from
    @param a_msgid2txt - dictionary in which to store the text of the
                         messages
    @param a_msgid2discid - dictionary for storing mapping from message
                        id's to their serial numbers in the discussions

    @return \c next serial message number to use
    """
    txt = ""
    msgid = None
    for imsg in a_thread.findall('msg'):
        # remember current message
        msgid = imsg.get("id")
        txt = imsg.find("text").text.encode(ENCODING).strip()
        a_msgid2txt[msgid] = txt
        a_msgid2discid[msgid] = a_start_id
        a_start_id += 1
        # recursively process children
        a_start_id = _get_messages(imsg, a_start_id, a_msgid2txt,
                                   a_msgid2discid)
    return a_start_id

# def find_rels(relation, tree, rels):
#     if tree.relname == relation:
#         rels.append(tree.str_min())
#     subtrees = tree.get_subtrees()
#     for st in subtrees:
#         find_rels(relation, st, rels)


def extract_relations(relation_name, src_fname, anno_fname):
    rels = []

    start_id = 0
    messages = {}
    msgid2discid = {}
    print "Processing file: '{:s}'".format(src_fname)
    srctree = ET.parse(src_fname).getroot()
    for ithread in srctree.iter('thread'):
        start_id = _get_messages(ithread, start_id, messages, msgid2discid)
    # read first annotation file
    rstForrest = RSTForrest(XML_FMT, messages, msgid2discid)
    rstForrest.parse(anno_fname)

    nuc = sat = None
    processed_subtrees = set()
    for itree in rstForrest.trees:
        #        find_rels(relation_name,itree,rels)
        subtrees = itree.get_subtrees(a_flag=TREE_ALL)
        for st in subtrees:
            if st in processed_subtrees:
                continue
            processed_subtrees.add(st)
            #print st.relname
            if st.relname == relation_name:
                nuc = st.parent
                sat = st
                rels.append((nuc.str_min(), sat.str_min()))
    return rels


def main(argv):
    """
    Main method for extracting relations from RST corpus.

    @param argv - command line parameters

    @return \c 0 on SUCCESS non \c 0 otherwise
    """
    global ENCODING
    # define command line arguments
    argparser = argparse.ArgumentParser(description = """Extract relations from RST corpus""")
    # mandatory arguments
    argparser.add_argument("src_dir", help = "directory with source files of corpus")
    argparser.add_argument("anno_dir", help = "directory with annotation files of corpus")
    argparser.add_argument("relation_name", help = "relation to be searched for")
    args = argparser.parse_args(argv)

    # iterate over each source file in `source` directory and find
    # corresponding annotation files
    anno1_fname = ""
    src_fname_base = ""
    rels = []

    for src_fname in glob.iglob(os.path.join(args.src_dir, "*.xml")):
        if not os.path.isfile(src_fname) or not os.access(src_fname, os.R_OK):
            continue
        # check annotation files corresponding to the given source file
        src_fname_base = os.path.splitext(os.path.basename(src_fname))[0]
        anno1_fname = ""
        anno1_fnames = glob.glob(os.path.join(args.anno_dir, \
                                                  src_fname_base + ".rst.xml"))
        if anno1_fnames:
            anno1_fname = anno1_fnames[0]
        if not os.path.isfile(anno1_fname) or not os.access(anno1_fname, os.R_OK):
            continue

        # find relations with given name
        rels.extend(extract_relations(args.relation_name, src_fname, anno1_fname))
    with open(args.relation_name + "-twit.txt", "w") as outfile:
        for nuc, sat in rels:
            outfile.write("Nucleus:" + nuc + "\n")
            outfile.write("Sattelite:" + sat + "\n")
            outfile.write("=" * 66 + "\n")
    return 0

##################################################################
# Main
if __name__ == "__main__":
    main(sys.argv[1:])
