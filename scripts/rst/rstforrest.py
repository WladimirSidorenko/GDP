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
from itertools import chain

import sys

##################################################################
# Class
class RSTForrest(object):
    """
    Class for analyzing and processing collections of RST trees.

    Variables:
    trees - set of most prominent RST trees
    msgid2iroots - mapping from message id to its corresponding (sub-)tree
    msgid2discid - dictionary mapping message id to its current number in
               discussions

    Methods:
    clear - public method for re-setting data
    parse - general method for parsing files

    """

    def __init__(self, a_fmt = XML_FMT, a_msgid2discid = None):
        """
        Class constructor.

        @param a_fmt - format of input data
        @param a_msgid2discid - dictionary mapping message id to its current
                        number in discussions

        """
        self.trees = set()
        self.msgid2iroots = defaultdict(set)
        if a_msgid2discid is None:
            self.msgid2discid = defaultdict(lambda: 0)
        else:
            self.msgid2discid = a_msgid2discid
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
        inodes = chain(idoc.iterfind("segments/segment"), idoc.iterfind("spans/span"))
        for inode in inodes:
            iid = inode.attrib.pop("id")
            inode.attrib["type"] = inode.tag
            inode.attrib["discid"] = self.msgid2discid[inode.attrib.get("msgid")]
            # get/create appropriate tree for the given node id
            itree = RSTTree(iid, **inode.attrib)
            self._nid2tree[iid] = itree
            self.trees.add(itree)
            self._nid2msgid[iid] = itree.msgid
            # set `t_start` and `t_end` of terminal nodes
            if itree.terminal:
                itree.start = itree.t_start = (self.msgid2discid[itree.msgid], itree.start)
                itree.end = itree.t_end = (self.msgid2discid[itree.msgid], itree.end)
            else:
                itree.start = itree.end = (-1, -1)
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
            nuc_tree.relname = "span"; nuc_tree.parent = span_tree; nuc_tree.nucleus = True
            sat_tree.relname = irel.get("relname"); sat_tree.parent = nuc_tree; sat_tree.nucleus = False
            # update child information of nucleus and span
            nuc_tree.add_children(sat_tree)
            span_tree.add_children(nuc_tree)
            # remove nucleus and satellite from the list of tree roots
            self.trees.discard(sat_tree); self.trees.discard(nuc_tree)
            # remove nucleus and satellite from the list of internal message tree roots
            if nuc_tree.msgid == span_tree.msgid:
                iroots = self.msgid2iroots[nuc_tree.msgid]
                iroots.discard(sat_tree); iroots.discard(nuc_tree)
        # read paratactic relations
        relname = ""
        internal = False
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
