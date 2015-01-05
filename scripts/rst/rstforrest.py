#!/usr/bin/env python2.7

##################################################################
"""
Module providing RSTForrest class.

Class:
RSTForrest - container class comprising several RST trees

"""

##################################################################
# Imports
from constants import LIST_SEP, FIELD_SEP, VALUE_SEP, \
    ENCODING, INT_NID, EXT_NID, TSV_FMT, LSP_FMT, PC3_FMT

from exceptions import RSTBadFormat, RSTBadStructure
from rstnode import RSTNode
from rsttree import RSTTree
from union_find import UnionFind

import sys

##################################################################
# Class
class RSTForrest(object):
    """
    Class for analyzing and processing collections of RST trees.

    Variables:
    trees - set of RST trees
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
        return u"\n\n".join([unicode(t) for t in trees])

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

        prnt_tree = chld_tree = None
        prnt_msgid, chld_msgid = a_fields[1].split(LIST_SEP)
        nids = a_fields[-1].split(VALUE_SEP)
        if len(nids) != 6:
            raise RSTBadFormat(\
                "Incorrect specification of external node: {:s}".format(FIELD_SEP.join(a_fields)))
        prnt_root_id, chld_root_id = nids[0], nids[-1]

        if prnt_msgid in self.msgid2tree:
            prnt_tree = self.msgid2tree[prnt_msgid]
            self.trees.add(prnt_tree)
        else:
            prnt_tree = self.msgid2tree[prnt_msgid] = RSTTree(prnt_root_id, msgid = prnt_msgid)
            self._nid2tree[prnt_root_id] = prnt_tree

        if chld_msgid in self.msgid2tree:
            chld_tree = self.msgid2tree[chld_msgid]
            self.trees.discard(chld_tree)
        else:
            chld_tree = self.msgid2tree[chld_msgid] = RSTTree(chld_root_id, msgid = chld_msgid)
            self._nid2tree[chld_root_id] = chld_tree

        self._join_trees(prnt_tree, chld_tree, nids)

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
        _, chld_root, prnt_chld_rel = a_fields[3:]
        prnt_msgid, chld_msgid = a_prnt_tree.msg_id, a_chld_tree.msg_id

        assert a_chld_tree.parent is None or a_chld_tree.parent == prnt_root, \
            "Message {:s} is linked to multiple parents".format(chld_msgid)
        assert a_chld_tree.relname is None or a_chld_tree.relname == relname, \
            "Message {:s} is linked to its parent via different relations: {:s} vs {:s}".format(\
            chld_msgid, a_chld_tree.relname, prnt_chld_rel)
        a_chld_tree.parent = prnt_root
        a_chld_tree.relname = prnt_chld_rel

        self._nid2msgid[cmn_root] = self._nid2msgid[prnt_root] = prnt_msgid
        self._nid2msgid[chld_root] = chld_msgid

        if prnt_msgid in self._msgid2enid:
            self._enid2enid[cmn_root] = self._msgid2enid[prnt_msgid]
            assert prnt_root in a_cmn_tree.ichildren, \
                "Common inter-message node has different child nodes: {:s} vs. {:s}.".format(\
                prnt_root, repr(a_cmn_tree.ichildren))
            assert cmn_prnt_rel == a_cmn_tree.relname, """\
