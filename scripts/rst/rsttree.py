#!/usr/bin/env python2.7

##################################################################
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
    _CHILDREN, _OFFSETS
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
    update - update tree attributes
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
        self.type = None
        self.end = -1
        self.start = -1
        self.text = ""
        self._terminal = False
        self._nestedness = 0          # nestedness level of this tree (used in print function)
        self.update(**a_attrs)

    def __cmp__(self, a_other):
        """
        Compare given tree with another one.

        @param a_other - tree to compare with

        @return \c integer lesser than, equal to, or greater than 0
        """
        return cmp(self.start, a_other.start)

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
        ret += u" (type " + self._escape_text(self.type) + ")"
        if self.relname:
            ret += u" (relname " + self._escape_text(self.relname) + ")"
        if self._terminal:
            ret += u" (start " + unicode(self.start) + ")"
            ret += u" (end " + unicode(self.end) + ")"
            ret += u" (text " + self._escape_text(self.text) + ")"
        # append internal nodes to the output
        ret += self._unicode_children(self.ichildren)
        # append external nodes to the output
        ret += self._unicode_children(self.echildren)
        ret += u")"
        return ret

    def add_children(self, *a_children):
        """
        Add new child tree.

        @param a_children - child trees to be added

        @return pointer to this tree
        """
        for ch in a_children:
            if ch.msgid is None or ch.msgid == self.msgid:
                self.ichildren.add(ch)
            else:
                self.echildren.add(ch)
        return self

    def get_edus(self, a_flag = TREE_INTERNAL):
        """
        Return list of descendant terminal trees in sorted order.

        @param a_flag - (optional) flag indicating which descendants (internal
                        or external, or both) should be processed

        @return list of descendant terminal trees
        """
        ret = []
        if self._terminal:
            ret.append(self)
        if a_flag & TREE_INTERNAL:
            for ch in self.ichildren:
                ret += ch.get_edus(a_flag)
        ret.sort(key = lambda edu: edu.start)
        if a_flag & TREE_EXTERNAL:
            for ch in self.echildren:
                ret += ch.get_edus(a_flag)
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
                assert "text" in a_attrs, \
                    "Text attribute not specified for terminal node {:s}.".format(self.msgid or "")
                text = a_attrs["text"]
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

        if self.type == "text":
            self._terminal = True

    def _escape_text(self, a_text):
        """
        Return text with all brackets escaped.

        @param a_text - text to be escaped

        @return text with escaped brackets
        """
        return '"' + QUOTE.sub(ESCAPED, a_text) + '"'

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
