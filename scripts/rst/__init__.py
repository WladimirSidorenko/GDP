#!/usr/bin/env python2.7

##################################################################
# Documentation
"""
Package for analyzing, constructing, and modifying RST trees.

Constants:
FIELD_SEP - field separator for TSV format (tab character in other words)
LIST_SEP - list items separator for TSV format
VALUE_SEP - attribute-value separator for TSV format
EXT_NID - string denoting start of description of an external node
INT_NID - string denoting start of description of an internal node

Classes:
RSTForrest - class for dealing with collections of RST trees
RSTNode - class representing single RST node
RSTTree - class for dealing with a single RST tree

Exceptions:
RSTException - abstract exception used as parent for all RST-related exceptions
RSTBadFormat - raised when attempting to parse an incorrect line
RSTBadStructure - raised when data structure to be read appears to be broken
"""

##################################################################
# Imports
from constants import LIST_SEP, FIELD_SEP, VALUE_SEP, INT_NID, EXT_NID
from exceptions import RSTException, RSTBadFormat, RSTBadStructure

from rstforrest import RSTForrest
from rstnode import RSTNode
from rsttree import RSTTree

##################################################################
# Intialization
__all__ = ["LIST_SEP", "FIELD_SEP", "VALUE_SEP", \
               "INT_NID", "EXT_NID", \
               "RSTForrest", "RSTTree", "RSTNode", \
               "RSTException", "RSTBadFormat", "RSTBadStructure"]
__author__ = "Uladzimir Sidarenka"
__email__ = "sidarenk at uni dash potsdam dot de"
__version__ = '0.0.1'
