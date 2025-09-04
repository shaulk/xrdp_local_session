#!/bin/bash

set -e
set -x

DISTRO="$1"
ARCH="$2"
DISTRO_NAME="${DISTRO%%-*}"
DISTRO_VERSION="${DISTRO#*-}"

version=$(git describe --tags | cut -b2-)

mkdir -p output
mkdir -p deps

docker buildx build \
	--platform linux/$ARCH \
	-t builder-$DISTRO_NAME-$DISTRO_VERSION-$ARCH \
	-f distros/$DISTRO_NAME/Dockerfile.$DISTRO_NAME-$DISTRO_VERSION \
	--load \
	.

docker run \
	-i \
	--rm \
	--platform linux/$ARCH \
	-v $PWD/..:/src \
	-v $PWD/output:/output \
	builder-$DISTRO_NAME-$DISTRO_VERSION-$ARCH \
	bash -c "
		set -x &&
		mkdir /build &&
		cp -r /src /build/xrdp-local-session-$version &&
		cd /build &&
		tar -czf xrdp-local-session_$version.orig.tar.gz xrdp-local-session-$version &&
		cd xrdp-local-session-$version &&
		dpkg-buildpackage -us -uc $deps_flags &&
		cd .. &&
		for x in *.*deb;
		do
			cp \"\$x\" \"/output/\$(echo \"\$x\" | sed -r \"s/(\\.d?deb)/.$DISTRO_NAME-$DISTRO_VERSION\\1/\")\" || exit 1
		done
	"
