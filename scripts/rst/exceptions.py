##################################################################
class RSTException(Exception):
    """
    Abstract exception class used as parent for all RST-related exceptions.
    """
    pass

##################################################################
class RSTBadStructure(RSTException):
    """
    Exception raised when data structure appears to be broken.

    Methods:

    Variables:
    msg - message containing error description
    """

    def __init__(self, a_msg):
        """
        Class constructor.

        @param a_line - line with bad formatting
        """
        self.msg = a_msg

    def __str__(self):
        """
        String representation.

        @return string containing the error message
        """
        return self.msg.encode(ENCODING)

    def __unicode__(self):
        """
        Unicode string representation.

        @return unicode string containing the erro message
        """
        return self.msg.encode("utf-8")

##################################################################
class RSTBadFormat(RSTException):
    """
    Exception raised when attempting to parse an incorrect line.

    Methods:

    Variables:
    msg - message containing description of an error
    """

    def __init__(self, a_line):
        """
        Class constructor.

        @param a_line - line with bad formatting
        """
        self.msg = u"Incorrect line format: '{:s}'".format(a_line)

    def __str__(self):
        """
        String representation.

        @return string containing the error message
        """
        return self.msg.encode(ENCODING)

    def __unicode__(self):
        """
        Unicode string representation.

        @return unicode string containing the erro message
        """
        return self.msg.encode("utf-8")
