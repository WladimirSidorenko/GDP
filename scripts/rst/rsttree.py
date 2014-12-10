##################################################################
# Imports
from constants import LIST_SEP, FIELD_SEP, VALUE_SEP, \
    EXT_NID, INT_NID, TSV_FMT, LSP_FMT, PC3_FMT
from exceptions import RSTBadFormat, RSTBadStructure
from rstnode import RSTNode

import bisect

##################################################################
# Class
class RSTTree(object):
    """
    Class for analyzing and processing single RST tree.

    Instance Variables:
    extnodes - dictionary, mapping internal node id's to RSTNode's
    intnodes - dictionary, mapping internal node id's to RSTNode's
    leaves - id's of nodes which are terminals in given tree
    msg_id - id of the message to which this tree belongs
    root - index of the root node of the given tree

    Methods:
    add_node - add new node to RST tree
    update_node - update information about given node in the tree
    """

    def __init__(self, a_msg_id = None):
        """
        Class constructor.

        @param a_msg_id - line with bad formatting
        """
        self.msg_id = a_msg_id
        self.intnodes = {}
        self.extnodes = {}
        self.leaves = []
        self.root = None

    def add_node(self, a_nid, a_attrs = {}):
        """
        Add new node to the tree.

        @param a_nid - id of new given node
        @param a_attrs - attributes of new given node

        @return \c void
        """
        if a_nid in self.intnodes:
            raise RSTBadFormat(u"Node {:s} already exists.".format(a_nid))
        inode = self.intnodes[a_nid] = RSTNode(a_nid)
        self.update_node(a_nid, a_attrs)

    def update_node(self, a_nid, a_attrs):
        """
        Update information about the given node.

        @param a_nid - id of the node to be updated
        @param a_attrs - new attributes of the node

        @return \c void
        """
        inode = self.intnodes[a_nid]
        inode.update(a_attrs)
        if inode.parent != None:
            if self.root != None:
                raise RSTBadStructure(u"Multiple roots found in tree (cf. nid {:s})".format(a_nid))
            else:
                self.root = a_nid
        if inode.type == "text":
            # leaves should keep the relative order of their segments
            bisect.insort(self.leaves, inode)

    def __str__(self, a_fmt = TSV_FMT):
        """Produce string representation of given tree.

        @param a_fmt - output format

        @return string representing given tree
        """
        raise NotImplementedError

    def __unicode__(self, a_fmt = TSV_FMT):
        """Produce unicode representation of given tree.

        @param a_fmt - output format

        @return unicode string representing given tree
        """
        return unicode(self.s__str__(a_fmt))
