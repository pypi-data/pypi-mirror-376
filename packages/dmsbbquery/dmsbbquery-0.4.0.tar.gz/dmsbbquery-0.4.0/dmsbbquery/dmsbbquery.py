"""
dmsbbquery.py – Base class and interface for DMS Backbone XML queries.

This module defines the abstract base class `DMSBackboneQuery` for constructing,
sending, and processing XML-based HTTP requests to the DMS Backbone system.

Classes:
    - DMSBackboneQuery: Abstract base class for shared XML request logic.
    - AliveTest: Sends a simple request to check backend availability.
"""


import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from xml.dom import minidom
import requests


class DMSBackboneQuery(ABC):
    """
    Abstract base class for DMS Backbone queries.

    Provides utility methods for sending and parsing XML-based HTTP requests,
    and for safely extracting data from the XML responses.

    Attributes:
        region (str): Region code.
        dealer (str): Dealer code.
        url (str): Full URL endpoint for the DMS service.
    """

    def __init__(self, region: str, dealer: str, url: str, path: str):
        """
        Initializes the query with region, dealer, and full URL.

        Args:
            region (str): Region code.
            dealer (str): Dealer code.
            url (str): Base URL of the DMS server.
            path (str): URI path for the specific service.
        """
        self.region = region
        self.dealer = dealer
        self.url = url.rstrip("/") + "/" + path.lstrip("/")
        self._success = False
        self._error_code = None
        self._error_text = None
        self._xml_root = None

    @abstractmethod
    def create_xml_payload(self, *args, **kwargs) -> bytes:
        """
        Abstract method that must return the XML payload to send.

        Returns:
            bytes: The XML request as a byte string.
        """
        pass  # pylint: disable=unnecessary-pass

    def send_request(self, xml_payload: bytes) -> requests.Response:
        """
        Sends the XML payload to the DMS Backbone server.

        Args:
            xml_payload (bytes): The XML request.

        Returns:
            requests.Response: The HTTP response object.

        Raises:
            RuntimeError: If the request fails.
        """
        headers = {
            "Content-Type": "text/xml",
            "charset": "UTF-8",
            "Accept": "application/xml",
        }
        try:
            response = requests.post(self.url, data=xml_payload, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError("Failed to send request to the DMS Backbone") from e
        return response

    def prettify_xml(self, xml_data: bytes) -> str:
        """
        Formats raw XML into a human-readable string.

        Args:
            xml_data (bytes): Raw XML byte string.

        Returns:
            str: Prettified XML string.
        """
        dom = minidom.parseString(xml_data)
        pretty_xml = dom.toprettyxml(indent="    ")
        lines = pretty_xml.split("\n")
        cleaned_lines = [line for line in lines if line.strip()]
        return "\n".join(cleaned_lines)

    def rawout(self) -> str:
        """
        Returns the formatted XML response from the last query.

        Returns:
            str: Prettified XML response.
        """
        xml_bytestr = ET.tostring(self._xml_root, encoding="utf-8")
        return self.prettify_xml(xml_bytestr)

    def _get_text(self, path: str, default=None):
        """
        Safely retrieves the text content of an XML element.

        Args:
            path (str): XPath-like path.
            default (Any, optional): Fallback if element or text is missing.

        Returns:
            str or Any: Text value or default.
        """
        node = self._xml_root.find(path)
        return node.text.strip() if node is not None and node.text else default

    def _get_attr(self, path: str, attr: str, default=None):
        """
        Safely retrieves an attribute from an XML element.

        Args:
            path (str): XPath-like path.
            attr (str): Attribute name.
            default (Any, optional): Fallback if attribute is missing.

        Returns:
            str or Any: Attribute value or default.
        """
        node = self._xml_root.find(path)
        return node.attrib.get(attr) if node is not None else default


class AliveTest(DMSBackboneQuery):
    """
    Implements DMSBackbone:AliveTest. A request to check backend availability.
    """

    def __init__(self, url: str, path: str = "DMSBackbone.bb"):
        """
        Initializes the AliveTest request and fetches the XML response.

        Args:
            url (str): Base URL of the DMS server.
            path (str, optional): The URI to call. Defaults to "WorkshopOrder.bb".
        """
        super().__init__(region="", dealer="", url=url, path=path)
        xml_payload = self.create_xml_payload()
        response = self.send_request(xml_payload)
        self._xml_root = ET.fromstring(response.text)

    def create_xml_payload(self) -> bytes:
        """
        Constructs the AliveTest XML request.

        Returns:
            bytes: The XML request as a byte string.
        """
        message = ET.Element("MESSAGE", DTD="XMLMSG", VERSION="1.2.0.0")
        command = ET.SubElement(message, "COMMAND")
        ET.SubElement(
            command,
            "REQUEST",
            {
                "NAME": "AliveTest",
                "DTD": "DMSBackbone",
                "VERSION": "1.1.1.0",
                "ID": "0",
            },
        )
        return ET.tostring(message, encoding="utf-8", xml_declaration=True)
