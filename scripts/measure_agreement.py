#!/usr/bin/env python

"""
Script for measuring agreeement on RST corpus.

USAGE:
script_name [OPTIONS] src_dir anno_dir1 anno_dir2
"""

##################################################################
# Libraries
from rst import RSTForrest, FIELD_SEP, TREE_INTERNAL, TSV_FMT

from collections import defaultdict
import argparse
import glob
import os
import sys

##################################################################
# Variables and Constants
ENCODING = "utf-8"

# indices used for copmputing kappa statistics
OVERLAP_IDX = 0
TOTAL_IDX = 1
MRKBL1_IDX = 2
MRKBL2_IDX = 3
DIFF_IDX = 4

# auxiliary function used for creating initial statistics list
KAPPA_GEN = lambda: [0] * 4 + [[]]

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
def _read_anno_file(a_anno_fname, a_rst, a_fmt):
    """
    Read annotation file and update corresponding RST forrest.

    @param a_anno_fname - name of the 1-st file containing annotation
    @param a_rst - RST forrest to be populated from given file
    @param a_fmt - format of input lines

    @return \c void
    """
    print >> sys.stderr, "Processing file '" + a_anno_fname + "'"
    with open(a_anno_fname) as ifile:
        fields = {}
        for line in ifile:
            print >> sys.stderr, "line =", repr(line)
            line = line.strip()
            a_rst.parse_line(line.decode(ENCODING), a_fmt)

def _merge_stat(a_trg_stat, a_src_stat):
    """
    Update statistics of a_trg_stat with a_src_stat.

    @param a_trg_stat - target statistics dictionary
    @param a_src_stat - target statistics dictionary

    @return void
    """
    idic = None
    for key, val in a_src_stat.iteritems():
        idic = a_trg_stat[key]
        for i, v in enumerate(val):
            idic[i] += v

def _compute_kappa(a_overlap, a_mrkbl1, a_mrkbl2, a_total):
    """Compute Cohen's Kappa.

    @param a_overlap - number of overlapping annotations in the 1-st annotation
    @param a_mrkbl1  - total number of markables in the 1-st annotation
    @param a_mrkbl2 - total number of markables in the 2-nd annotation
    @param a_total - total number of tokens in file

    @return float
    """
    assert a_overlap <= a_mrkbl1, \
        "The numer of matched annotation in the 1-st file exceeds the total number of markables."
    assert a_overlap <= a_mrkbl2, \
        "The numer of matched annotation in the 2-nd file exceeds the total number of markables."
    # compute chance agreement
    if a_total == 0.0:
        return 0.0
    agreement = float(a_total - a_mrkbl1 + a_overlap - a_mrkbl2 + a_overlap) / a_total
    # chances that the first/second annotator randomly annotated a token with
    # that markable
    chance1 = float(a_mrkbl1) / a_total
    chance2 = float(a_mrkbl2) / a_total
    chance = chance1 * chance2 + (1.0 - chance1) * (1.0 - chance2)
    # compute Cohen's Kappa
    if chance < 1.0:
        kappa = (agreement - chance) / (1.0 - chance)
    else:
        kappa = 0.0
    assert kappa <= 1.0, "Invalid kappa value: '{:.2f}'".format(kappa)
    return kappa

