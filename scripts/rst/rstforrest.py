#!/usr/bin/env python2.7

##################################################################
"""
Module providing RSTForrest class.

Class:
RSTForrest - container class comprising several RST trees

"""

##################################################################
# Imports
from constants import LIST_SEP, FIELD_SEP, VALUE_SEP, CHILDREN, \
    ENCODING, INT_NID, EXT_NID, TSV_FMT, LSP_FMT, PC3_FMT

from exceptions import RSTBadFormat, RSTBadStructure
from rsttree import RSTTree

import sys

##################################################################
# Class
class RSTForrest(object):
    """
    Class for analyzing and processing collections of RST trees.

    Variables:
    trees - set of most prominent RST trees
    msgid2tree - mapping from message id to its corresponding (sub-)tree

    Methods:
    parse_line - general method for parsing lines

    """

    def __init__(self):
        """
        Class constructor.
        """
        self.trees = set()
        self.msgid2tree = {}
        # mapping from node id to its corresponding tree
        self._nid2tree = {}
        # mapping from node id to the id of its corresponding message
        self._nid2msgid = {}
        # mapping from message id to the id of external node which spans this
        # message and all its children
        self._msgid2enid = {}
        # mapping from external node id to another external node id (used due
        # to specifics of current RST Tool save implementation)
        self._enid2enid = {}
        # mapping from internal node id to external node id (used due to
        # specifics of current RST Tool save implementation)
        self._inid2enid = {}
        self._inid_line_seen = False

    def __str__(self):
        """
        Return string representation of given forrest.

        @return string representation of the forrest
        """
        return unicode(self).encode(ENCODING)

    def __unicode__(self):
        """
        Return unicode representation of given forrest.

        @return unicode representation of the forrest
        """
        return u"\n\n".join([unicode(t) for t in trees.parents])

    def parse_line(self, a_line, a_fmt = TSV_FMT):
        """
        General method for parsing lines with RST forrests.

        @param a_line - line to be parsed
        @param a_fmt - format of input data

        @return \c void
        """
        if a_fmt == TSV_FMT:
            parse_func = self._parse_tsv
        else:
            raise NotImplementedError
        parse_func(a_line)

    def _parse_tsv(self, a_line):
        """
        Parse line in tab-separated value format.

        @param a_line - line to be parsed

        @return \c void
        """
        if not a_line:
            return
        fields = a_line.split(FIELD_SEP)
        if fields[0] == EXT_NID:
            self._parse_tsv_extnid(fields)
        elif fields[0] == INT_NID:
            self._parse_tsv_intnid(fields)
        else:
            raise RSTBadFormat(line.encode(ENCODING))

    def _parse_tsv_extnid(self, a_fields):
        """
        Private method for parsing TSV line describing external node.

        Example of a line which is supposed to be parsed by this method:
        msgs2extnid	404534340387753985,404541334905950208	50235020span50205022r-question

        @param a_fields - line's tab separated fields

        @return \c void
        """
        assert not self._inid_line_seen, \
            "External node specification should preceed description of internal nodes."

        cmn_tree = chld_tree = None
        cmn_msgid, chld_msgid = a_fields[1].split(LIST_SEP)
        nids = a_fields[-1].split(VALUE_SEP)
        if len(nids) != 6:
            raise RSTBadFormat(\
                "Incorrect specification of external node: {:s}".format(FIELD_SEP.join(a_fields)))
        cmn_root_id, chld_root_id = nids[0], nids[-2]

        if cmn_msgid in self.msgid2tree:
            cmn_tree = self.msgid2tree[cmn_msgid]
        else:
            cmn_tree = self._nid2tree[cmn_root_id] = self.msgid2tree[cmn_msgid] = \
                RSTTree(cmn_root_id, msgid = cmn_msgid)
            self.trees.add(cmn_tree)

        if chld_msgid in self.msgid2tree:
            chld_tree = self.msgid2tree[chld_msgid]
            self.trees.discard(chld_tree)
        else:
            chld_tree = self._nid2tree[chld_root_id] = self.msgid2tree[chld_msgid] = \
                RSTTree(chld_root_id, msgid = chld_msgid)

        self._join_trees(cmn_tree, chld_tree, nids)

    def _join_trees(self, a_cmn_tree, a_chld_tree, a_fields):
        """
        Private method for joining two separate trees into one.

        Example of fields that are supposed to be parsed by this method:
        ["5023", "5020", "span", "5020", "5022", "r-question"]

        @param a_cmn_tree - pointer to common node tree
        @param a_chld_tree - pointer to child tree
        @param a_fields - relation specification

        @return \c void
        """
        cmn_root, prnt_root, cmn_prnt_rel = a_fields[:3]
        prnt_chld_rel = a_fields[-1]
        chld_root = a_chld_tree.id
        prnt_msgid, chld_msgid = a_cmn_tree.msgid, a_chld_tree.msgid

        assert a_chld_tree.parent is None or a_chld_tree.parent == prnt_root, \
            "Message {:s} is linked to multiple parents".format(chld_msgid)
        assert a_chld_tree.relname is None or a_chld_tree.relname == prnt_chld_rel, \
            "Message {:s} is linked to its parent via different relations: {:s} vs {:s}".format(\
            chld_msgid, a_chld_tree.relname, prnt_chld_rel)

        self._nid2msgid[cmn_root] = self._nid2msgid[prnt_root] = prnt_msgid
        self._nid2msgid[chld_root] = chld_msgid

        prnt_tree = None
        if prnt_msgid in self._msgid2enid:
            self._enid2enid[cmn_root] = self._msgid2enid[prnt_msgid]
            assert prnt_root in self._nid2tree, \
                "No tree created for root node {:s} of message {:s}.".format(prnt_root, prnt_msgid)
            prnt_tree = self._nid2tree[prnt_root]
            assert prnt_tree in a_cmn_tree.ichildren, \
                "Common inter-message node has different child nodes: {:s} vs. {:s}.".format(\
                prnt_root, repr(a_cmn_tree.ichildren))
            assert prnt_tree.relname == cmn_prnt_rel, """\
Different relation types specified for common inter-tweet node {:s} and its child node {:s}: {:s} vs. {:s}.\
""".format(cmn_root, prnt_root, prnt_tree.relname, cmn_prnt_rel)
        else:
            # if it's the first time that we see that the parent message has a
            # child message, we have to check if the parent message has
            # already been specified as someone else's child
            self._msgid2enid[prnt_msgid] = cmn_root
            self._inid2enid[prnt_root] = cmn_root

            if a_cmn_tree.id == cmn_root:
                # create a tree for parent node
                prnt_tree = RSTTree(prnt_root, msgid = prnt_msgid, relname = cmn_prnt_rel, \
                                        echildren = set([a_chld_tree]))
                self._nid2tree[prnt_root] = prnt_tree
                a_cmn_tree.ichildren.add(prnt_tree)
            elif a_cmn_tree.id == prnt_root:
                # if we first saw that the parent message was a child to
                # another message, we have to re-link the prent of the root
                # node to the common node
                prnt_tree = a_cmn_tree
                cmn_tree = self.msgid2tree[prnt_msgid] = RSTTree(cmn_root, msgid = prnt_msgid, \
                                                                     ichildren = set([prnt_tree]))
                self._nid2tree[cmn_root] = cmn_tree
                grnd_parent = prnt_tree.parent
                if grnd_parent is not None:
                    cmn_tree.parent = grnd_parent
                    grnd_parent.echildren.discard(prnt_tree)
                    grnd_parent.echildren.add(cmn_tree)
                    cmn_tree.relname = prnt_tree.relname
                prnt_tree.parent = cmn_tree
                prnt_tree.relname = cmn_prnt_rel
            else:
                raise RSTBadStructure("Multiple roots found for message {:s}: {:s} vs. {:s}".format(\
                        prnt_msgid, cmn_root, a_cmn_tree.id))
        a_chld_tree.parent = prnt_tree
        a_chld_tree.relname = prnt_chld_rel
        prnt_tree.add_children(a_chld_tree)

    def _parse_tsv_intnid(self, a_fields):
        """
        Private method for parsing TSV line describing internal node.

        Example of a line which is supposed to be parsed by this method:
        nid	5074	404262465166639104404263018453692416	text73-90	typespan	textwgt915	labelwgt	arrowwgt	spanwgt916	relname	children5070	parent	constituents	visible1	span7390	offsets	xpos355	ypos30	oldindex	newindex	constit	promotion

        @param a_fields - line's fields

        @return \c void
        """
        self._inid_line_seen = True
        # obtain id of the given node
        inid = a_fields[1]
        # create new tree for referenced message ids, if such tree does not
        # exist already
        msgids = a_fields[2].split(VALUE_SEP)
        msgid = msgids[0] if len(msgids) else None
        if len(msgids):
            msgid = msgids[0]
        # convert specified attribute fields to an attribute dictionary
        f = []
        v = None
        attrdic = dict()
        for fld in a_fields[3:]:
            f = fld.split(VALUE_SEP)
            v = [el for el in f[1:] if el != ""]
            if not v:
                continue
            elif len(v) == 1 and f[0] != CHILDREN:
                attrdic[f[0]] = v[0]
            else:
                attrdic[f[0]] = v
        # replace children with their respective trees
        if CHILDREN in attrdic:
            children = set([])
            for ch_id in attrdic[CHILDREN]:
                if ch_id in self._inid2enid:
                    ch_id = self._inid2enid[ch_id]
                if ch_id not in self._nid2tree[ch_id]:
                    self._nid2tree[ch_id] = RSTTree(ch_id)
                children.add(self._nid2tree[ch_id])
            attrdic[CHILDREN] = children
        if len(msgids) == 2:
            # correct parent, if necessary
            if PARENT in attrdic:
                grnd_prnt_id = None
                grnd_prnt_tree = prnt_tree = None
                prnt_id = attrdic[PARENT]
                if prnt_id in self._enid2enid:
                    prnt_id = self._enid2enid[prnt_id]
                elif inid in self._inid2enid and prnt_id != self._inid2enid[inid]:
                    grnd_prnt_id = prnt_id
                    prnt_id = self._inid2enid[inid]
                    assert inid in self._nid2tree, "Root node of discussion message is not present in forrest."
                    assert prnt_id in self._nid2tree, "Abstract root of discussion message is not present in forrest."
                    assert grnd_prnt_id in self._nid2tree, "External parent of discussion message is not present in forrest."
                    prnt_tree = self._nid2tree[prnt_id]
                    grnd_prnt_tree = self._nid2tree[grnd_prnt_id]
                    assert prnt_tree.parent is None or prnt_tree.parent == grnd_prnt_tree, \
                        "Different parents specified for node {:s} ({:s} vs. {:s}).".format( \
                        prnt_tree.id, prnt_tree.parent.id, grnd_prnt_tree.id)
                    assert prnt_tree.relname is None or RELNAME in attrdic and \
                        prnt_tree.relname == attrdic[RELNAME], \
                        "Different parents specified for node {:s} ({:s} vs. {:s}).".format( \
                        prnt_tree.id, prnt_tree.relname, attrdic[RELNAME] if RELNAME in attrdic else "")
                    prnt_tree.parent = grnd_prnt_tree
                    prnt_tree.relname = attrdic.pop(RELNAME, None)
                if prnt_tree is None and prnt_id not in self._nid2tree:
                    prnt_tree = self._nid2tree[prnt_id] = RSTTree(prnt_id)
                else:
                    prnt_tree = self._nid2tree[prnt_id]
                attrdic[PARENT] = prnt_tree
            # if the node connects two messages, then check if its id
            # shouldn't be mapped to something else (TODO: subject to change
            # after changing RSTTool save format)
            if inid in self._enid2enid:
                inid = self._enid2enid[inid]

            if inid not in self._nid2tree:
                self.msgid2tree[msgid] = self._nid2tree[inid] = RSTTree(inid, **attrdic)
            else:
                self._nid2tree[inid].update(**attrdic)
        elif len(msgids) == 1:
            # create tree for the given node, if necessary
            if inid not in self._nid2tree:
                self._nid2tree[inid] = RSTTree(inid, msgid = msgid)
            self._nid2tree[inid].update(**attrdic)
        else:
            raise RSTBadFormat(line)
