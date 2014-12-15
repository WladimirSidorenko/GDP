##################################################################
# Imports
from constants import LIST_SEP, FIELD_SEP, VALUE_SEP, \
    TSV_FMT
from exceptions import RSTBadFormat

##################################################################
# Class
class RSTNode(object):
    """
    Class for analyzing and processing single RST node.

    Variables:
    id - internal id of that node
    children - node's children
    end - end offset of the text
    parent - node's parent
    relname - relation connecting that node to its parent
    span - node span covered
    start - start offset of the text
    text - actual text of terminal node
    type - type of that node (can be either `text' or `span')

    Methods:
    update - update information about a node from a dictionary
    """

    def __init__(self, a_id):
        """
        Class constructor.

        @param a_id - id of that node
        """
        self.id = a_id
        self.children = []
        self.end = -1
        self.parent = None
        self.relname = None
        self.span = []
        self.start = -1
        self.text = None
        self.type = None

    def update(self, a_attrs):
        """
        Update information about node attributes from dictionary.

        @param a_attrs - dictionary with information about the node

        @return \c void
        """
        if "offsets" in a_attrs:
            if len(a_attrs["offsets"]) == 2:
                self.start, self.end = a_attrs["offsets"]
            elif a_attrs["offsets"]:
                raise RSTBadFormat(VALUE_SEP.join(a_attrs["offsets"]))

        for k, v in a_attrs.iteritems():
            if hasattr(self, k):
                setattr(self, k, v)

    def __cmp__(self, a_other):
        """
        Compare given node with another one.

        @param a_other - node to compare with

        @return negative integer if self is less than, zero if equal to, and
        positive integer if self is greate than its argument
        """
        return cmp(self.start, a_other.start)

    def __str__(self, a_fmt = TSV_FMT):
        """
        Return string representation of given node.

        @param a_fmt - output format
        """
        pass

    def __unicode__(self, a_fmt = TSV_FMT):
        """
        Return unicode representation of given node.

        @param a_fmt - output format
        """
        return unicode(self.__str__(a_fmt))
