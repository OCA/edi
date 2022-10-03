Go to "EDI -> Config -> Backends" and edit or create one.
Find the tab "Webservice" and add a webservice.
On the webservice record you can specify all the general parameters to connect to the service
(see `webservice` README for more details).

If you want to take full control on if/how the webservice is used
you can do it via exchange type's advanced settings.

Hence, assuming your webservice has a URL configured as `https://my.endpoint/{path}`::

  components:
    send:
      usage: webservice.send  # or any custom component usage inheriting from this
      work_ctx:
        webservice:
          method: post  # mandatory
          url_params:
            path: endpoint1/foo


For each call related to this type, you'll get a POST request against
`https://my.endpoint/endpoint/foo`.

``url_params`` can contain all the keys need for URL interpolation.

In addition, you can user ``url`` to override the full url used for the call
per exchange type.

If you want to send data as bytes you can use the option `send_as_bytes` like::

  [...]
        webservice:
          send_as_bytes: true
  [...]
