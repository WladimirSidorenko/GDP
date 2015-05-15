#!/usr/bin/env python

"""
Script for measuring agreeement on RST corpus.

USAGE:
script_name [OPTIONS] src_dir anno_dir1 anno_dir2
"""

##################################################################
# Libraries
from rst import RSTForrest, FIELD_SEP, TREE_INTERNAL, XML_FMT

from collections import defaultdict, Counter
from itertools import chain
import argparse
import glob
import os
import sys
import xml.etree.ElementTree as ET

##################################################################
# Variables and Constants
ENCODING = "utf-8"

# indices used for copmputing kappa statistics
CONFUSION_IDX = 0
DIFF_IDX = 1
NONE = "none"
SEG = "segment"
NONSEG = "nonsegment"

# auxiliary function used for creating initial statistics list
KAPPA_GEN = lambda: [defaultdict(lambda: Counter()), []] # confusion matrix, list of differences

# statistics dictionaries
KAPPA_STAT = defaultdict(KAPPA_GEN) # total kappa statistics

# constants specifying which RST elements should be tested
SEGMENTS = "segments"
CHCK_SEGMENTS = 1
NUCLEARITY = "nuclearity"
CHCK_NUCLEARITY = 2
RELATIONS = "relations"
CHCK_RELATIONS = 4
ALL = "all"
CHCK_ALL = 7

##################################################################
# Methods
def _merge_stat(a_trg_stat, a_src_stat):
    """
    Update statistics of a_trg_stat with a_src_stat.

    @param a_trg_stat - target statistics to be updated
    @param a_src_stat - target statistics from which to update

    @return void
    """
    confusion1 = confusion2 = stat1 = idic = None
    for key2, stat2 in a_src_stat.iteritems():
        stat1 = a_trg_stat[key2]
        confusion1 = stat1[CONFUSION_IDX]
        confusion2 = stat2[CONFUSION_IDX]
        print >> sys.stderr, "confusion1", repr(confusion1)
        print >> sys.stderr, "confusion2", repr(confusion2)
        for confusion_key2, confusion_stat2 in confusion2.iteritems():
            print >> sys.stderr, "confusion1[confusion_key2]", repr(confusion1[confusion_key2])
            confusion1[confusion_key2].update(confusion_stat2)
        stat1[DIFF_IDX] += stat2[DIFF_IDX]

def _compute_kappa(a_overlap, a_marginals1, a_marginals2, a_total):
    """Compute Cohen's Kappa.

    @param a_overlap - total number of matches between two annotations
    @param a_marginals1  - total number of specific markables in the 1-st annotation
    @param a_marginals2 - total number of specific markables in the 2-nd annotation
    @param a_total - total number of marked objects

    @return float
    """
    assert a_overlap <= sum(a_marginals1.values()), \
        "The numer of matched annotation in the 1-st file exceeds the total number of annotations."
    assert a_overlap <= sum(a_marginals2.values()), \
        "The numer of matched annotation in the 2-nd file exceeds the total number of annotations."
    if a_total == 0.0:
        return 0.0
    # normalize overlap figures
    observed = float(a_overlap) / float(a_total)
    # compute chance agreement
    chance = sum([v * a_marginals2[k] for k, v in a_marginals1.iteritems()]) / float(a_total**2)
    # compute Cohen's Kappa
    if chance < 1.0:
        kappa = (observed - chance) / (1.0 - chance)
    else:
        kappa = 0.0
    assert kappa <= 1.0, "Invalid kappa value: '{:.2f}'".format(kappa)
    return kappa

