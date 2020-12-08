This module aims to provide an infrastructure to simplify interchangability of documents
between systems providing a configuration platform.
It will be inherited by other modules in order to define the proper implementations of
components.

In order to define a new Exchange Record, we need to configure:

* Backend Type
* Exchange Type
* Backend
* Components

Component definition
~~~~~~~~~~~~~~~~~~~~

The component usage must be defined like `edi.{direction}.{kind}.{code}` where:

* direction is `output` or `input`
* kind can be: `generate`, `send`, `check`, `process`, `receive`
* code is the `{backend type code}` or `{backend type code}.{exchange type code}`

User EDI generation
~~~~~~~~~~~~~~~~~~~

On the exchange type, it might be possible to define a set of models, a domain and a
snippet of code.
After defining this fields, we will automatically see buttons on the view to generate
the exchange records.
This configuration is useful to define a way of generation managed by user.
