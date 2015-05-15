#!/usr/bin/env python

"""
Module providing class for RSTTree.

Constants:
DQUOTES - regular expression matching double quotes
ESCAPED - substitution string used to escape quotes
EXT_REL_PRFX - prefix of external relations

Class:
RSTTree - class representing single RST tree

@author = Uladzimir Sidarenka
@mail = <sidarenk at uni dash potsdam dot de>
@version = 0.0.1

"""

##################################################################
# Imports
from constants import ENCODING, LIST_SEP, FIELD_SEP, VALUE_SEP, \
    XML_FMT, TREE_INTERNAL, TREE_EXTERNAL, TREE_ALL, \
    NUC_RELS, _CHILDREN, _TEXT, _OFFSETS
from exceptions import RSTBadFormat, RSTBadLogic, RSTBadStructure

import re
import sys

##################################################################
# Constants
QUOTE = re.compile("([\"'])")
ESCAPED = r"\\\1"
EXT_REL_PRFX = "r-"

##################################################################
# Class
class RSTTree(object):
    """
    Class for analyzing and processing single RST tree.

    Instance Variables:
    id - id of the root node
    msgid - id of the message to which this tree belongs
    parent - tree's parent tree
    relname - relation connecting this tree to its parent
    ichildren - internal child trees (those which pertain to the same message)
    echildren - external child trees (those which pertain to other messages)

    type - type of this tree (can be either `text' or `span')
    start - start offset of the text (for terminal trees)
    end - end offset of the text (for terminal trees)
    text - actual text of terminal tree (for terminal trees)

    Methods:
    add_children - add child trees
    get_edus - return list of descendant terminal trees
    get_subtrees - return list of all descendants (by default, only internal
             subtrees are returned)
    unicode_min - return minimal unicode representation of the given tree
    str_min - return minimal string representation of the given tree
    update - update attributes of the given tree

    """

    def __init__(self, a_id, **a_attrs):
        """
        Class constructor.

        @param a_id - id of the root node of this tree
        @param a_attrs - dictionary of attributes of this tree
        """
        self.id = a_id
        self.msgid = None
        self.parent = None
        self.relname = None
        self.etype = None
        self.external = False
        self.echildren = set()
        self.ichildren = set()
        self.nucleus = False
        self.type = None
        self.start = -1
        self.end = -1
        self.t_start = -1        # start position of the whole subtree
        self.t_end = -1          # end position of the whole subtree
        self.text = ""
        self._terminal = False
        # nestedness level of this tree (used in print function)
        self._nestedness = 0
        self.update(**a_attrs)

    def __eq__(self, a_other):
        """
        Compare given tree with another one and return true if they are the same.

        @param a_other - tree to compare with

        @return true if trees are the same
        """
        if not isinstance(a_other, RSTTree):
            raise RSTBadLogic("Can't compare RST tree with {:s}".format(a_other.__class__.__name__))
        return id(self) == id(a_other)

    def __ne__(self, a_other):
        """
        Compare given tree with another one and return true if they are not same.

        @param a_other - tree to compare with

        @return true if trees are not the same
        """
        return not self.__eq__(a_other)

    def __cmp__(self, a_other):
        """
        Compare given tree with another one.

        @param a_other - tree to compare with

        @return \c integer lesser than, equal to, or greater than 0
        """
        # print >> sys.stderr, repr(self)
        # print >> sys.stderr, repr(a_other)
        ret = cmp(self.t_start, a_other.t_start)
        if ret == 0:
            return cmp(self.t_end, a_other.t_end)
        return ret

    def __str__(self):
        """Produce string representation of the tree.

        @return string representation of the tree
        """
        return unicode(self).encode(ENCODING)

    def __unicode__(self):
        """Produce unicode representation of the tree.

        @return unicode representation of the tree
        """
        ret = u'\t' * self._nestedness
        ret += u"(" + self.id
        if self.msgid is not None and (self.parent is None or self.parent.msgid != self.msgid):
            ret += u" (msgid " + self._escape_text(self.msgid) + ")"
        ret += u" (type " + self._escape_text(self.type or "") + ")"
        if self.relname:
            ret += u" (relname " + self._escape_text(self.relname) + ")"
        if self._terminal or self.start >= 0:
            self._terminal = True
            ret += u" (start " + unicode(self.start) + ")"
            ret += u" (end " + unicode(self.end) + ")"
            ret += u" (text " + self._escape_text(self.text) + ")"
        # append internal nodes to the output
        ret += self._unicode_children(self.ichildren)
        # append external nodes to the output
        ret += self._unicode_children(self.echildren)
        ret += u")"
        return ret

    def str_min(self, a_flag = TREE_INTERNAL, *a_attrs):
        """
        Return minimal string representation of the given tree.

        @param a_attrs - attributes that should be printed for trees

        @return minimal unicode representation
        """
        return self.unicode_min(a_flag, a_attrs).encode(ENCODING)

    def unicode_min(self, a_flag = TREE_INTERNAL, *a_attrs):
        """
        Return minimal unicode representation of the given tree.

        @param a_attrs - attributes that should be printed for trees

        @return minimal unicode representation
        """
        ret = u'\t' * self._nestedness
        ret += u"("
        if self._nestedness < 2:
            ret += self.id
            if self._nestedness == 2:
                avalue = None
                for attr in a_attrs:
                    avalue = getattr(attr, None)
                    if avalue is not None:
                        ret += " (" + attr + ' ' + avalue + ')'
        if self._terminal:
            ret += u" (text " + self._escape_text(self.text) + ")"
        else:
            ret += u"..."

        orig_nestedness = 0
        chld_nestedness = self._nestedness + 1
        if a_flag & TREE_INTERNAL:
            for ch in self.ichildren():
                orig_nestedness = ch_tree._nestedness
                ch_tree._nestedness = chld_nestedness
                ret += '\n' + ch_tree.unicode_min()
                ch_tree._nestedness = orig_nestedness
        if a_flag & TREE_EXTERNAL:
            for ch in self.echildren():
                orig_nestedness = ch_tree._nestedness
                ch_tree._nestedness = chld_nestedness
                ret += '\n' + ch_tree.unicode_min()
                ch_tree._nestedness = orig_nestedness
        return ret

    def add_children(self, *a_children):
        """
        Add new child tree.

        @param a_children - child trees to be added

        @return pointer to this tree
        """
        changed = False
        external = bool(self.external and self.etype != TERMINAL)
        min_start = max_end = -1
        for ch in a_children:
            # update lists of children
            if ch.msgid is None or ch.msgid == self.msgid:
                self.ichildren.add(ch)
            else:
                self.echildren.add(ch)
            if self.external and
            # update minimum start and maximum character offsets available from
            # children
            if external:
                # update minimum start and maximum character offsets available from
                # children
                if min_start < 0 or ch.id < min_start:
                    min_start = ch.id
                if max_end < 0 or ch.id > max_end:
                    max_end = ch.id
            else:
                if min_start < 0 or (ch.t_start >= 0 and ch.t_start < min_start):
                    min_start = ch.t_start
                if ch.t_end > max_end:
                    max_end = ch.t_end
        # update self and parent node, if necessary
        self._update_start_end(min_start, max_end)
        return self

    def get_edus(self, a_flag = TREE_INTERNAL):
        """
        Return list of descendant terminal trees in sorted order.

        @param a_flag - (optional) flag indicating which descendants (internal
                        or external, or both) should be returned

        @return list of descendant terminal trees
        """
        ret = []
        print >> sys.stderr, "get_edus: processing tree '{:s}' (is terminal = {:d})".format(self.id, \
                                                                                                self._terminal)
        if self._terminal:
            ret.append(self)

        if a_flag & TREE_INTERNAL:
            if not self.external or self.etype == "text":
                for ch in self.ichildren:
                    ret += ch.get_edus(a_flag)
                ret.sort(key = lambda edu: edu.start)
        if a_flag & TREE_EXTERNAL:
            for ch in self.echildren:
                ret += ch.get_edus(a_flag)
            if self.external and self.etype != "text":
                for ch in self.ichildren:
                    ret += ch.get_edus(a_flag)
        return ret

    def get_subtrees(self, a_flag = TREE_INTERNAL):
        """
        Return list of all descendant trees in sorted order.

        @param a_flag - (optional) flag indicating which descendants (internal
                        or external, or both) should be returned

        @return list of descendant trees
        """
        ret = []
        ret.append(self)
        if a_flag & TREE_INTERNAL:
            if not self.external or self.etype == TERMINAL:
                for ch in self.ichildren:
                    ret += ch.get_subtrees(a_flag)
                ret.sort()
        if a_flag & TREE_EXTERNAL:
            for ch in self.echildren:
                ret += ch.get_subtrees(a_flag)
            if self.external and self.etype != TERMINAL:
                for ch in self.ichildren:
                    ret += ch.get_subtrees(a_flag)
        return ret

    def update(self, **a_attrs):
        """
        Update tree's attributes.

        @param a_attrs - dictionary of tree attributes

        @return \c void
        """
        for k, v in a_attrs.iteritems():
            if hasattr(self, k):
                setattr(self, k, v)
        # set private variables and convert types of some attributes
        if self.type == "segment":
            self._terminal = True
            self.t_start = self.start = int(self.start)
            self.t_end = self.end = int(self.end)
        else:
            self._terminal = False
        self.external = int(self.external)

    def _escape_text(self, a_text):
        """
        Return text with all brackets escaped.

        @param a_text - text to be escaped

        @return text with escaped brackets
        """
        return '"' + QUOTE.sub(ESCAPED, a_text) + '"'

    def _update_tstart_tend(self, a_start, a_end)
        """
        Update start and end attributes of current node and its parent, if necessary.

        @param a_start - new start value
        @param a_end - new end value

        @return \c void
        """
        if self._terminal:
            if not self.parent is None:
                self.parent._update_start_end(a_start, a_end, a_external)
        elif a_external and self.external and self.etype != TERMINAL:
            changed = False
            if self.t_start < 0 or self.t_start > a_start:
                self.t_start = a_start
                changed = True
            if self.t_end < 0 or self.t_end < a_end:
                self.t_end = a_end
                changed = True
            if changed and not self.parent is None:
                self.parent._update_start_end(a_start, a_end, a_external)
    #     if self.parent is None or self.parent.msgid != self.msgid:
    #         return
    #     changed = False
    #     if self.t_start >= 0 and (self.parent.t_start < 0 or self.parent.t_start > self.t_start):
    #         changed = True
    #         self.parent.t_start = self.t_start

    #     if self.t_end >= 0 and (self.parent.t_end < 0 or self.parent.t_end < self.t_end):
    #         changed = True
    #         self.parent.t_end = self.t_end

    #     if changed:
    #         self.parent._update_parent()

    def _unicode_children(self, a_children):
        """
        Convert children to their unicode representation.

        @param a_children - children whose unicode representation is requested

        @return unicode string representing children
        """
        ret = u""
        orig_nestedness = 0
        chld_nestedness = self._nestedness + 1
        for ch_tree in a_children:
            orig_nestedness = ch_tree._nestedness
            ch_tree._nestedness = chld_nestedness
            ret += '\n' + unicode(ch_tree)
            ch_tree._nestedness = orig_nestedness
        return ret
