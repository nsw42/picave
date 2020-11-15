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

      if ((baseclass == "Exception") || (substr(baseclass, 1, 3) == "Gtk") || (substr(baseclass, 1, 6) == "ctypes")) {
        fillcolour="#d0d0d0";
      } else {
        fillcolour="";
      }
      if (fillcolour != "") {
        print q baseclass q " [ fillcolor=" q fillcolour q ", style=" q "filled" q " ]"
      }
    }
}
END {print "}"}
' src/*.py > docs/class_diagram.dot

dot -Tpng -O docs/class_diagram.dot
