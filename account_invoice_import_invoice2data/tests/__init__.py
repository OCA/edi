# -*- coding: utf-8 -*-

# The test below works well, but the full installation of invoice2data
# with the special version of the pdftotext binary is difficult
# Invoice2data new requires a recent version of poppler-utils
# from https://poppler.freedesktop.org/releases.html
# But Travis build environnement are based on Ubuntu 12.04 and I didn't
# find any PPA for poppler-utils for 12.04 and it doesn't seem easy to have a
# static build
#from . import test_invoice_import
