#! /bin/sh

DEST=$1
if [ -z "$DEST" ]; then
  DEST=picave
fi

go mod tidy
go build -o "$DEST" .