def output_stat(a_stat = KAPPA_STAT, a_ostream = sys.stderr, a_header = ""):
    """
    Output agreement statistics.

    @param a_stat - dictionary containing agreement statistics
    @param a_ostream - output file stream for statistics
    @param a_header - optional header to print before actual statistics

    @return void
    """
    if a_header:
        print >> a_ostream, a_header

    print >> a_ostream, \
        "{:15s}{:15s}{:15s}{:15s}{:15s}{:15s}".format("Element", "Overlap", "Markables1", \
                                                          "Markables2", "Total", "Kappa")
    confusion_mtx = None
    marginals1 = Counter()
    marginals2 = Counter()
    total = _total = overlap = mrkbl1 = mrkbl2 = 0
    for elname, elstat in a_stat.iteritems():
        confusion_mtx = elstat[CONFUSION_IDX]
        marginals1.clear(); marginals2.clear()
        total = overlap = mrkbl1 = mrkbl2 = 0
        for k, v in confusion_mtx.iteritems():
            overlap += confusion_mtx[k][k]
            # print >> sys.stderr, "k =", repr(k)
            # print >> sys.stderr, "v =", repr(v)
            _total = sum(v.values())
            total += _total
            marginals1[k] = _total
            marginals2.update(v)
        # print >> sys.stderr, "overlap =", overlap
        # print >> sys.stderr, "total =", total
        # print >> sys.stderr, "marginals1 =", repr(marginals1)
        # print >> sys.stderr, "marginals2 =", repr(marginals2)
        kappa = _compute_kappa(overlap, marginals1, marginals2, total)
        print >> a_ostream, "{:15s}{:<15d}{:<15d}{:<15d}{:<15d}{:<15.2%}".format(\
            elname, overlap, sum(marginals1.values()), sum(marginals2.values()), total, kappa)
        if elstat[DIFF_IDX]:
            for d in elstat[DIFF_IDX]:
                print "#\t" + elname
                print d.encode(ENCODING)

def _update_segment_diff(a_diff, a_txt, a_bndr1, a_bndr2):
    """
    Generate difference on segments.

    @param a_diff - list of differences to be updated
    @param a_txt - raw text of the trees
    @param a_bndr1 - set of discourse boundaries from the 1-st annotator
    @param a_bndr2 - set of discourse boundaries from the 2-nd annotator

    @return \c True if difference was generated, False otherwise
    """
    ret = a_msgid + '\t'
    boundaries = [(b, "<1>") for b in a_bndr1 - a_bndr2]
    boundaries += [(b, "<2>") for b in a_bndr2 - a_bndr1]
    if not boundaries:
        return False
    boundaries += [(b, "<>") for b in a_bndr1 & a_bndr2]
    boundaries.sort(key = lambda el: el[0])
    prev_b = 0
    for b, tag in boundaries:
        ret += a_txt[prev_b:b] + tag
        prev_b = b
    ret += a_txt[b:]
    a_diff.append(ret)
    return True

def _update_segment_stat(a_argmnt_stat, a_txt, a_edus1, a_edus2, a_diff = False, \
                             a_strict = False):
    """
    Update agreement statistics about segment boundaries.

    @param a_argmnt_stat - list containing relevant agreement statistics
    @param a_txt - raw text of the trees
    @param a_edus1 - EDUs from the 1-st annotation
    @param a_edus2 - EDUs from the 2-nd annotation
    @param a_diff - generate differences
    @param a_strict - apply strict comparison metric

    @return \c void
    """
    # update number of total and overlapping segments
    bndr1 = set([edu.end for edu in a_edus1])
    bndr2 = set([edu.end for edu in a_edus2])
    print >> sys.stderr, "bndr1 =", repr(bndr1)
    print >> sys.stderr, "bndr2 =", repr(bndr2)

    seg_seg_overlap = len(bndr1 & bndr2)
    total_seg = len(bndr1 | bndr2)

    # update counters of EDU boundaries
    confusion_mtx = a_argmnt_stat[CONFUSION_IDX]
    # print >> sys.stderr, "confusion_mtx[SEG] =", repr(confusion_mtx[SEG])
    # print >> sys.stderr, "confusion_mtx[SEG][NONSEG] =", repr(confusion_mtx[SEG][NONSEG])
    confusion_mtx[SEG][NONSEG] += len(bndr1) - seg_seg_overlap
    confusion_mtx[NONSEG][SEG] += len(bndr2) - seg_seg_overlap
    confusion_mtx[SEG][SEG] += seg_seg_overlap
    # The total number of possible EDU boundaries will depend on the particular
    # scheme.  For strict metric, NONSEG <-> NONSEG is going to be 0.
    if not a_strict:
        confusion_mtx[NONSEG][NONSEG] += len(a_txt.split()) - total_seg
    # if a_diff:
    #     _update_segment_diff(a_argmnt_stat[DIFF_IDX], a_txt, bndr1, bndr2)

