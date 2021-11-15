In order to create a new template type, we need to create a new module that adds a new
kind of component

.. code-block:: python

    class MyComponent(Component):
        _name = "component.name"
        _inherit = "edi.component.process_data.mixin"
        _process_type = "template type code"

        def process_data(self, data, template, file):
            "To implement what it should do"
