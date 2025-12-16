# Maintainer: Shaul Kremer <shaulk@users.noreply.github.com>

pkgname=xrdp-local-session
pkgver=0.1.1
pkgrel=1
pkgdesc="Local client for xrdp providing seamless switching between local and RDP connections - core"
url="https://github.com/shaulk/xrdp_local_session"
arch=(any)
license=('Apache-2.0')
makedepends=('python')
depends=('python' 'python-typer' 'python-psutil' 'python-dbus' 'python-pydantic')
source=("xrdp-local-session.tar.gz")
sha256sums=('SKIP')

prepare() {
  true
}

build() {
  true
}

package() {
  cd "${pkgname}"
  python3 setup.py install --prefix=/usr --root="${pkgdir}"
  mkdir -p "${pkgdir}/usr/share/xsessions/"
  cp xrdp-local-session.desktop "${pkgdir}/usr/share/xsessions/"
  mkdir -p "${pkgdir}/usr/share/doc/${pkgname}/"
  cp README.md "${pkgdir}/usr/share/doc/${pkgname}/"
}
