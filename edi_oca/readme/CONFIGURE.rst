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


Exchange type rules configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Exchange types can be further configured with rules.
You can use rules to:

1. make buttons automatically appear in forms
2. define your own custom logic

Go to an exchange type and go to the tab "Model rules".
There you can add one or more rule, one per model.
On each rule you can define a domain or a snippet to activate it.
In case of a "Form button" kind, if the domain and/ the snippet is/are satisfied,
a form btn will appear on the top of the form.
This button can be used by the end user to manually generate an exchange.
If there's more than a backend and the exchange type has not a backend set,
a wizard will appear asking to select a backend to be used for the exchange.

In case of "Custom" kind, you'll have to define your own logic to do something.
