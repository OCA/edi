from odoo.tools.misc import wrap_module

json = wrap_module(__import__("json"), ["loads", "dumps"])
