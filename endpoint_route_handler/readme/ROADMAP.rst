* add api docs helpers
* allow multiple HTTP methods on the same endpoint
* multiple values for route and methods

    keep the same in the ui for now, later own we can imagine a multi-value selection or just add text field w/ proper validation and cleanup

    remove the route field in the table of endpoint_route

    support a comma separated list of routes
    maybe support comma separated list of methods
    use only routing.routes for generating the rule
    sort and freeze its values to update the endpoint hash

    catch dup route exception on the sync to detect duplicated routes
    and use the endpoint_hash to retrieve the real record
    (note: we could store more info in the routing information which will stay in the map)

    for customizing the rule behavior the endpoint the hook is to override the registry lookup

    make EndpointRule class overridable on the registry

NOTE in v16 we won't care anymore about odoo controller
so the lookup of the controller can be simplified to a basic py obj that holds the routing info.
