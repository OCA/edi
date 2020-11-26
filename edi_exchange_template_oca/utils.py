from lxml import etree

from odoo.tools import pycompat


def xml_purge_nswrapper(xml_content):
    """Purge `nswrapper` elements.

    QWeb template does not allow parsing namespaced elements
    without declaring namespaces on the root element.

    Hence, by default you cannot define smaller re-usable templates
    if the have namespaced elements.

    The trick is to wrap your reusable template with `nswrapper` element
    which holds the namespace for that particular sub template.
    For instance:

        <nswrapper xmlns:foo="http://www.unece.org/cefact/Foo">
            <foo:LovelyNamespacedElement />
        </nswrapper>

    Then this method is going to purge these unwanted elements from the result.
    """
    if not (xml_content and xml_content.strip()):
        return xml_content
    root = etree.XML(xml_content)
    # deeper elements come after, keep the root element at the end (if any)
    for nswrapper in reversed(root.xpath("//nswrapper")):
        parent = nswrapper.getparent()
        if parent is None:
            # fmt:off
            return "".join([
                pycompat.to_text(etree.tostring(el))
                for el in nswrapper.getchildren()
            ])
            # fmt:on
        parent.extend(nswrapper.getchildren())
        parent.remove(nswrapper)
    return etree.tostring(root)