def _update_attr_stat(a_argmnt_stat, a_attr, a_subsegs, a_segs2trees1, a_segs2trees2, \
                                a_diff = False):
    """
    Update agreement statistics about relation types between EDUs.

    @param a_argmnt_stat - list containing relevant agreement statistics
    @param a_attr - string representing tree attribute whose agreement should be checked
    @param a_subsegs - set of all possible subsegments
    @param a_segs2trees1 - RST trees from the 1-st annotation
    @param a_segs2trees2 - RST trees from the 2-nd annotation
    @param a_diff - flag specifying whether differences should be generated

    @return \c void

    """
    tree1 = tree2 = None
    attr1 = attr2 = None
    confusion_mtx = a_argmnt_stat[CONFUSION_IDX]
    print >> sys.stderr, "_update_attr_stat: a_attr =", repr(a_attr)
    print >> sys.stderr, "_update_attr_stat: a_subsegs =", repr(a_subsegs)
    print >> sys.stderr, "_update_attr_stat: a_segs2trees1 =", repr(a_segs2trees1)
    print >> sys.stderr, "_update_attr_stat: a_segs2trees2 =", repr(a_segs2trees2)
    for sseg in a_subsegs:
        # print >> sys.stderr, "_update_attr_stat: sseg =", repr(sseg)
        tree1 = a_segs2trees1[sseg]
        tree2 = a_segs2trees2[sseg]
        # print >> sys.stderr, "_update_attr_stat: tree1 =", repr(tree1)
        # print >> sys.stderr, "_update_attr_stat: tree2 =", repr(tree2)
        if not tree1:
            if not tree2:
                confusion_mtx[NONE][NONE] += 1
        elif not tree2:
            confusion_mtx[getattr(tree1, a_attr)][NONE] += 1
        else:
            attr1 = getattr(tree1, a_attr)
            attr2 = getattr(tree2, a_attr)
            confusion_mtx[attr1][attr2] += 1
            if attr1 != attr2 and a_diff:
                a_argmnt_stat[DIFF_IDX].append(tree1.minimal_str(TREE_INTERNAL, a_attr) + \
                                                   "\nvs.\n" + tree2.minimal_str(TREE_INTERNAL, \
                                                                                     a_attr))

def _get_subtrees(a_rsttrees):
    """
    Obtain all subtrees from a given tree.

    @param a_rsttrees - RST trees to obtain subtrees from

    @return list of 2-tuples with tree offsets and subtrees
    """
    ret = []
    for irsttree in a_rsttrees:
        for subtree in irsttree.get_subtrees():
            ret.append(((subtree.t_start, subtree.t_end), subtree))
    return ret

def _get_messages(a_thread, a_messages):
    """
    Populate dictionary of messages

    @param a_thread - XML element representing whole thread
    @param a_messages - dictionary in which to store the thread messages
    """
    for imsg in a_thread.iterfind('msg'):
        a_messages[imsg.get("id")] = imsg.find("text").text.encode(ENCODING).strip()
        for chmsg in imsg.iterfind('msg'):
            _get_messages(chmsg, a_messages)

