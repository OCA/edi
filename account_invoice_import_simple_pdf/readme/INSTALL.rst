The most important technical component of this module is the tool that converts the PDF to text. Converting PDF to text is not an easy job. As outlined in this `blog post <https://dida.do/blog/how-to-extract-text-from-pdf>`_, different tools can give quite different results. The best results are usually achieved with tools based on a PDF viewer, which exclude pure-python tools. But pure-python tools are easier to install than tools based on a PDF viewer. It is important to understand that, if you change the PDF to text tool, you will certainly have a slightly different text output, which may oblige you to update the field extraction rule, which can be time-consuming if you have already configured many vendors.

The module supports 5 different extraction methods:

1. `PyMuPDF <https://github.com/pymupdf/PyMuPDF>`_ which is a Python binding for `MuPDF <https://mupdf.com/>`_, a lightweight PDF toolkit/viewer/renderer published under the AGPL licence by the company `Artifex Software <https://artifex.com/>`_.
#. `pdftotext python library <https://pypi.org/project/pdftotext/>`_, which is a python binding for the pdftotext tool.
#. `pdftotext command line tool <https://en.wikipedia.org/wiki/Pdftotext>`_, which is based on `poppler <https://poppler.freedesktop.org/>`_, a PDF rendering library used by `xpdf <https://www.xpdfreader.com/>`_ and `Evince <https://wiki.gnome.org/Apps/Evince/FrequentlyAskedQuestions>`_ (the PDF reader of `Gnome <https://www.gnome.org/>`_).
#. `pdfplumber <https://pypi.org/project/pdfplumber/>`_, which is a python library built on top the of the python library `pdfminer.six <https://pypi.org/project/pdfminer.six/>`_. pdfplumber is a pure-python solution, so it's very easy to install on all OSes.
#. `pypdf <https://github.com/py-pdf/pypdf/>`_, which is one of the most common PDF lib for Python. pypdf is a pure-python solution, so it's very easy to install on all OSes.

PyMuPDF and pdftotext both give a very good text output. So far, I can't say which one is best. pdfplumber and pypdf often give lower-quality text output, but their advantage is that they are pure-Python librairies, so you will always be able to install it whatever your technical environnement is.

You can choose one extraction method and only install the tools/libs for that method.

Install PyMuPDF
~~~~~~~~~~~~~~~

Install it via pip:

.. code::

  sudo pip3 install --upgrade pymupdf

Beware that *PyMuPDF* is not a pure-python library: it uses MuPDF, which is written in C language. If a python wheel for your OS, CPU architecture and Python version is available on pypi (check the `list of PyMuPDF wheels <https://pypi.org/project/PyMuPDF/#files>`_ on pypi), it will install smoothly. Otherwize, the installation via pip will require MuPDF and all its development libs to compile the binding.

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

Install pypdf
~~~~~~~~~~~~~

To install the **pypdf** python lib, run:

.. code::

  sudo pip3 install --upgrade pypdf


Other requirements
~~~~~~~~~~~~~~~~~~

This module also requires the following Python libraries:

* `regex <https://pypi.org/project/regex/>`_ which is backward-compatible with the *re* module of the Python standard library, but has additional functionalities.
* `dateparser <https://github.com/scrapinghub/dateparser>`_ which is a powerful date parsing library.

The dateparser lib depends itself on regex. So you can install these Python libraries via pip with the following command:

.. code::

  sudo pip3 install --upgrade dateparser

The dateparser lib is not compatible with all regex lib versions. As of September 2022, the `version requirement <https://github.com/scrapinghub/dateparser/blob/master/setup.py#L30>`_ declared by dateparser for regex is **!=2019.02.19, !=2021.8.27, <2022.3.15**. So the latest version of regex which is compatible with dateparser is **2022.3.2**. To know the version of regex installed in your environment, run:


.. code::

  sudo pip3 show regex

To force regex to version 2022.3.2, run:

.. code::

  sudo pip3 install regex==2022.3.2
