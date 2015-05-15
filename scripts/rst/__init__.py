#!/usr/bin/env python

##################################################################
# Documentation
"""
Package for analyzing, constructing, and modifying RST trees.

Constants:
ENCODING - default encoding used for output (utf-8)
FIELD_SEP - field separator for TSV format (tab character in other words)
LIST_SEP - list items separator for TSV format
VALUE_SEP - attribute-value separator for TSV format
TSV_FMT - flag for tab-separated format
LSP_FMT - flag for s-expression format
PC3_FMT - flag for PC3 (SGML) format
XML_FMT - flag for XML format
TERMINAL - string representing that given node is of terminal type
TREE_INTERNAL - flag indicating that only internal tree nodes
          should be processed
TREE_EXTERNAL - flag indicating that only external tree nodes
          should be processed
TREE_ALL - flag indicating that both internal and external tree
          nodes should be processed
NUC_RELS - set of relations that can go out from a nucleus node

Classes:
RSTForrest - class for dealing with collections of RST trees
RSTTree - class for dealing with a single RST tree (which can also
          be just a single node)

Exceptions:
RSTException - abstract exception used as parent for all RST-related exceptions
RSTBadFormat - raised when attempting to parse an incorrect line
RSTBadLogic - raised when when illegitimate operation is attempted
RSTBadStructure - raised when data structure to be read appears to be broken

@author = Uladzimir Sidarenka
@mail = <sidarenk at uni dash potsdam dot de>
@version = 0.0.1

"""

##################################################################
# Imports
from constants import ENCODING, LIST_SEP, FIELD_SEP, VALUE_SEP, \
    LSP_FMT, XML_FMT, PC3_FMT, TREE_INTERNAL, TREE_EXTERNAL, \
    TREE_ALL, NUC_RELS

from exceptions import RSTException, RSTBadFormat, RSTBadLogic, RSTBadStructure

from rstforrest import RSTForrest
from rsttree import RSTTree

##################################################################
# Intialization
__all__ = ["ENCODING", "LIST_SEP", "FIELD_SEP", "VALUE_SEP", \
               "TSV_FMT", "LSP_FMT", "PC3_FMT", \
               "TREE_INTERNAL", "TREE_EXTERNAL", "TREE_ALL", "NUC_RELS", \
               "RSTForrest", "RSTTree", \
               "RSTException", "RSTBadFormat", "RSTBadStructure"]
__author__ = "Uladzimir Sidarenka"
__email__ = "sidarenk at uni dash potsdam dot de"
__version__ = '0.0.1'
