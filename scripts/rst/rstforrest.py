##################################################################
# Imports
from constants import LIST_SEP, FIELD_SEP, VALUE_SEP, INT_NID, EXT_NID
from exceptions import RSTBadFormat
from node import RSTNode
from tree import RSTTree
from union_find import UnionFind

##################################################################
# Class
class RSTForrest(object):
    """
    Class for analyzing and processing collections of RST trees.

    Variables:
    roots - set of RST tree roots
    msgid2tree - mapping from message id to the particular (sub-)tree
    msgid2root - mapping from message id to the index of the
                 root of the corresponding RST tree

    Methods:
    parse_tsv - parse lines in tab separated value format
    """

    def __init__(self):
        """
        Class constructor.
        """
        self.roots = set()
        self.msgid2tree = {}
        self.msgid2root = UnionFind()
        self._child2prnt = {}

    def parse_tsv(self, a_line):
        """
        Parse line in tab-separated value format.

        @param a_line - line to be parsed

        @return \c void
        """
        if not a_line:
            return

        fields = a_line.split(FIELD_SEP)
        if fields[0] == EXT_NID:
            prnt_msgid, chld_msgid = fields[1].split(LIST_SEP)
            assert chld_msgid not in self._child2prnt or self._child2prnt[chld_msgid] == prnt_msgid, \
                u"Multiple parents specified for message {:s}".format(chld_msgid)

            # join two messages into a single cluster and remember message id
            # of their common ancestor
            self.msgid2root.union(prnt_msgid, chld_msgid)
            self.roots.add(self.msgid2root[prnt_msgid])
            # update (and if necessary create) trees for parent and child messages
            if prnt_msgid not in self.msgid2tree:
                self.msgid2tree[prnt_msgid] = RSTTree(prnt_msgid)
            if chld_msgid not in self.msgid2tree:
                self.msgid2tree[chld_msgid] = RSTTree(chld_msgid)
            # join parent's tree with that of the child
            prnt_tree = self.msgid2tree[prnt_msgid]
            chld_tree = self.msgid2tree[chld_msgid]
            self._join_trees(prnt_tree, chld_tree, fields[-1].split(VALUE_SEP))
        elif fields[0] == INT_NID:
            msgid = fields[1].split(LIST_SEP)
            if msgid not in self.msgid2tree:
                self.msgid2tree[msgid] = RSTTree(msgid)
            self.msgid2tree[msgid].parse_tsv(line)
        else:
            raise RSTBadFormat(line)

    def __str__(self):
        """TODO: Write decription."""
        raise NotImplementedError

    def __unicode__(self):
        """TODO: Write decription."""
        raise NotImplementedError

    def _join_trees(self, a_prnt_tree, a_chld_tree, a_fields):
        """
        Private method for joining two separate trees into one.

        @param a_prnt_tree - pointer to parent tree
        @param a_chld_tree - pointer to child tree
        @param a_fields - relation specification

        @return \c void
        """
        pass
