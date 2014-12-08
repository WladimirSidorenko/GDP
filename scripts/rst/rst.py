

##################################################################
# Libraries
from union_find import UnionFind

##################################################################
# Constants

##################################################################
# Class RSTForrest
class RSTForrest(object):
    """
    Class for analyzing and processing collections of RST trees.

    Variables:
    roots - set of RST tree roots
    msgid2tree - mapping from message id to the tree index
    msgid2root - mapping from message id to the id of the
                 root of the corresponding RST tree

    Methods:
    parse_tsv - parse tab-separated value line
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
            # update (and if necessary create) trees for parent and child
            if prnt_msgid not in self.msgid2tree:
                self.msgid2tree[prnt_msgid] = RSTTree(prnt_msgid)
            if chld_msgid not in self.msgid2tree:
                self.msgid2tree[chld_msgid] = RSTTree(chld_msgid)
            # join parent's tree with that of the child
            prnt_tree = self.msgid2tree[prnt_msgid]
            chld_tree = self.msgid2tree[chld_msgid]

##################################################################
# Class RSTTree
class RSTTree(object):
    """
    Class for analyzing and processing single RST tree.

    Variables:
    root - varibale pointing to the root of an RST tree
    leaves - container holding terminal nodes of the tree

    Methods:
    """

    def __init__(self):
        """
        Class constructor.

        @param a_line - line with bad formatting
        """
        pass

##################################################################
# Exceptions
class IncorrectStructure(Exception):
    """
    Exception raised when data structure appears to be broken.

    Methods:

    Variables:
    msg - message containing error description
    """

    def __init__(self, a_msg):
        """
        Class constructor.

        @param a_line - line with bad formatting
        """
        self.msg = a_msg

    def __str__(self):
        """
        String representation.

        @return string containing the error message
        """
        return self.__unicode__()

    def __unicode__(self):
        """
        Unicode string representation.

        @return unicode string containing the erro message
        """
        return self.msg.encode("utf-8")

class IncorrectFormat(Exception):
    """
    Exception raised when attempting to parse an incorrect line.

    Methods:

    Variables:
    msg - message containing description of an error
    """

    def __init__(self, a_line):
        """
        Class constructor.

        @param a_line - line with bad formatting
        """
        self.msg = u"Incorrect line format: '{:s}'".format(a_line)

    def __str__(self):
        """
        String representation.

        @return string containing the error message
        """
        return self.__unicode__()

    def __unicode__(self):
        """
        Unicode string representation.

        @return unicode string containing the erro message
        """
        return self.msg.encode("utf-8")