def output_stat(a_ostream = sys.stderr, a_stat = KAPPA_STAT, a_header = ""):
    """
    Output agreement statistics.

    @param a_ostream - output file stream for statistics
    @param a_stat - dictionary containing agreement statistics
    @param a_header - optional header to print before actual statistics

    @return void
    """
    if a_header:
        print >> a_ostream, a_header

    print >> a_ostream, \
        "{:15s}{:15s}{:15s}{:15s}{:15s}{:15s}".format("Element", "Overlap", "Markables1", \
                                                          "Markables2", "Total", "Kappa")
    for elname, elstat in a_stat.iteritems():
        overlap = elstat[OVERLAP_IDX]
        mrkbl1 = elstat[MRKBL1_IDX]
        mrkbl2 = elstat[MRKBL2_IDX]
        total = elstat[TOTAL_IDX]
        kappa = _compute_kappa(overlap, mrkbl1, mrkbl2, total)
        print >> a_ostream, "{:15s}{:<15d}{:<15d}{:<15d}{:<15d}{:<15.2%}".format(\
            elname, overlap, mrkbl1, mrkbl2, total, kappa)
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
    # update counters of EDU boundaries
    bndr1 = set([edu.end for edu in a_edus1])
    a_argmnt_stat[MRKBL1_IDX] += len(bndr1)
    bndr2 = set([edu.end for edu in a_edus2])
    a_argmnt_stat[MRKBL2_IDX] += len(bndr2)
    a_argmnt_stat[OVERLAP_IDX] += len(bndr1 & bndr2)
    # the total number of possible EDU boundaries will depend on particular
    # scheme
    if a_strict:
        a_argmnt_stat[TOTAL_IDX] += len(bndr1.union(bndr2))
    else:
        # print >> sys.stderr, "a_txt =", repr(a_txt)
        a_argmnt_stat[TOTAL_IDX] += len(a_txt.split())

    if a_diff:
        _update_segment_diff(a_argmnt_stat[DIFF_IDX], a_txt, bndr1, bndr2)

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
    print >> sys.stderr, "_update_attr_stat: a_attr =", repr(a_attr)
    print >> sys.stderr, "_update_attr_stat: a_subsegs =", repr(a_subsegs)
    print >> sys.stderr, "_update_attr_stat: a_segs2trees1 =", repr(a_segs2trees1)
    print >> sys.stderr, "_update_attr_stat: a_segs2trees2 =", repr(a_segs2trees2)
    a_argmnt_stat[MRKBL1_IDX] += len(a_subsegs)
    a_argmnt_stat[MRKBL2_IDX] += len(a_subsegs)
    a_argmnt_stat[TOTAL_IDX] += len(a_subsegs)
    for sseg in a_subsegs:
        print >> sys.stderr, "_update_attr_stat: sseg =", repr(sseg)
        tree1 = a_segs2trees1[sseg]
        tree2 = a_segs2trees2[sseg]
        print >> sys.stderr, "_update_attr_stat: tree1 =", repr(tree1)
        print >> sys.stderr, "_update_attr_stat: tree2 =", repr(tree2)
        if not tree1:
            if not tree2:
                a_argmnt_stat[OVERLAP_IDX] += 1
        elif not tree2:
            pass
        elif getattr(tree1, a_attr) == getattr(tree2, a_attr):
            print >> sys.stderr, "_update_attr_stat: (sim) tree1.attr =", getattr(tree1, a_attr)
            print >> sys.stderr, "_update_attr_stat: (sim) tree2.attr =", getattr(tree2, a_attr)
            a_argmnt_stat[OVERLAP_IDX] += 1
        else:
            print >> sys.stderr, "_update_attr_stat: (diff) tree1.attr =", getattr(tree1, a_attr)
            print >> sys.stderr, "_update_attr_stat: (diff) tree2.attr =", getattr(tree2, a_attr)
            # the number of these differences will be smaller than
            if a_diff:
                a_argmnt_stat[DIFF_IDX].append(tree1.minimal_str(TREE_INTERNAL, a_attr) + \
                                                   "\nvs.\n" + tree2.minimal_str(TREE_INTERNAL, a_attr))


