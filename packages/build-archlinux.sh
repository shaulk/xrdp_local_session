#!/bin/bash

set -e
set -x

ARCH="$1"

mkdir -p output

version=$(git describe --tags | cut -b2-)

docker buildx build \
	--platform linux/$ARCH \
	-t builder-archlinux-$ARCH \
	-f distros/archlinux/Dockerfile \
	--load \
	.

docker run \
	-i \
	--platform linux/$ARCH \
	-v $PWD/..:/src \
	-v $PWD/output:/output \
	builder-archlinux-$ARCH \
	bash -c "
		set -x &&
		mkdir /build &&
		cp -r /src /build/xrdp-local-session &&
		cp /src/PKGBUILD /build/PKGBUILD &&
		cd /build &&
		tar -czf xrdp-local-session.tar.gz xrdp-local-session &&
		cd xrdp-local-session &&
		useradd -m builder &&
		chown -R builder /build &&
		su - builder -c \"cd /build && makepkg\" &&
		for x in /build/*.pkg.tar.*;
		do
			cp \"\$x\" \"/output/\$(basename \"\$x\" | sed -r \"s/(\\.pkg\\..*)$/.archlinux\\1/\")\" || exit 1
		done
	"
