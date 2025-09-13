"""
workshoporder.py – Querying workshop orders from the DMS Backbone.

This module provides the `GetOrder` and `ListOrder` classes to retrieve detailed
information about individual workshop orders as well as lists of all orders
for a given region and dealer.

Both classes inherit from `DMSBackboneQuery` and implement the respective
XML requests for the WorkshopOrder service.
"""


import xml.etree.ElementTree as ET
from dmsbbquery import DMSBackboneQuery


class GetOrder(DMSBackboneQuery):
    """
    Implements WorkshopOrder:GetOrder.

    Retrieves detailed information about a specific order by order number.

    Attributes:
        region (str): Region code.
        dealer (str): Dealer code.
        url (str): Full URL endpoint for the WorkshopOrder service.
    """

    def __init__(self, region: str, dealer: str, url: str):
        """
        Initializes the GetOrder query.

        Args:
            region (str): Region code.
            dealer (str): Dealer code.
            url (str): Base URL of the DMS server.
        """
        super().__init__(region, dealer, url, "WorkshopOrder.bb")

    def request(self, order_id: str):
        """
        Sends a request to retrieve order information by order number.

        Args:
            order_id (str): The order number.

        Returns:
            requests.status_code
        """
        xml_payload = self.create_xml_payload(order_id)
        response = self.send_request(xml_payload)
        self._xml_root = ET.fromstring(response.text)

        self._error_code = self._get_text(".//EXCEPTION/ERROR/CODE")
        if self._error_code is not None:
            self._success = False
            self._error_text = self._get_text(".//EXCEPTION/ERROR/TEXT")
        else:
            self._success = True

        return response.status_code

    @property
    def success(self) -> bool:
        """Returns True if the last request was successful."""
        return self._success

    @property
    def error_code(self):
        """Returns the error code from the last request, if any."""
        return self._get_text(".//EXCEPTION/ERROR/CODE")

    @property
    def error_text(self):
        """Returns the error description from the last request, if any."""
        return self._get_text(".//EXCEPTION/ERROR/TEXT")

    def create_xml_payload(self, order_id: str) -> bytes:
        """
        Creates the XML payload for the GetOrder request.

        Args:
            order_id (str): The order number.

        Returns:
            bytes: XML request as UTF-8 encoded bytes.
        """
        message = ET.Element("MESSAGE", DTD="XMLMSG", VERSION="1.2.0.0")
        command = ET.SubElement(message, "COMMAND")
        request = ET.SubElement(
            command,
            "REQUEST",
            {
                "NAME": "GetOrder",
                "DTD": "WorkshopOrder",
                "VERSION": "1.1.1.0",
                "ID": "0",
            },
        )
        params = [
            {"NAME": "COUNTRY_CODE", "VALUE": "DEU"},
            {"NAME": "REGION", "VALUE": self.region},
            {"NAME": "DEALER", "VALUE": self.dealer},
            {"NAME": "ORDER_NO", "VALUE": order_id},
        ]
        for param in params:
            ET.SubElement(request, "PARAM", param)

        return ET.tostring(message, encoding="utf-8", xml_declaration=True)


class ListOrder(DMSBackboneQuery):
    """
    Implements WorkshopOrder:ListOrder.

    Retrieves a list of all orders for the given region and dealer.

    Attributes:
        region (str): Region code.
        dealer (str): Dealer code.
        url (str): Full URL endpoint for the WorkshopOrder service.
    """

    def __init__(self, region: str, dealer: str, url: str):
        """
        Initializes the ListOrder query and immediately sends the request.

        Args:
            region (str): Region code.
            dealer (str): Dealer code.
            url (str): Base URL of the DMS server.
        """
        super().__init__(region, dealer, url, "WorkshopOrder.bb")
        xml_payload = self.create_xml_payload()
        response = self.send_request(xml_payload)
        self._xml_root = ET.fromstring(response.text)

    def get_order_numbers(self) -> list[str]:
        """
        Retrieves a list of all order numbers from the response.

        Returns:
            List[str]: List of order numbers.
        """
        return [
            elem.text.strip()
            for elem in self._xml_root.findall(".//ORDER/ORDER_NO")
            if elem is not None and elem.text
        ]

    def create_xml_payload(self) -> bytes:
        """
        Creates the XML payload for the ListOrder request.

        Returns:
            bytes: XML request as UTF-8 encoded bytes.
        """
        message = ET.Element("MESSAGE", DTD="XMLMSG", VERSION="1.2.0.0")
        command = ET.SubElement(message, "COMMAND")
        request = ET.SubElement(
            command,
            "REQUEST",
            {
                "NAME": "ListOrder",
                "DTD": "WorkshopOrder",
                "VERSION": "1.4.0.0",
                "ID": "0",
            },
        )
        params = [
            {"NAME": "COUNTRY_CODE", "VALUE": "DEU"},
            {"NAME": "REGION", "VALUE": self.region},
            {"NAME": "DEALER", "VALUE": self.dealer},
        ]
        for param in params:
            ET.SubElement(request, "PARAM", param)

        return ET.tostring(message, encoding="utf-8", xml_declaration=True)
