#! /bin/sh

set -e

if [ "$1" = "--release" ]; then
  echo Release build
  cd src
  go clean -r -cache -testcache -modcache -fuzzcache
  cd ..
fi

VER=$(git describe)
DATE=$(date +%Y-%m-%d)
echo "$VER ($DATE)" > src/version.txt

cross_compile() {
  echo ======================== Building with $1 ========================
  builder=$1
  destdir=$2
  # The .git folder and the LICENSE file are needed for SBOM generation
  docker run -it --rm -v ./.git:/go/.git -v ./src:/go/src -v ./LICENSE:/go/src/LICENSE -v $destdir:/go/output -w /go/src "$builder" sh -c '
    [ -f /etc/profile.d/go_cross.sh ] && . /etc/profile.d/go_cross.sh;
    go mod tidy;
    go build -v -ldflags "-s -w" -o /go/output/picave .;
    cyclonedx-gomod app -json -output /go/output/picave.sbom.json -licenses -packages -std;
  '
}

cross_compile gotk-cross-builder-alpine3.19-armhf  ./dist/alpine3.19-armhf
cross_compile gotk-cross-builder-alpine3.19-arm64  ./dist/alpine3.19-arm64
cross_compile gotk-cross-builder-bookworm-armhf  ./dist/debian-bookworm-armhf
cross_compile gotk-cross-builder-bookworm-arm64  ./dist/debian-bookworm-arm64

cd src
go mod tidy
mkdir -p ../dist/macOS
go build -o ../dist/macOS/picave .
