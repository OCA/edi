Provide unified way to handle external webservices configuration and calls.

Each external webservice is represented - and configured - by a `webservice.backend` record.
The handling of the requests is delegated to adapters (special components).
At the moment, the only protocol supported by directly by this module is `HTTP`.

Additional protocols can be easily supported by adding more adapters.

Nevertheless, no matter which protocol you'll use,
technically you'll have to always issue calls from the backend object.
Eg:

    my_backend.call("GET", "any/endpoint")
    my_backend.call("POST", "any/endpoint")