def _update_stat(a_argmnt_stat, a_rsttrees1, a_rsttrees2, a_msgid, a_txt, a_chck_flags, \
                     a_diff, a_sgm_strict):
    """
    Measure agreement of two RST trees.

    @param a_argmnt_stat - dictionary with agreement statistics to be updated
    @param a_rsttrees1 - RST trees from 1-st annotation
    @param a_rsttrees2 - RST trees from 2-nd annotation
    @param a_msgid - id of the message to be annnotated
    @param a_txt - raw text of the trees
    @param a_chck_flags - flags specifying which elements should be tested
    @param a_diff - flag specifying whether differences should be generated
    @param a_sgm_strict - flag indicating whether segment agreement should
                       apply strict metric

    @return \c void

    """
    edus1 = [edu for rsttree in a_rsttrees1 for edu in rsttree.get_edus()]
    edus2 = [edu for rsttree in a_rsttrees2 for edu in rsttree.get_edus()]
    # estimate agreement on segment boundaries
    if a_chck_flags & CHCK_SEGMENTS:
        _update_segment_stat(a_argmnt_stat[SEGMENTS], a_txt, edus1, edus2, \
                                      a_diff, a_sgm_strict)
    subsegs = []
    # chain(edus1, edus2)
    if a_chck_flags & (CHCK_NUCLEARITY | CHCK_RELATIONS):
        # obtain starts and ends of segments
        starts = list(set([edu.start for edu in chain(edus1, edus2)]))
        starts.sort()
        ends = list(set(edu.end for edu in chain(edus1, edus2)))
        ends.sort()
        # generate all possible subsegments
        j_end = 0
        # for each start position, create a list of tuples with this start
        # position as the first element and all succeeding end positions as the
        # second elements
        for start_i in starts:
            assert start_i >= 0, "Invalid start of RSTTree: {:d}".format(start_i)
            while j_end < len(ends) and ends[j_end] <= start_i:
                j_end += 1
            for end_j in ends[j_end:]:
                assert end_j >= 0, "Invalid start of RSTTree: {:d}".format(end_j)
                subsegs.append((start_i, end_j))
        print >> sys.stderr, "subsegs = ", repr(subsegs)
        segs2trees1 = defaultdict(lambda: None, _get_subtrees(a_rsttrees1))
        segs2trees2 = defaultdict(lambda: None, _get_subtrees(a_rsttrees2))
        print >> sys.stderr, "segs2trees1 = ", repr(segs2trees1)
        print >> sys.stderr, "segs2trees2 = ", repr(segs2trees2)
        sys.exit(66)

        if a_chck_flags & CHCK_NUCLEARITY:
            _update_attr_stat(a_argmnt_stat[NUCLEARITY], "nucleus", subsegs, segs2trees1, \
                                  segs2trees2, a_diff)
        if a_chck_flags & CHCK_RELATIONS:
            _update_attr_stat(a_argmnt_stat[RELATIONS], "relname", subsegs, segs2trees1, \
                                  segs2trees2, a_diff)

