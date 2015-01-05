#!/usr/bin/env python2.7

##################################################################
"""
Module providing RSTTree class.

Constants:
DQUOTES - regular expression matching double quotes
ESCAPED - substitution string used to escape quotes

Class:
RSTTree - class representing single RST tree

"""

##################################################################
# Imports
from constants import ENCODING, LIST_SEP, FIELD_SEP, VALUE_SEP, \
    CHILDREN, OFFSETS, TSV_FMT
from exceptions import RSTBadFormat

import re

##################################################################
# Constants
QUOTE = re.compile("([\"'])")
ESCAPED = r"\\\1"

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
    tree - tree to which this node belongs
    type - type of that node (can be either `text' or `span')

    Methods:
    update - update tree's attributes
    """

    def __init__(self, a_id, a_tree = None):
        """
        Class constructor.

        @param a_id - id of that node
        """
        self.id = a_id
        self.children = set()
        self.end = -1
        self.parent = None
        self.relname = None
        self.span = []
        self.start = -1
        self.text = None
        self.tree = a_tree
        self.type = None
        self._depth = 0

    def update(self, a_attrs):
        """
        Update information about node attributes from dictionary.

        @param a_attrs - dictionary with information about the node

        @return \c void
        """
        if OFFSETS in a_attrs and a_attrs[OFFSETS] is not None:
            if len(a_attrs[OFFSETS]) == 2:
                self.start, self.end = a_attrs[OFFSETS]
            elif a_attrs[OFFSETS]:
                raise RSTBadFormat("Bad offset format:" + VALUE_SEP.join(a_attrs[OFFSETS]))
            a_attrs.pop(OFFSETS, None)

        if CHILDREN in a_attrs and a_attrs:
            self.children = self.children.union(a_attrs[CHILDREN])
            a_attrs.pop(CHILDREN, None)

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

    def __str__(self):
        """
        Return string representation of given node.

        @return string representation of given node
        """
        return unicode(self).encode(ENCODING)

    def __unicode__(self):
        """
        Return unicode representation of given node.

        @return unicode representation of given node
        """
        ostr = self._depth * '\t' + "(" + self.id
        ostr += " (type " + self.type + ")"
        if self.relname:
            ostr += " (relname " + self.relname + ")"
        if self.start >= 0:
            ostr += " (start " + str(self.start) + ")"
            ostr += " (end " + str(self.end) + ")"
            ostr += " (text " + self._escape_text(self.text) + ")"
        chdepth = self._depth + 1
        chnode = None
        for ch in self.children:
            chnode = self.tree.nodes[ch]
            chnode._depth = chdepth
            ostr += '\n' + unicode(chnode)
        ostr += ")"
        return ostr

    def _escape_text(self, a_text):
        """
        Return text with all brackets escaped.

        @return text with escaped brackets
        """
        return '"' + DQUOTES.sub(ESCAPED, a_text) + '"'
