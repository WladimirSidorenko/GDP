#!/usr/bin/env python

"""
Module providing RSTTree class.

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
    TSV_FMT, LSP_FMT, PC3_FMT, TREE_INTERNAL, TREE_EXTERNAL, TREE_ALL, \
    NUC_RELS, _CHILDREN, _TEXT, _OFFSETS
from exceptions import RSTBadFormat, RSTBadStructure

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
        self.echildren = set()
        self.ichildren = set()
        self.nucleus = False
        self.type = None
        self.end = -1
        self.start = -1
        self.text = ""
        self._terminal = False
        # nestedness level of this tree (used in print function)
        self._nestedness = 0
        self.update(**a_attrs)
        self._update_parent()

    def __cmp__(self, a_other):
        """
        Compare given tree with another one.

        @param a_other - tree to compare with

        @return \c integer lesser than, equal to, or greater than 0
        """
        ret = cmp(self.start, a_other.start)
        if ret == 0:
            return cmp(self.end, a_other.end)
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
        if self._terminal or self.type == "text":
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
        for ch in a_children:
            if ch.msgid is None or ch.msgid == self.msgid:
                if self.start < 0 or ch.start < self.start:
                    self.start = ch.start
                if self.end < 0 or ch.end > self.end:
                    self.end = ch.end
                self.ichildren.add(ch)
            else:
                self.echildren.add(ch)
        self._update_parent()
        return self

    def get_edus(self, a_flag = TREE_INTERNAL):
        """
        Return list of descendant terminal trees in sorted order.

        @param a_flag - (optional) flag indicating which descendants (internal
                        or external, or both) should be returned

        @return list of descendant terminal trees
        """
        ret = []
        if self._terminal:
            ret.append(self)
        elif self.type == "text":
            self._terminal = True
            ret.append(self)
        if a_flag & TREE_INTERNAL:
            for ch in self.ichildren:
                ret += ch.get_edus(a_flag)
        ret.sort(key = lambda edu: edu.start)
        if a_flag & TREE_EXTERNAL:
            for ch in self.echildren:
                ret += ch.get_edus(a_flag)
        return ret

    def get_subtrees(self, a_flag = TREE_INTERNAL):
        """
        Return list of descendant trees in sorted order.

        @param a_flag - (optional) flag indicating which descendants (internal
                        or external, or both) should be returned

        @return list of descendant trees
        """
        ret = []
        ret.append(self)
        if a_flag & TREE_INTERNAL:
            for ch in self.ichildren:
                ret += ch.get_subtrees(a_flag)
        ret.sort()
        if a_flag & TREE_EXTERNAL:
            for ch in self.echildren:
                ret += ch.get_subtrees(a_flag)
        return ret

    def update(self, **a_attrs):
        """
        Update tree's attributes.

        @param a_attrs - dictionary of tree attributes

        @return \c void
        """
        if "msgid" in a_attrs:
            self.msgid = a_attrs.pop("msgid")

        if _OFFSETS in a_attrs and a_attrs[_OFFSETS] is not None:
            if len(a_attrs[_OFFSETS]) == 2:
                self.start, self.end = [int(ofs) for ofs in a_attrs[_OFFSETS]]
                assert _TEXT in a_attrs, \
                    "Text attribute not specified for terminal node {:s}.".format(self.msgid or "")
                text = a_attrs[_TEXT]
                t_len = len(text)
                delta_start = t_len - len(text.lstrip())
                delta_end = t_len - len(text.rstrip())
                self.start += delta_start
                self.end -= delta_end
            elif a_attrs[_OFFSETS]:
                raise RSTBadFormat("Bad offset format:" + VALUE_SEP.join(a_attrs[_OFFSETS]))
            a_attrs.pop(_OFFSETS, None)

        if _CHILDREN in a_attrs:
            self.add_children(*a_attrs[_CHILDREN])
            a_attrs.pop(_CHILDREN, None)

        for k, v in a_attrs.iteritems():
            if hasattr(self, k):
                setattr(self, k, v)

        if self.type == _TEXT:
            self._terminal = True

        if self.relname in NUC_RELS:
            self.nucleus = True

    def _escape_text(self, a_text):
        """
        Return text with all brackets escaped.

        @param a_text - text to be escaped

        @return text with escaped brackets
        """
        return '"' + QUOTE.sub(ESCAPED, a_text) + '"'

    def _update_parent(self):
        """
        Update parent's start and end attributes if necessary.

        @return \c void
        """
        if self.parent is None or self.parent.msgid != self.msgid:
            return

        if self.start >= 0 and self.parent.start > self.start:
            self.parent.start = self.start

        if self.end >= 0 and self.parent.end < self.end:
            self.parent.end = self.end

        self.parent._update_parent()

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
