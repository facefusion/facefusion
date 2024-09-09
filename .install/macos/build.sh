#!/bin/bash

VERSION='3.0.0'

rm facefusion_$VERSION.pkg
pkgbuild --root . --scripts . --identifier com.facefusion.installer --version $VERSION --install-location $HOME/FaceFusion facefusion_$VERSION.pkg
