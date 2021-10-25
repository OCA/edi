As a mixin
~~~~~~~~~~

Use standard Odoo inheritance::

    class MyModel(models.Model):
        _name = "my.model"
        _inherit = "endpoint.route.handler"

Once you have this, each `my.model` record will generate a route.
You can have a look at the `endpoint` module to see a real life example.


As a tool
~~~~~~~~~

Initialize non stored route handlers and generate routes from them.
For instance::

    route_handler = self.env["endpoint.route.handler"]
    endpoint_handler = MyController()._my_handler
    vals = {
        "name": "My custom route",
        "route": "/my/custom/route",
        "request_method": "GET",
        "auth_type": "public",
    }
    new_route = route_handler.new(vals)
    new_route._refresh_endpoint_data()  # required only for NewId records
    new_route._register_controller(endpoint_handler=endpoint_handler, key="my-custom-route")

Of course, what happens when the endpoint gets called
depends on the logic defined on the controller method.

In both cases (mixin and tool) when a new route is generated or an existing one is updated,
the `ir.http.routing_map` (which holds all Odoo controllers) will be updated.

You can see a real life example on `shopfloor.app` model.
