Install the weboob library (TODO: check that it works with the stable version weboob 1.3 and not just the development version weboob 1.4):

.. code::

  sudo pip install weboob

Some Weboob modules require additionnal Python libraries. For example, the `Weboob module for Bouygues Telecom <http://weboob.org/modules#mod_bouygues>`_ requires:

.. code::

  sudo pip install python-jose

Weboob requires `MuPDF <https://mupdf.com/>`_. If you use Debian/Ubuntu, run:

.. code::

  sudo apt install mupdf-tools
