# default encoding
ENCODING = "utf-8"

# field separators for TSV format
LIST_SEP = ','
FIELD_SEP = '\t'
VALUE_SEP = '\034'

# output formats
TSV_FMT = 1
LSP_FMT = 2
PC3_FMT = 4

# flags indicating internal or external children of trees should be returned
TREE_INTERNAL = 1
TREE_EXTERNAL = 2
TREE_ALL = 3

# node identificators used in TSV format
_INT_NID = "nid"
_EXT_NID = "msgs2extnid"
_OFFSETS = "offsets"
_CHILDREN = "children"
_PARENT = "parent"
_RELNAME = "relname"
