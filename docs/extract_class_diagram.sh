#! /bin/bash

cd $(dirname $0)/..

which gawk > /dev/null && awk=gawk
[ "$awk" = "" ] && awk=awk

$awk '
BEGIN {print "digraph G {"}
/^class.*\(.*\)/ {
    classname = gensub(/\(.*/, "", "g", $2)
    baseclass = gensub(/^.*\(/, "", "g", $0)
    baseclass = gensub(/\).*/, "", "g", baseclass)
    if ((baseclass != "object") && (baseclass != "ABC")) {
      q = "\""

      split(baseclass, bases, ",")
      for(idx in bases) {
        base = bases[idx]
        base = gensub(/^ */, "", "g", base)
        base = gensub(/ *$/, "", "g", base)
        print q classname q " -> " q base q

        if ((base == "Exception") || (substr(base, 1, 3) == "Gtk") || (substr(base, 1, 6) == "ctypes")) {
          fillcolour="#d0d0d0";
        } else if (substr(base, length(base)-8) == "Interface") {
          fillcolour="#d0d0ff";
        } else {
          fillcolour="";
        }
        if (fillcolour != "") {
          print q base q " [ fillcolor=" q fillcolour q ", style=" q "filled" q " ]"
        }
      }
    }
}
END {print "}"}
' src/*.py > docs/class_diagram.dot

dot -Tpng -O docs/class_diagram.dot
