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
    TERMINAL, NONTERMINAL, NUC_RELS, _CHILDREN, _TEXT, _OFFSETS
from exceptions import RSTBadFormat, RSTBadLogic, RSTBadStructure

import re
import sys

##################################################################
# Constants
QUOTE = re.compile(u"([\"'])", re.U)
ESCAPED = ur"\\\1"
EXT_REL_PRFX = "r-"


##################################################################
# Class
class RSTTree(object):
    """
    Class for analyzing and processing single RST tree.

    Instance Variables:
    id - id of the root node
    msgid - id of the message to which this tree belongs
    discid - id of the message in discussion
    parent - pointer to the parent tree
    relname - relation connecting this tree to its parent
    ichildren - internal child trees (those which pertain to the same message)
    echildren - external child trees (those which pertain to other messages)

    type - type of this tree (can be either `text' (TERMINAL) or `span' (NONTERMINAL))
    start - start offset of the text
    end - end offset of the text
    t_start - start offset of the underlying subtree
    t_end - end offset of the underlying subtree
    terminal - boolean value indicating whether given node is terminal
               or not
    text - actual text of terminal node

    Methods:
    add_children - add child trees
    adjust_offsets - adjust offsets of terminal nodes to exclude trailining and
                     leading whitespaces
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
        self.discid = -1
        self.parent = None
        self.relname = None
        self.etype = None
        self.external = False
        self.echildren = set()
        self.ichildren = set()
        self.nucleus = False
        self.type = None
        self.start = (-1, -1)
        self.end = (-1, -1)
        self.t_start = (-1, -1) # start position of the whole subtree
        self.t_end = (-1, -1)   # end position of the whole subtree
        self.text = ""
        self.terminal = False
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
        return self.id == a_other.id and self.msgid == a_other.msgid

    def __hash__(self):
        """Return hash key for the given element.

        @return tuple: message id, node id

        """
        return int(self.id) ^ int(self.msgid)

    def __ne__(self, a_other):
        """
        Compare given tree with another one and return true if they are not the same.

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
        if self.terminal or self.start >= 0:
            self.terminal = True
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

    def unicode_min(self, a_flag=TREE_INTERNAL, *a_attrs):
        """Return minimal unicode representation of the given tree.

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
        text = ""
        if self.terminal:
            text = self.text.decode("utf-8", errors="ignore")
            ret += u" (text " + \
                   self._escape_text(text) \
                   + u")"
        else:
            ret += u"..."

        orig_nestedness = 0
        chld_nestedness = self._nestedness + 1
        if a_flag & TREE_INTERNAL:
            for ch_tree in self.ichildren:
                orig_nestedness = ch_tree._nestedness
                ch_tree._nestedness = chld_nestedness
                ret += u'\n' + ch_tree.unicode_min()
                ch_tree._nestedness = orig_nestedness
        if a_flag & TREE_EXTERNAL:
            for ch in self.echildren():
                orig_nestedness = ch_tree._nestedness
                ch_tree._nestedness = chld_nestedness
                ret += u'\n' + ch_tree.unicode_min()
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
        min_start = max_end = (-1, -1)
        for ch in a_children:
            # update lists of children
            if ch.msgid == self.msgid:
                self.ichildren.add(ch)
            else:
                self.echildren.add(ch)
            # update minimum start and maximum positions available from
            # children
            if ch.t_start[0] > -1 and (min_start[0] < 0 or min_start > ch.t_start):
                min_start = ch.t_start
            if ch.t_end > max_end:
                max_end = ch.t_end
        # update `start` and `end` values of self and parent, if necessary
        self._update_tstart_tend(min_start, max_end)
        return self

    def adjust_offsets(self):
        """
        Adjust offsets of terminal nodes to remove leading and trailing whitespaces.

        @return \c void
        """
        if not self.terminal or not self.text:
            return
        assert self.start == self.t_start and self.t_start[0] > -1, "start and t_start fields of\
 RST terminal diverged before `adjust_offsets was called`"
        assert self.end == self.t_end and self.t_end[0] > -1, "end and t_end fields of RST\
 terminal diverged before `adjust_offsets was called`"
        orig_len = len(self.text)
        self.text = self.text.lstrip()
        delta_start = orig_len - len(self.text)
        orig_len = len(self.text)
        self.text = self.text.rstrip()
        delta_end = orig_len - len(self.text)
        self.start = self.t_start = (self.t_start[0], self.t_start[-1] + delta_start)
        self.end = self.t_end = (self.t_end[0], self.t_end[-1] - delta_end)

    def get_edus(self, a_flag=TREE_INTERNAL):
        """
        Return list of descendant terminal trees in sorted order.

        @param a_flag - (optional) flag indicating which descendants (internal
                        or external, or both) should be returned

        @return list of descendant terminal trees
        """
        ret = []
        if self.terminal:
            ret.append(self)
        # external EDUs subsume internal ones
        if a_flag & TREE_EXTERNAL or not self.external or self.etype == TERMINAL:
            for ch in self.ichildren:
                ret += ch.get_edus(a_flag)
        # additionally, external EDUs also include external children
        if a_flag & TREE_EXTERNAL:
            for ch in self.echildren:
                ret += ch.get_edus(a_flag)
        ret.sort(key = lambda edu: edu.start)
        return ret

    def get_subtrees(self, a_flag=TREE_INTERNAL):
        """Return list of all descendant trees in sorted order.

        @param a_flag - (optional) flag indicating which descendants (internal
                        or external, or both) should be returned

        @return set of descendant trees

        """
        ret = []
        ret.append(self)
        if a_flag & TREE_EXTERNAL:
            for ch in self.echildren:
                ret += ch.get_subtrees(a_flag)
            if self.external and self.etype != TERMINAL:
                for ch in self.ichildren:
                    ret += ch.get_subtrees(a_flag)
        if a_flag & TREE_INTERNAL:
            if not self.external or self.etype == TERMINAL:
                for ch in self.ichildren:
                    ret += ch.get_subtrees(a_flag)
                ret.sort()
            else:
                if not (a_flag & TREE_EXTERNAL and
                        self.external and
                        self.etype != TERMINAL):
                    for ch in self.ichildren:
                        if ch.msgid == self.msgid:
                            return set(ret + ch.get_subtrees())
        return set(ret)

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
            self.type = TERMINAL
            self.terminal = True
            self.t_start = self.start = int(self.start)
            self.t_end = self.end = int(self.end)
        else:
            self.type = NONTERMINAL
            self.terminal = False
        self.external = int(self.external)

    def _escape_text(self, a_text):
        """
        Return text with all brackets escaped.

        @param a_text - text to be escaped

        @return text with escaped brackets
        """
        return u'"' + QUOTE.sub(ESCAPED, a_text) + u'"'

    def _update_tstart_tend(self, a_start, a_end):
        """
        Update `t_start` and `t_end` attributes.

        @param a_start - new `t_start` value
        @param a_end - new `t_end` value

        @return \c void
        """
        update = False
        # check if new `t_start` value should be updated
        if a_start[0] > -1 and (self.t_start[0] < 0 or a_start < self.t_start):
            update = True
            self.t_start = a_start
        if a_end > self.t_end:
            update = True
            self.t_end = a_end
        # update `start` and `end` values of non-terminal nodes
        if update and not self.terminal:
            if a_start[0] == self.discid or (self.external and self.etype != TERMINAL):
                self.start = self.t_start
            if a_end[0] == self.discid or (self.external and self.etype != TERMINAL):
                self.end = self.t_end
        # propagate new `t_start`, `t_end` values to the parent
        if update and self.parent is not None:
            self.parent._update_tstart_tend(a_start, a_end)

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
