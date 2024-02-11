#! /bin/sh

cross_build() {
  GTK_BUILDER_TAG=$1
  DESTDIR=$2
  mkdir -p $DESTDIR
  echo Building with $GTK_BUILDER_TAG
  docker run -it --rm -v ./:/go/src -w /go/src "$GTK_BUILDER_TAG" ./build.sh "$DESTDIR/picave"
}

if [ $# -eq 0 ]; then
  cross_build go-gtk-image-linuxarmhf dist/linuxarmhf
  cross_build go-gtk-image-linuxarm64 dist/linuxarm64
else
  BUILDER=$1
  DESTDIR=$2
  cross_build "$BUILDER" "$DESTDIR"
fi
