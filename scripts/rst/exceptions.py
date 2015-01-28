#!/usr/bin/env python2.7

##################################################################
"""
Module providing custom exceptions for RST package.

Exception Classes:
RSTException - abstract parent class of all RST excpetions
RSTBadFormat - exception thrown when bad line format is encounted
RSTBadLogic - exception thrown when illegitimate operation is attempted
RSTBadStructure - exception thrown when bad tree structure is encounted

"""

##################################################################
class RSTException(Exception):
    """
    Exception class used as parent for all RST-related exceptions.
    """
    def __init__(self, a_msg):
        """
        Class constructor.

        @param a_msg - line containing error description
        """
        super(RSTException, self).__init__(a_msg)

##################################################################
class RSTBadLogic(RSTException):
    """
    Exception raised when  illegitimate operation is attempted.

    This class subclasses `RSTException` and simply passes its error
    desciption to its parent class.

    Methods:

    Variables:
    """

    def __init__(self, a_msg):
        """
        Class constructor.

        @param a_line - line containing error description
        """
        super(RSTBadLogic, self).__init__(a_msg)

##################################################################
class RSTBadStructure(RSTException):
    """
    Exception raised when data structure appears to be broken.

    This class subclasses `RSTException` and simply passes its error
    desciption to its parent class.

    Methods:

    Variables:
    """

    def __init__(self, a_msg):
        """
        Class constructor.

        @param a_line - line containing error description
        """
        super(RSTBadStructure, self).__init__(a_msg)

##################################################################
class RSTBadFormat(RSTException):
    """
    Exception raised when attempting to parse an incorrect line.

    This class subclasses `RSTException` and simply passes its error
    desciption to its parent class.

    Methods:

    Variables:
    """

    def __init__(self, a_line):
        """
        Class constructor.

        @param a_line - line containing error description
        """
        super(RSTBadStructure, self).__init__(a_msg)
