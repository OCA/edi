As a mixin
~~~~~~~~~~

Use standard Odoo inheritance::

    class MyModel(models.Model):
        _name = "my.model"
        _inherit = "endpoint.route.handler"

Once you have this, each `my.model` record will generate a route.
You can have a look at the `endpoint` module to see a real life example.

The options of the routing rules are defined by the method `_default_endpoint_options`.
Here's an example from the `endpoint` module::

    def _default_endpoint_options_handler(self):
        return {
            "klass_dotted_path": "odoo.addons.endpoint.controllers.main.EndpointController",
            "method_name": "auto_endpoint",
            "default_pargs": (self.route,),
        }

As you can see, you have to pass the references to the controller class and the method to use
when the endpoint is called. And you can prepare some default arguments to pass.
In this case, the route of the current record.


As a tool
~~~~~~~~~

Initialize non stored route handlers and generate routes from them.
For instance::

    route_handler = self.env["endpoint.route.handler.tool"]
    endpoint_handler = MyController()._my_handler
    vals = {
        "name": "My custom route",
        "route": "/my/custom/route",
        "request_method": "GET",
        "auth_type": "public",
    }
    new_route = route_handler.new(vals)
    new_route._register_controller()

You can override options and define - for instance - a different controller method::

    options = {
        "handler": {
            "klass_dotted_path": "odoo.addons.my_module.controllers.SpecialController",
            "method_name": "my_special_handler",
        }
    }
    new_route._register_controller(options=options)

Of course, what happens when the endpoint gets called
depends on the logic defined on the controller method.

In both cases (mixin and tool) when a new route is generated or an existing one is updated,
the `ir.http.routing_map` (which holds all Odoo controllers) will be updated.

You can see a real life example on `shopfloor.app` model.
