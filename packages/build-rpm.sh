#!/bin/bash

set -e
set -x

DISTRO="$1"
ARCH="$2"
DISTRO_NAME="${DISTRO%%-*}"
DISTRO_VERSION="${DISTRO#*-}"

case $DISTRO_NAME in
	fedora) DISTRO_SHORTNAME=fc ;;
	*)
		echo "Unknown distro $DISTRO_NAME."
		exit 1
		;;
esac

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
	--platform linux/$ARCH \
	-v $PWD/..:/src \
	-v $PWD/output:/output \
	builder-$DISTRO_NAME-$DISTRO_VERSION-$ARCH \
	bash -c "
		set -x &&
		mkdir -p /build /root/rpmbuild/SOURCES /root/rpmbuild/SPECS &&
		cp -r /src /build/xrdp-local-session-$version &&
		cp /src/xrdp-local-session.spec /root/rpmbuild/SPECS/ &&
		cd /build &&
		cat /build/xrdp-local-session-$version/xrdp_local_session/common/xrdp.py &&
		tar -czf /root/rpmbuild/SOURCES/xrdp-local-session-$version.tar.gz xrdp-local-session-$version &&
		cd /root/rpmbuild/SPECS &&
		rpmbuild -bb xrdp-local-session.spec &&
		cp /root/rpmbuild/RPMS/*/*.rpm /output/
	"
