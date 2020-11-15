#! /bin/bash

cd $(dirname $0)/..

awk '
BEGIN {print "digraph G {"}
/^class.*\(.*\)/ {
    classname = gensub(/\(.*/, "", "g", $2)
    baseclass = gensub(/^.*\(/, "", "g", $2)
    baseclass = gensub(/\).*/, "", "g", baseclass)
    if (baseclass != "object") {
      q = "\""
      print q classname q " -> " q baseclass q
    }
}
END {print "}"}
' src/*.py > docs/class_diagram.dot

dot -Tpng -O docs/class_diagram.dot
