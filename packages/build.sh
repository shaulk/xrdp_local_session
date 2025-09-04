#!/bin/bash

DISTRO="$1"
DISTRO_NAME="${DISTRO%%-*}"

case $(uname -m) in
	x86_64)
		arch="amd64"
		;;
	aarch64)
		arch="arm64"
		;;
	*)
		echo "Invalid architecture $(uname -m)." >&2
		exit 1
		;;
esac

case $DISTRO_NAME in
	debian)
		./build-deb.sh "$DISTRO" "$arch"
		;;
	ubuntu)
		./build-deb.sh "$DISTRO" "$arch"
		;;
	fedora)
		./build-rpm.sh "$DISTRO" "$arch"
		;;
	archlinux)
		./build-archlinux.sh "$arch"
		;;
	*)
		echo "Invalid distro." >&2
		exit 1
		;;
esac
