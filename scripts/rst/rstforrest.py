#!/usr/bin/env python

"""
Module providing RSTForrest class.

Class:
RSTForrest - container class comprising several RST trees

"""

##################################################################
# Imports
from constants import ENCODING, LIST_SEP, FIELD_SEP, VALUE_SEP, \
    TERMINAL, XML_FMT, LSP_FMT, PC3_FMT, _INT_NID, _EXT_NID, \
    _PARENT, _CHILDREN, _RELNAME

from exceptions import RSTBadFormat, RSTBadStructure
from rsttree import RSTTree

from collections import defaultdict

import sys

##################################################################
# Class
class RSTForrest(object):
    """
    Class for analyzing and processing collections of RST trees.

    Variables:
    trees - set of most prominent RST trees
    msgid2iroots - mapping from message id to its corresponding (sub-)tree

    Methods:
    clear - public method for re-setting data
    parse - general method for parsing files

    """

    def __init__(self, a_fmt = XML_FMT):
        """
        Class constructor.

        @param a_fmt - format of input data
        """
        self.trees = set()
        self.msgid2iroots = defaultdict(set)
        # mapping from node id to its corresponding tree
        self._nid2tree = {}
        # mapping from node id to the id of its corresponding message
        self._nid2msgid = {}
        # set appropriate parse function
        if a_fmt == XML_FMT:
            self._parse_func = self._parse_xml
        else:
            raise NotImplementedError

    def __unicode__(self):
        """
        Return unicode representation of given forrest.

        @return unicode representation of the forrest
        """
        return u"\n\n".join([unicode(t) for t in self.trees])

    def __str__(self):
        """
        Return string representation of given forrest.

        @return string representation of the forrest
        """
        return unicode(self).encode(ENCODING)

    def clear(self):
        """
        Public method for re-setting data.

        @return \c void
        """
        self.trees.clear()
        self.msgid2iroots.clear()
        self._nid2tree.clear()
        self._nid2msgid.clear()

    def parse(self, a_file):
        """
        General method for parsing files with RST forrests.

        @param a_file - file to be parsed

        @return \c void
        """
        self._parse_func(a_file)

    def _parse_xml(self, a_file):
        """
        Parse line in tab-separated value format.

        @param a_file - XML file to parse

        @return \c void
        """
        import xml.etree.ElementTree as ET
        idoc = ET.parse(a_file).getroot()
        # read segments and spans
        iid = -1; itree = None
        inodes = [iseg for iseg in idoc.iterfind("segments/segment")] + \
            sorted([ispan for ispan in idoc.iterfind("spans/span")], key = lambda s: s.get("id"))
        for inode in inodes:
            iid = inode.attrib.pop("id")
            inode.attrib["type"] = inode.tag
            # print >> sys.stderr, "_parse_xml: iid =", iid
            # print >> sys.stderr, "_parse_xml: inode.attrib =", repr(inode.attrib)
            itree = RSTTree(iid, **inode.attrib)
            # update offset information
            if not itree._terminal and (itree.external == 0 or itree.etype == "text"):
                itree.t_start = self._nid2tree[itree.start].start
                itree.t_end = self._nid2tree[itree.end].end
            self._nid2tree[iid] = itree
            self._nid2msgid[iid] = itree.msgid
            self.trees.add(itree)
            # print >> sys.stderr, "_parse_xml: itree.msgid =", itree.msgid
            if not itree.external or itree.etype == TERMINAL:
                self.msgid2iroots[itree.msgid].add(itree)
        # read hypotactic relations
        iroots = None
        span_id = nuc_id = sat_id = None
        span_tree = nuc_tree = sat_tree = None
        for irel in idoc.iterfind(".//hypRelation"):
            span_id = irel.find("spannode").get("idref"); span_tree = self._nid2tree[span_id]
            nuc_id = irel.find("nucleus").get("idref"); nuc_tree = self._nid2tree[nuc_id]
            sat_id = irel.find("satellite").get("idref"); sat_tree = self._nid2tree[sat_id]
            # update parent and child information of nucleus and satellite
            nuc_tree.relation = "span"; nuc_tree.parent = span_tree; nuc_tree.nucleus = True
            sat_tree.relation = irel.get("relname"); sat_tree.parent = nuc_tree; sat_tree.nucleus = False
            # update child information of nucleus and span
            nuc_tree.add_children(sat_tree)
            span_tree.add_children(nuc_tree)
            # remove nucleus and satellite from the list of tree roots
            print >> sys.stderr, "_parse_xml: discarding tree ", sat_tree.id
            print >> sys.stderr, "_parse_xml: discarding tree ", nuc_tree.id
            self.trees.discard(sat_tree); self.trees.discard(nuc_tree)
            # remove nucleus and satellite from the list of internal message tree roots
            if nuc_tree.msgid == sat_tree.msgid and nuc_tree.msgid == span_tree.msgid:
                iroots = self.msgid2iroots[nuc_tree.msgid]
                iroots.discard(sat_tree); iroots.discard(nuc_tree)
        # read paratactic relations
        internal = False
        relname = ""
        for irel in idoc.iterfind(".//parRelation"):
            relname = irel.get("relname")
            span_id = irel.find("spannode").get("idref"); span_tree = self._nid2tree[span_id]
            internal = True
            for inuc in irel.iterfind("nucleus"):
                nuc_id = inuc.get("idref"); nuc_tree = self._nid2tree[nuc_id]
                nuc_tree.relation = relname; nuc_tree.parent = span_tree; nuc_tree.nucleus = True
                # update child information of span
                span_tree.add_children(nuc_tree)
                self.trees.discard(nuc_tree)
                # check if the nucleus belongs to the same message
                if nuc_tree.msgid != span_tree.msgid:
                    internal = False
            # remove nucleus and satellite from the list of internal message tree roots
            if internal:
                iroots =  self.msgid2iroots[span_tree.msgid]
                for inuc in irel.iterfind("nucleus"):
                    nuc_id = inuc.get("idref"); nuc_tree = self._nid2tree[nuc_id]
                    iroots.discard(nuc_tree)
