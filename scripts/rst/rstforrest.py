##################################################################
# Imports
from constants import LIST_SEP, FIELD_SEP, VALUE_SEP, \
    ENCODING, INT_NID, EXT_NID, TSV_FMT, LSP_FMT, PC3_FMT

from exceptions import RSTBadFormat
from rstnode import RSTNode
from rsttree import RSTTree
from union_find import UnionFind

##################################################################
# Class
class RSTForrest(object):
    """
    Class for analyzing and processing collections of RST trees.

    Variables:
    roots - set of RST tree roots
    msgid2tree - mapping from message id to the particular (sub-)tree
    msgid2root - mapping from message id to the root index of the corresponding
                 RST tree

    Methods:
    parse_line - general method for parsing lines (particular choice of
            parsing function will depend on the specified format)
    parse_tsv - parse lines in tab separated value format

    """

    def __init__(self):
        """
        Class constructor.
        """
        self.roots = set()
        self.msgid2tree = {}
        self.msgid2root = UnionFind()
        self._enid2enid = {}
        self._inid2enid = {}
        self._child2prnt = {}

    def parse_line(self, a_line, a_fmt = TSV_FMT):
        """
        General method for parsing lines with RST forrests.

        @param a_line - line to be parsed
        @param a_fmt - format of input data

        @return \c void
        """
        parse_func = self.parse_tsv
        if a_fmt == TSV_FMT:
            parse_func(a_line)
        else:
            raise NotImplementedError

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
            self._parse_tsv_extnid(fields)
        elif fields[0] == INT_NID:
            self._parse_tsv_intnid(fields)
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

    def _parse_tsv_extnid(self, a_fields):
        """
        Private method for parsing TSV line describing external node.

        @param a_fields - line's tab separated fields

        @return \c void
        """
        prnt_msgid, chld_msgid = a_fields[1].split(LIST_SEP)
        assert chld_msgid not in self._child2prnt or self._child2prnt[chld_msgid] == prnt_msgid, \
            "Multiple parents specified for message {:s}".format(chld_msgid).encode(ENCODING)

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
        self._join_trees(prnt_tree, chld_tree, a_fields[-1].split(VALUE_SEP))

    def _parse_tsv_intnid(self, a_fields):
        """
        Private method for parsing TSV line describing internal node.

        @param a_fields - line's fields

        @return \c void
        """
        # create new trees for referenced message ids, if not already created
        msgids = a_fields[1].split(LIST_SEP)
        for mid in msgids:
            if mid not in self.msgid2tree:
                self.msgid2tree[mid] = RSTTree(mid)
        # obtain id of the given node
        inid = a_fields[1]
        # convert specified attribute fields to an attribute dictionary
        f = []
        attrdic = dict()
        for fld in a_fields[3:]:
            f = fld.split(VALUE_SEP)
            attrdic[f[0]] = [el for el in f[1:] if el != ""]
        if len(msgids) == 2:
            # if the node connects two messages, then check if its id shouldn't
            # be mapped to something else
            if inid in self._enid2enid:
                inid = self._enid2enid[inid]
            else:
                # check if we already have a dedicated external node for the
                # parent message
                if msgids[0] in self._msgid2enid:
                    inid = self._enid2enid[inid] = self._msgid2enid[msgids[0]]
                else:
                    self._msgid2enid[msgid] = inid
            for chnid in attrdic["children"]:
                self._inid2enid[chnid] = inid
            # hopefully, that's the right thing to do next
            if not self.msgid2tree[msgid].has_node(inid):
                self.msgid2tree[msgid].add_node(a_nid = inid, a_attrs = attrdic)
            else:
                self.msgid2tree[msgid].update_node(a_nid = inid, a_attrs = attrdic)
        elif len(msgids) == 1:
            msgid = msgids[0]
            # translate id of the parent
            if "parent" in attrdic and attrdic["parent"] and attrdic["parent"][0] in self._enid2enid:
                attrdic["parent"] = self._enid2enid[attrdic["parent"]]
            # translate id's of the children, if needed
            if "children" in attrdic:
                translated_children = set()
                for chnid in set(attrdic["children"]):
                    if chnid in self._inid2enid:
                        translated_children.add(self._inid2enid[chnid])
                    else:
                        translated_children.add(chnid)
                attrdic["children"] = translated_children
            self.msgid2tree[msgid].add_node(a_nid = inid, a_attrs = attrdic)
        else:
            raise RSTBadFormat(line)