def _update_stat(a_argmnt_stat, a_rsttree1, a_rsttree2, a_msgid, a_txt, a_chck_flags, \
                     a_diff, a_sgm_strict):
    """
    Measure agreement of two RST trees.

    @param a_argmnt_stat - dictionary with agreement statistics to be updated
    @param a_rsttree1 - RST tree from 1-st annotation
    @param a_rsttree2 - RST tree from 2-nd annotation
    @param a_msgid - id of the message to be annnotated
    @param a_txt - raw text of the trees
    @param a_chck_flags - flags specifying which elements should be tested
    @param a_diff - flag specifying whether differences should be generated
    @param a_sgm_strict - flag indicating whether segment agreement should
                       apply strict metric

    @return \c void

    """
    edus1 = a_rsttree1.get_edus()
    edus2 = a_rsttree2.get_edus()
    if a_chck_flags & CHCK_SEGMENTS:
        _update_segment_stat(a_argmnt_stat[SEGMENTS], a_txt, edus1, edus2, \
                                      a_diff, a_sgm_strict)
    subsegs = []
    if a_chck_flags & (CHCK_NUCLEARITY | CHCK_RELATIONS):
        # obtain starts and ends of segments
        starts = list(set([edu.start for edu in edus1] + [edu.start for edu in edus2]))
        starts.sort()
        ends = list(set([edu.end for edu in edus1] + [edu.end for edu in edus2]))
        ends.sort()
        # generate all possible subsegments
        j_start = 0
        for start_i in starts:
            assert start_i >= 0, "Invalid start of RSTTree: {:d}".format(start_i)
            while j_start < len(ends) and ends[j_start] < start_i:
                j_start += 1
            for end_j in ends[j_start:]:
                assert end_j >= 0, "Invalid start of RSTTree: {:d}".format(end_j)
                subsegs.append((start_i, end_j))
    print >> sys.stderr, "subsegs = ", repr(subsegs)
    segs2trees1 = defaultdict(lambda: None, [((t.start, t.end), t) for t in a_rsttree1.get_subtrees()])
    segs2trees2 = defaultdict(lambda: None, [((t.start, t.end), t) for t in a_rsttree2.get_subtrees()])

    if a_chck_flags & CHCK_NUCLEARITY:
        _update_attr_stat(a_argmnt_stat[NUCLEARITY], "nucleus", subsegs, segs2trees1, segs2trees2, \
                                    a_diff)
    if a_chck_flags & CHCK_RELATIONS:
        _update_attr_stat(a_argmnt_stat[RELATIONS], "relname", subsegs, segs2trees1, segs2trees2, \
                                   a_diff)

def update_stat(a_src_fname, a_anno1_fname, a_anno2_fname, a_chck_flags, a_diff = False, \
                    a_sgm_strict = True, a_file_fmt = TSV_FMT, a_verbose = True):
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
    # read source file
    messages = {}
    fields = []
    with open(a_src_fname) as ifile:
        for line in ifile:
            line = line.decode(ENCODING).strip()
            if not line:
                continue
            fields = line.split(FIELD_SEP)
            assert len(fields) == 2, u"Incorrect format: '{:s}'".format(line).encode(ENCODING)
            messages[fields[0]] = fields[1]
    # read first annotation file
    rstForrest1 = RSTForrest()
    _read_anno_file(a_anno1_fname, rstForrest1, a_file_fmt)
    # read second annotation file
    rstForrest2 = RSTForrest()
    _read_anno_file(a_anno2_fname, rstForrest2, a_file_fmt)
    # perform neccessary agreement tests
    skip = False
    agrmt_stat = defaultdict(KAPPA_GEN)
    for msg_id, msg in messages.iteritems():
        skip = False
        if msg_id not in rstForrest1.msgid2tree:
            print >> sys.stderr, \
                """WARNING: Message {:s} was not annotated by 1-st annotator""".format(msg_id)
            skip = True
        if msg_id not in rstForrest2.msgid2tree:
            print >> sys.stderr, \
                """WARNING: Message {:s} was not annotated by 2-nd annotator""".format(msg_id)
            skip = True
        if skip:
            continue
        _update_stat(agrmt_stat, rstForrest1.msgid2tree[msg_id], rstForrest2.msgid2tree[msg_id], \
                         msg_id, messages[msg_id], a_chck_flags, a_diff, a_sgm_strict)
    if a_verbose:
        output_stat(sys.stdout, agrmt_stat, "Statistics on file {:s}".format(a_src_fname))
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
                         default = "*")
    argparser.add_argument("-d", "--output-difference", help = """output difference""",
                         action = "store_true")
    argparser.add_argument("-e", "--encoding", help = """encoding of input file[s]""",
                         type = str, default = "utf-8")
    argparser.add_argument("--file-format", help = "format of annotation file", type = str,
                         default = TSV_FMT)
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
