The most important technical component of this module is the tool that converts the PDF to text. Converting PDF to text is not an easy job. As outlined in this `blog post <https://dida.do/blog/how-to-extract-text-from-pdf>`_, different tools can give quite different results. The best results are usually achieved with tools based on a PDF viewer, which exclude pure-python tools. But pure-python tools are easier to install than tools based on a PDF viewer. It is important to understand that, if you change the PDF to text tool, you will certainly have a slightly different text output, which may oblige you to update the field extraction rule, which can be time-consuming if you have already configured many vendors.

The module supports 4 different extraction methods:

1. `PyMuPDF <https://github.com/pymupdf/PyMuPDF>`_ which is a Python binding for `MuPDF <https://mupdf.com/>`_, a lightweight PDF toolkit/viewer/renderer published under the AGPL licence by the company `Artifex Software <https://artifex.com/>`_.
#. `pdftotext python library <https://pypi.org/project/pdftotext/>`_, which is a python binding for the pdftotext tool.
#. `pdftotext command line tool <https://en.wikipedia.org/wiki/Pdftotext>`_, which is based on `poppler <https://poppler.freedesktop.org/>`_, a PDF rendering library used by `xpdf <https://www.xpdfreader.com/>`_ and `Evince <https://wiki.gnome.org/Apps/Evince/FrequentlyAskedQuestions>`_ (the PDF reader of `Gnome <https://www.gnome.org/>`_).
#. `pdfplumber <https://pypi.org/project/pdfplumber/>`_, which is a python library built on top the of the python library `pdfminer.six <https://pypi.org/project/pdfminer.six/>`_. pdfplumber is a pure-python solution, so it's very easy to install on all OSes.

PyMuPDF and pdftotext both give a very good text output. So far, I can't say which one is best. pdfplumber often gives lower-quality text output, but its advantage is that it's a pure-Python solution, so you will always be able to install it whatever your technical environnement is.

You can choose one extraction method and only install the tools/libs for that method.

Install PyMuPDF
~~~~~~~~~~~~~~~

To install **PyMuPDF**, if you use Debian (Bullseye aka v11 or higher) or Ubuntu (20.04 or higher), run the following command:

.. code::

  sudo apt install python3-fitz

You can also install it via pip:

.. code::

  sudo pip3 install --upgrade PyMuPDF


but beware that *PyMuPDF* is just a binding on MuPDF, so it will require MuPDF and all the development libs required to compile the binding. That's why *PyMuPDF* is much easier to install via the packages of your Linux distribution (package name **python3-fitz** on Debian/Ubuntu, but the package name may be different in other distributions) than with pip.

Install pdftotext python lib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install **pdftotext python lib**, run:

.. code::

  sudo apt install build-essential libpoppler-cpp-dev pkg-config python3-dev

and then install the lib via pip:

.. code::

  sudo pip3 install --upgrade pdftotext

On OSes other than Debian/Ubuntu, follow the instructions on the `project page <https://github.com/jalan/pdftotext>`_.

Install pdftotext command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install **pdftotext command line**, run:

.. code::

  sudo apt install poppler-utils

Install pdfplumber
~~~~~~~~~~~~~~~~~~

To install the **pdfplumber** python lib, run:

.. code::

  sudo pip3 install --upgrade pdfplumber

Other requirements
~~~~~~~~~~~~~~~~~~

This module also requires the following Python libraries:

* `regex <https://pypi.org/project/regex/>`_ which is backward-compatible with the *re* module of the Python standard library, but has additional functionalities.
* `dateparser <https://github.com/scrapinghub/dateparser>`_ which is a powerful date parsing library.

You can install these Python libraries via pip:

.. code::

  sudo pip3 install --upgrade regex dateparser
