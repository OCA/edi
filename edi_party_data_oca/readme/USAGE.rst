An handy util method is to retrive the component::

    from odoo.addons.edi_party_data_oca.utils import get_party_data_component

    component = get_party_data_component(exchange_record, partner)

    data = component.get_party()
