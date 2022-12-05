ID numbers selection
~~~~~~~~~~~~~~~~~~~~

On the exchange type form, find the field "ID categories"
and set the categories allowed for that exchange type.

If not set, *all the IDs* of the partner will be exposed.

Name field
~~~~~~~~~~

On the exchange type form, modify the advanced settings
so that the work context of the component that is used (eg: generate)
contains `party_data_name_field`. For instance::

    components:
        generate:
            usage: my.generate
            work_ctx:
                party_data_name_field: name
