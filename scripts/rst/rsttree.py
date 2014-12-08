##################################################################
# Imports
from constants import LIST_SEP, FIELD_SEP, VALUE_SEP, EXT_NID, INT_NID, \
    TSV_FMT, LSP_FMT, PC3_FMT
from exceptions import RSTBadFormat, RSTBadStructure

##################################################################
# Class
class RSTTree(object):
    """
    Class for analyzing and processing single RST tree.

    Instance Variables:
    msg_id - id of the message to which this tree belongs
    root - pointer to root node of that tree
    nodes - dictionary mapping node id's to RST
    leaves - id's of nodes which are terminals in given tree

    Methods:
    parse - parse lines in tab separated value format
    """

    def __init__(self, a_msg_id = None):
        """
        Class constructor.

        @param a_msg_id - line with bad formatting
        """
        self.msg_id = a_msg_id

    def _parse_tsv(self, a_line):
        """
        Parse line in tab-separated value format.

        @param a_line - line to be parsed

        @return \c void
        """
        if not a_line:
            return

        fields = a_line.split(FIELD_SEP)
        if fields[0] != INT_NID:
            if fields[0] == EXT_NID:
                raise RSTBadFormat(a_line + u". Consider using RSTForrest instead.")
            else:
                raise RSTBadFormat(a_line)
        elif fields[2] != self.msg_id:
            raise RSTBadFormat(a_line + u""".  Message id of the node disagrees with message id
of the tree.""")
        nid = fields[1]
        if nid not in self.nodes:
            self.nodes[nid] = RSTNode(nid)
        # convert parsed fields to a dictionary and update information about the node
        inode = self.nodes[nid]
        inode.update(dic([(f[0], f[1:]) for f in \
                              [fld.split(VALUE_SEP) for fld in fields]]))
        if node.parent == None:
            if self.root != None:
                raise RSTBadStructure("Multiple roots found in tree.")

        if node.type == "text":
            self.leaves.append(node.inid)

    def __str__(self, a_fmt = TSV_OFMT):
        """Produce string representation of given tree.

        @param a_fmt - output format

        @return string representing given tree
        """
        raise NotImplementedError

    def __unicode__(self, a_fmt = TSV_OFMT):
        """Produce unicode representation of given tree.

        @param a_fmt - output format

        @return unicode string representing given tree
        """
        return unicode(self.s__str__(a_fmt))
