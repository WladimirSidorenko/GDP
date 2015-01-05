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

"""
##################################################################
# Imports
from constants import ENCODING, LIST_SEP, FIELD_SEP, VALUE_SEP, \
    CHILDREN, OFFSETS, EXT_NID, INT_NID, TSV_FMT, LSP_FMT, PC3_FMT
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
    terminal - flag indicating whether this tree is a terminal node

    Methods:
    add_child - add child tree
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
        self.children = set()
        self.type = None
        self.end = -1
        self.start = -1
        self.text = ""
        self.terminal = False
        self._nestedness = 0          # nestedness level of this tree (used in print function)
        self.update(a_attrs)

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
        ret += u"(" + self.id + ' '
        if self.parent is None or self.parent.msgid != self.msgid:
            ostr += u"(msgid " + self.msgid + ") "
        ostr += u"(type " + self.type + ") "
        if self.relname:
            ostr += u"(relname " + self.relname + ") "
        if self.terminal:
            ostr += u"(start " + unicode(self.start) + ") "
            ostr += u"(end " + unicode(self.start) + ") "
            ostr += u"(text " + self._escape_text(self.text) + ") "

        # append internal nodes to the output
        ostr += self._unicode_children(self.ichildren)
        # append external nodes to the output
        ostr += self._unicode_children(self.echildren)
        ostr += u")"
        return ret

    def add_child(self, a_child):
        """
        Add new child tree.

        @param a_child - child tree to be added

        @return pointer to this tree
        """
        self.children.add(a_child)
        return self

    def update(self, a_attrs):
        """
        Update tree's attributes.

        @param a_attrs - attributes of the tree

        @return \c void
        """
        if OFFSETS in a_attrs and a_attrs[OFFSETS] is not None:
            if len(a_attrs[OFFSETS]) == 2:
                self.start, self.end = a_attrs[OFFSETS]
            elif a_attrs[OFFSETS]:
                raise RSTBadFormat("Bad offset format:" + VALUE_SEP.join(a_attrs[OFFSETS]))
            a_attrs.pop(OFFSETS, None)

        if CHILDREN in a_attrs:
            for ch in a_attrs[CHILDREN]:
                if ch.msgid == self.msgid:
                    self.ichildren.add(ch)
                else:
                    self.echildren.add(ch)
            a_attrs.pop(CHILDREN, None)

        for k, v in a_attrs.iteritems():
            if hasattr(self, k):
                setattr(self, k, v)

        if self.text and self.type == "text":
            self.terminal = True

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
        ostr = u""
        for ch_tree in a_children:
            if ch_tree._nestedness == 0:
                ch_tree._nestedness += 1
            ostr += '\n' + unicode(ch_tree)
        return ostr
