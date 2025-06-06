# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


import requests
from lxml import etree as ElementTree
from markupsafe import Markup

from odoo.addons.component.core import Component


class EdiversaApi(Component):
    _name = "ediversa.api"
    _usage = "ediversa.api"
    _backend_type = "ediversa"
    _inherit = "edi.component.mixin"

    def send_request(self, msg, test=False):
        param = (
            "edi_ediversa_oca.api_url" if not test else "edi_ediversa_oca.api_url_test"
        )
        url = self.env["ir.config_parameter"].get_param(param, False)
        try:
            r = requests.post(url, data=msg, timeout=20)
            response = r.content
        except Exception:
            response = "error"
        return response

    def get_documents(self, company):
        env = "comedicloudws" if not company.edi_ediversa_test else "comedicloudwstest"
        msg = Markup(
            f"""<soapenv:Envelope
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:com="{env}">
    <soapenv:Header/>
    <soapenv:Body>
        <com:downloadDocumentListExtended soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
            <user xsi:type="xsd:string">{company.edi_ediversa_user}</user>
            <password xsi:type="xsd:string">{company.edi_ediversa_password}</password>
        </com:downloadDocumentListExtended>
    </soapenv:Body>
</soapenv:Envelope>"""
        )
        response = self.send_request(msg, company.edi_ediversa_test)
        namespaces = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "a": env,
        }
        tree = ElementTree.fromstring(response)
        docs = tree.findall(
            "./soap:Body"
            "/a:downloadDocumentListExtendedResponse"
            "/a:result"
            "/a:documents"
            "/a:document",
            namespaces,
        )
        return docs

    def download_document(self, identifier, company):
        env = "comedicloudws" if not company.edi_ediversa_test else "comedicloudwstest"
        msg = Markup(
            f"""<soapenv:Envelope
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:com="{env}">
    <soapenv:Header/>
    <soapenv:Body>
        <com:downloadDocument soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
            <user xsi:type="xsd:string">{company.edi_ediversa_user}</user>
            <password xsi:type="xsd:string">{company.edi_ediversa_password}</password>
            <identifier xsi:type="xsd:string">{identifier}</identifier>
        </com:downloadDocument>
    </soapenv:Body>
</soapenv:Envelope>"""
        )
        response = self.send_request(msg, company.edi_ediversa_test)
        namespaces = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "a": env,
        }
        tree = ElementTree.fromstring(response)
        doc = tree.find("./soap:Body" "//a:content", namespaces)
        return doc

    def confirm_document_download(self, identifier, company):
        env = "comedicloudws" if not company.edi_ediversa_test else "comedicloudwstest"
        msg = Markup(
            f"""<soapenv:Envelope
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:com="{env}">
    <soapenv:Header/><soapenv:Body>
        <com:confirmDocumentDownload soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
            <user xsi:type="xsd:string">{company.edi_ediversa_user}</user>
            <password xsi:type="xsd:string">{company.edi_ediversa_password}</password>
            <identifier xsi:type="xsd:string">{identifier}</identifier>
        </com:confirmDocumentDownload>
    </soapenv:Body>
</soapenv:Envelope>"""
        )
        self.send_request(msg, company.edi_ediversa_test)
        return True

    def send_document(self, filename, file, company):
        env = "comedicloudws" if not company.edi_ediversa_test else "comedicloudwstest"
        msg = Markup(
            f"""<soapenv:Envelope
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:com="{env}">
    <soapenv:Header/><soapenv:Body>
        <com:uploadDocument soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
            <user xsi:type="xsd:string">{company.edi_ediversa_user}</user>
            <password xsi:type="xsd:string">{company.edi_ediversa_password}</password>
            <filename xsi:type="xsd:string">{filename}</filename>
            <file xsi:type="xsd:string">{file.decode()}</file>
        </com:uploadDocument>
    </soapenv:Body>
</soapenv:Envelope>"""
        )
        response = self.send_request(msg, company.edi_ediversa_test)
        namespaces = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "a": env,
        }
        tree = ElementTree.fromstring(response)
        docs = tree.find(
            "./soap:Body"
            "/a:uploadDocumentResponse"
            "/a:result"
            "/a:internal_identifier",
            namespaces,
        )
        return docs.text
