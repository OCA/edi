"""
Converts a Python dictionary to a valid XML string

https://github.com/watzon/xmler Slightly modified and adapted for py3.

TODO: project seems dead but it's very small and shall be easy to maintain.
Decide if we want to keep it here or contribute back.
"""

from xml.dom import minidom
from xml.etree.ElementTree import Element, tostring

__version__ = "0.2.0"
version = __version__


def dict2xml(input_dict, encoding="utf-8", pretty=False):
    """Converts a python dictionary into a valid XML string

    Args:
        - encoding specifies the encoding to be included in the encoding
          segment. If set to False no encoding segment will be displayed.
        - customRoot defines the tag to wrap the returned output. Can be
          a string, dictionary, or False if no custom root is to be used.

    Returns:
        A XML formatted string representing the dictionary.

    Examples:
        ```
        dic = {
            "Envelope": {
                "@ns": "soapenv",
                "@attrs": {
                    "xmlns:soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
                    "xmlns:urn": "urn:partner.soap.sforce.com"
                },
                "Header": {
                    "@ns": "soapenv",
                    "SessionHeader": {
                        "@ns": "urn",
                        "sessionId": {
                            "@ns": "urn",
                            "@value": "00D36000000b28L!ARsAQMtHo4XD71VYRxoz"
                        }
                    }
                },
                "Body": {
                    "@ns": "soapenv",
                    "query": {
                        "@ns": "urn",
                        "queryString": {
                            "@ns": "urn",
                            "@value": "SELECT Id, Name FROM Account LIMIT 2"
                        }
                    }
                }
            }
        }

        xml = xml2dict(dict, customRoot=False)
        print(xml)
        ```

        output:
        ```
        <?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
          xmlns:urn="urn:partner.soap.sforce.com">
          <soapenv:Header>
             <urn:SessionHeader>
                <urn:sessionId>{0}</urn:sessionId>
             </urn:SessionHeader>
          </soapenv:Header>
        </soapenv:Envelope>
        ```
    """

    xml_string = tostring(parse(input_dict, pretty=pretty), encoding=encoding)

    if pretty:
        xml_pretty_string = minidom.parseString(xml_string)
        return xml_pretty_string.toprettyxml().decode(encoding)
    else:
        return xml_string.decode(encoding)


def parse(input_dict, parent=None, pretty=False):
    parent = parent or {}
    for key, value in input_dict.items():

        if isinstance(value, (float, int)):
            # Enfoce strings here
            value = str(value)

        parent["name"] = key
        parent["value"] = value

        if isinstance(value, dict):
            if "@ns" in value:
                parent["namespace"] = value.pop("@ns", None)

            if "@attrs" in value:
                parent["attributes"] = value.pop("@attrs", None)

            if "@name" in value:
                parent["name"] = value.pop("@name", None)

            if "@value" in value:
                val = value["@value"]
                if isinstance(val, (float, int)):
                    # Enfoce strings here
                    val = str(val)
                parent["value"] = value = val

    if "namespace" in parent:
        parent["name"] = "{}:{}".format(parent["namespace"], parent["name"])

    if "attributes" in parent:
        element = Element(parent["name"], parent["attributes"])
    else:
        element = Element(parent["name"])

    if isinstance(parent["value"], dict):
        for child_key, child_value in parent["value"].items():
            element.append(parse({child_key: child_value}, parent={}))

    elif isinstance(parent["value"], (list, set, tuple)):
        for child in parent["value"]:
            element.append(parse(child, parent={}))

    else:
        element.text = parent["value"]

    return element