Different relation types specified for common inter-tweet node and its child: {:s} vs. {:s}.\
""".format(cmn_prnt_rel, a_cmn_tree.relname)
        else:
            # if it's the first time that we see that the parent message has a
            # child message, we have to check if the parent message has
            # already been specified as someone else's child
            self._msgid2enid[prnt_msgid] = cmn_root
            self._inid2enid[prnt_root] = cmn_root

            if a_cmn_tree.id == cmn_root:
                # create a tree for parent node
                prnt_tree = RSTTree(prnt_root, msgid = prnt_msgid)

                a_cmn_tree.add_child(prnt_root, {"children": set([prnt_root])})
                a_prnt_tree.add_node(prnt_root, {"parent": cmn_root,"relname": cmn_prnt_rel, \
                                                   "children": set([chld_root])})
            elif a_prnt_tree.root == prnt_root:
                a_prnt_tree.root = None
                cmn_node = a_prnt_tree.add_node(cmn_root, {"children": set([prnt_root])})
                # if we first saw that the parent message was a child to
                # another message, we have to re-link the prent of the root
                # node to the common node
                prnt_node = a_prnt_tree.nodes[prnt_root]
                grnd_prnt = prnt_node.parent
                # update parent's parent
                cmn_node.parent = grnd_prnt
                cmn_node.relname = prnt_node.relname
                prnt_node.parent = cmn_root
                prnt_node.relname = cmn_prnt_rel
                # update grand parent's children
                grnd_prnt_msgid = self._nid2msgid[grnd_prnt]
                grnd_prnt_tree = self.msgid2tree[grnd_prnt_msgid]
                grnd_prnt_node = grnd_prnt_tree.nodes[grnd_prnt]
                grnd_prnt_node.children.remove(prnt_root)
                grnd_prnt_node.children.add(cmn_root)
            else:
                raise RSTBadStructure("Multiple roots found for tree {:s} vs. {:s}".format(cmn_root, \
                        a_prnt_tree.root))
        a_prnt_tree.nodes[prnt_root].children.add(chld_root)

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
        msgid = msgids[0]
        for m_id in msgids:
            if m_id not in self.msgid2tree:
                self.msgid2tree[m_id] = RSTTree(m_id)
        # convert specified attribute fields to an attribute dictionary
        f = []
        v = None
        attrdic = dict()
        for fld in a_fields[3:]:
            f = fld.split(VALUE_SEP)
            v = [el for el in f[1:] if el != ""]
            if not v:
                continue
            elif len(v) == 1 and f[0] != "children":
                attrdic[f[0]] = v[0]
            else:
                attrdic[f[0]] = v
        if len(msgids) == 2:
            # if the node connects two messages, then check if its id
            # shouldn't be mapped to something else (TODO: subject to change
            # after changing RSTTool save format)
            if inid in self._enid2enid:
                inid = self._enid2enid[inid]

            if inid not in self.msgid2tree[msgid].nodes:
                self.msgid2tree[msgid].add_node(a_nid = inid, a_attrs = attrdic)
            else:
                self.msgid2tree[msgid].update_node(a_nid = inid, a_attrs = attrdic)
        elif len(msgids) == 1:
            # translate id of the parent
            if "parent" in attrdic and attrdic["parent"]:
                parent = attrdic["parent"]
                if parent in self._enid2enid:
                    attrdic["parent"] = self._enid2enid[parent]
                elif inid in self._inid2enid and parent in self._inid2enid:
                    enid = self._inid2enid[inid]
                    assert inid in self.msgid2tree[msgid].nodes, "Root node with external linkage is not present in tree."
                    inode = self.msgid2tree[msgid].nodes[inid]
                    assert enid in self.msgid2tree[msgid].nodes, "External node is not present in tree."
                    enode = self.msgid2tree[msgid].nodes[enid]
                    assert inode.parent == enid, \
                        "Different parents specified for node {:s} ({:s} vs. {:s}).".format(inid, inode.parent, enid)
                    assert enode.parent == parent, \
                        "Different parents specified for external node {:s} ({:s} vs. {:s}).".format(enid, enode.parent, parent)
                    relname = attrdic.pop("relname", None)
                    assert enode.relname == relname, \
                        "Different relations specified for external node {:s} ({:s} vs. {:s}).".format(enid, enode.relname, relname)
                    attrdic.pop("parent", None)
            # translate id's of the children, if needed
            if "children" in attrdic:
                translated_children = set()
                for chnid in attrdic["children"]:
                    if chnid in self._inid2enid:
                        translated_children.add(self._inid2enid[chnid])
                    else:
                        translated_children.add(chnid)
                attrdic["children"] = translated_children
            if inid not in self.msgid2tree[msgid].nodes:
                self.msgid2tree[msgid].add_node(a_nid = inid, a_attrs = attrdic)
            else:
                self.msgid2tree[msgid].update_node(a_nid = inid, a_attrs = attrdic)
        else:
            raise RSTBadFormat(line)
