"""
This module provides an interface to interact with the DMS Backbone server
using XML payloads. It defines the DummyInterface class, which extends the 
DMSBackboneQuery, to send requests and handle XML responses.

Dependencies:
    xml.etree.ElementTree: For parsing XML data.
    DMSBackboneQuery: Base class that provides the DMSBackboneQuery infrastructure.

Classes:
    DummyInterface: Extends DMSBackboneQuery to manage interactions with the DMS server.
"""
import xml.etree.ElementTree as ET
from dmsbbquery import DMSBackboneQuery


class DummyInterface(DMSBackboneQuery):
    """

    Attributes:
        region (str): Region code.
        dealer (str): Dealer code.
        url (str): Base Url of the DMS server.
        path (str): Specific path for the API endpoint on the DMS server.
    """

    def __init__(self, region: str, dealer: str, url: str, path: str):
        """
        Initializes the DummyInterface with region, dealer, base URL
        and path.

        Args:
            region (str): Region code.
            dealer (str): Dealer code.
            url (str): Base URL of the DMS server.
            path (str): Specific path for the API endpoint on the DMS server.
        """
        super().__init__(region, dealer, url, path)

    def request(self, xml_payload):
        """

        Args:

        Returns:
            requests.status_code

        Raises:
        """
        response = self.send_request(xml_payload)
        self._xml_root = ET.fromstring(response.text)

        return response.status_code

    def create_xml_payload(self):
        pass
