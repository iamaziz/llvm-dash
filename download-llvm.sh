#!/usr/bin/env bash
LLVM_SRC="llvm-3.6.0.src"
LLVM_SRC_TARBALL="llvm-3.6.0.src.tar.xz"
LLVM_SRC_URL="http://llvm.org/releases/3.6.0/${LLVM_SRC_TARBALL}"
set -e

rm -rf "${LLVM_SRC}" build

if [ ! -f "${LLVM_SRC_TARBALL}" ]; then
    wget "${LLVM_SRC_URL}"
fi

md5sum -c MD5SUM

tar -xf "${LLVM_SRC_TARBALL}" "${LLVM_SRC}/docs" "${LLVM_SRC}/examples"

pushd "${LLVM_SRC}/docs"
make -f Makefile.sphinx BUILDDIR=../../build html
popd

rm -rf LLVM.docset
mkdir -p LLVM.docset/Contents/Resources/Documents
cp -r build/html/* LLVM.docset/Contents/Resources/Documents/