def update_stat(a_src_fname, a_anno1_fname, a_anno2_fname, a_chck_flags, a_diff = False, \
                    a_sgm_strict = True, a_file_fmt = XML_FMT, a_verbose = True):
    """
    Measure agreement of two files.

    @param a_src_fname - name of source file with original text
    @param a_anno1_fname - name of the 1-st file containing annotation
    @param a_anno2_fname - name of the 2-nd file containing annotation
    @param a_chck_flags - flags specifying which elements should be tested
    @param a_diff - flag specifying whether differences should be generated
    @param a_sgm_strict - flag indicating whether segment agreement should
                         use strict metric
    @param a_file_fmt - format of annotation file
    @param a_verbose - output statistics for file

    @return \c void

    """
    global KAPPA_STAT
    # read messages
    messages = {}
    srctree = ET.parse(a_src_fname).getroot()
    print >> sys.stderr, "Processing file: '{:s}'".format(a_src_fname)
    for ithread in srctree.iter('thread'):
        _get_messages(ithread, messages)
    # read first annotation file
    rstForrest1 = RSTForrest(a_file_fmt)
    rstForrest1.parse(a_anno1_fname)
    # read second annotation file
    rstForrest2 = RSTForrest(a_file_fmt)
    rstForrest2.parse(a_anno2_fname)
    # perform neccessary agreement tests
    skip = False
    agrmt_stat = defaultdict(KAPPA_GEN)
    for msg_id, msg in messages.iteritems():
        skip = False
        if msg_id not in rstForrest1.msgid2iroots:
            print >> sys.stderr, \
                """WARNING: Message {:s} was not annotated by the 1-st annotator""".format(msg_id)
            skip = True
        if msg_id not in rstForrest2.msgid2iroots:
            print >> sys.stderr, \
                """WARNING: Message {:s} was not annotated by the 2-nd annotator""".format(msg_id)
            skip = True
        if skip:
            continue
        _update_stat(agrmt_stat, rstForrest1.msgid2iroots[msg_id], rstForrest2.msgid2iroots[msg_id], \
                         msg_id, messages[msg_id], a_chck_flags, a_diff, a_sgm_strict)
        # delete both lines
        # output_stat(agrmt_stat, sys.stdout, "Statistics on file {:s}".format(a_src_fname))
        # sys.exit(66)
    if a_verbose:
        output_stat(agrmt_stat, sys.stdout, "Statistics on file {:s}".format(a_src_fname))
    _merge_stat(KAPPA_STAT, agrmt_stat)

def main(argv):
    """
    Main method for measuring agreeement in RST corpus.

    @param argv - command line parameters

    @return \c 0 on SUCCESS non \c 0 otherwise
    """
    global ENCODING
    # define command line arguments
    argparser = argparse.ArgumentParser(description = """Script for measuring corpus agreement
on RST.""")
    # optional arguments
    argparser.add_argument("--anno-sfx", help = "extension of annotation files", type = str,
                         default = "")
    argparser.add_argument("-d", "--output-difference", help = """output difference""",
                         action = "store_true")
    argparser.add_argument("--file-format", help = "format of annotation file", type = str,
                         default = XML_FMT)
    argparser.add_argument("--segment-strict", help = """use strict metric
for evaluating segment agreement""", action = "store_true")
    argparser.add_argument("--src-ptrn", help = "shell pattern of source files", type = str,
                         default = "*")
    argparser.add_argument("--type", help = """type of element (relation) for which
to measure the agreement""", choices = [SEGMENTS, NUCLEARITY, RELATIONS, ALL],
                           type = str, action = "append")
    argparser.add_argument("-v", "--verbose", help = "output agreement statistics for each file", \
                               action = "store_true")
    # mandatory arguments
    argparser.add_argument("src_dir", help = "directory with source files used for annotation")
    argparser.add_argument("anno1_dir", help = "directory with annotation files of first annotator")
    argparser.add_argument("anno2_dir", help = "directory with annotation files of second annotator")
    args = argparser.parse_args(argv)
    # set parameters
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
        chck_flags |= CHCK_ALL

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
        anno1_fnames = glob.glob(os.path.join(args.anno1_dir, \
                                                  src_fname_base + args.anno_sfx))
        if anno1_fnames:
            anno1_fname = anno1_fnames[0]
        if not os.path.isfile(anno1_fname) or not os.access(anno1_fname, os.R_OK):
            continue

        anno2_fname = ""
        anno2_fnames = glob.glob(os.path.join(args.anno2_dir, \
                                                  src_fname_base + args.anno_sfx))
        if anno2_fnames:
            anno2_fname = anno2_fnames[0]
        if not os.path.isfile(anno2_fname) or not os.access(anno2_fname, os.R_OK):
            continue

        # measure agreement for the given annotation files
        update_stat(src_fname, anno1_fname, anno2_fname, chck_flags, args.output_difference, \
                        args.segment_strict, args.file_format, args.verbose)
    output_stat()
    return 0

##################################################################
# Main
if __name__ == "__main__":
    main(sys.argv[1:])
