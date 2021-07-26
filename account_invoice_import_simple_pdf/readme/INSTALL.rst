This module requires several Python libraries:

* `PyMuPDF <https://github.com/pymupdf/PyMuPDF>`_ which is a Python binding for `MuPDF <https://mupdf.com/>`_, a lightweight PDF toolkit/viewer/renderer published under the AGPL licence by the company `Artifex Software <https://artifex.com/>`_
* `regex <https://pypi.org/project/regex/>`_ which is backward-compatible with the *re* module of the Python standard library, but has additional functionalities.
* `dateparser <https://github.com/scrapinghub/dateparser>`_ which is a powerful date parsing library.

If you use Debian (Bullseye or higher) or Ubuntu (20.04 or higher), run the following command:

.. code::

  sudo apt install python3-fitz python3-regex python3-dateparser

You can also install these Python librairies via pip:

.. code::

  sudo pip3 install --upgrade PyMuPDF regex dateparser

but beware that *PyMuPDF* is just a binding on MuPDF, so it will require MuPDF and all the development libs required to compile the binding. So, for *PyMuPDF*, it's much easier to install it via the packages of your Linux distribution (package name **python3-fitz** on Debian/Ubuntu, but the package name may be different in other distributions).
