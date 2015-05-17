# default encoding
ENCODING = "utf-8"

# field separators for TSV format
LIST_SEP = ','
FIELD_SEP = '\t'
VALUE_SEP = '\034'

# output formats
XML_FMT = 1
LSP_FMT = 2
PC3_FMT = 4

# flags indicating internal or external children of trees should be returned
TREE_INTERNAL = 1
TREE_EXTERNAL = 2
TREE_ALL = 3

TERMINAL = "text"
NONTERMINAL = "span"

# relations that can go out from a nucleus node
NUC_RELS = set(["List", "Joint", "Sequence", "Contrast", "Same", "Comparison", \
                   "OTHER-multinuc", "span"])

# node identificators used in TSV format
_INT_NID = "nid"
_EXT_NID = "msgs2extnid"
_OFFSETS = "offsets"
_CHILDREN = "children"
_PARENT = "parent"
_RELNAME = "relname"
_TEXT = "text"
