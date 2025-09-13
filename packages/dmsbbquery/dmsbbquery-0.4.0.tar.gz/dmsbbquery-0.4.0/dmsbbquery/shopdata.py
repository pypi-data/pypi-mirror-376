"""
shopdata.py – Querying stock and pricing information from the DMS.

This module contains the `GetStockInformation` class which sends requests to the DMS Backbone
to retrieve spare part information such as stock levels, price, category, and storage location.

The class inherits from `DMSBackboneQuery` and implements the specific XML request
for the ShopData service.
"""


import xml.etree.ElementTree as ET
from dmsbbquery import DMSBackboneQuery


class GetStockInformation(DMSBackboneQuery):
    """
    Implements ShopData:GetStockInformation.

    Queries spare part stock availability, pricing, and metadata from the DMS system.

    Attributes:
        region (str): Region code.
        dealer (str): Dealer code.
        url (str): Full URL endpoint for the ShopData service.
    """

    def __init__(self, region: str, dealer: str, url: str):
        """
        Initializes the GetStockInformation query.

        Args:
            region (str): Region code.
            dealer (str): Dealer code.
            url (str): Base URL of the DMS server.
        """
        super().__init__(region, dealer, url, "ShopData.bb")

    def request(self, partnumber: str, brand_id: str = "V"):
        """
        Sends a request for stock and pricing information for a spare part.

        If the initial request returns no stock, a fallback request with brand_id "F" is sent.

        Args:
            partnumber (str): Spare part number.
            brand_id (str, optional): Brand identifier. Defaults to "V".

        Returns:
            int: HTTP status code of the response
        """
        response = self._send_request_and_parse(partnumber, brand_id)
        if not self._has_stock():
            response = self._send_fallback_request(partnumber)

        return response.status_code

    def _send_request_and_parse(self, partnumber: str, brand_id: str):
        """
        Sends a request with the given partnumber and brand_id, and parses the XML response.

        Args:
            partnumber (str): Spare part number.
            brand_id (str): Brand identifier.

        Returns:
            requests.Response: Response object from the request.
        """
        xml_payload = self.create_xml_payload(partnumber, brand_id)
        response = self.send_request(xml_payload)
        self._xml_root = ET.fromstring(response.text)
        self._error_code = self._get_text(".//EXCEPTION/ERROR/CODE")
        self._success = self._error_code is None
        return response

    def _has_stock(self):
        """
        Checks if the parsed XML response contains stock information.

        Returns:
            bool: True if stock information is available, False otherwise.
        """
        stocks = self._get_text(".//STOCKS")
        return stocks is not None

    def _send_fallback_request(self, partnumber: str):
        """
        Sends a fallback request with brand_id "F" if the initial request fails.

        Args:
            partnumber (str): Spare part number.

        Returns:
            requests.Response: Response object from the fallback request.
        """
        xml_payload = self.create_xml_payload(partnumber, brand_id="F")
        response = self.send_request(xml_payload)
        self._xml_root = ET.fromstring(response.text)
        return response

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

    @property
    def stock(self):
        """Returns the available stock amount."""
        return self._get_text(".//STOCKS", default="na")

    @property
    def invoice_text(self):
        """Returns the invoice text for the part."""
        return self._get_text(".//INVOICE_TEXT")

    @property
    def price(self):
        """Returns the price value of the part."""
        return self._get_text(".//PRICE")

    @property
    def currency(self):
        """Returns the currency for the price."""
        return self._get_attr(".//PRICE", "CURRENCY")

    @property
    def tax_rate(self):
        """Returns the tax rate for the part."""
        return self._get_attr(".//TAXCODE", "RATE")

    @property
    def category(self):
        """Returns the spare part category."""
        return self._get_text(".//SPAREPART_CATEGORY")

    @property
    def group(self):
        """Returns the spare part group."""
        return self._get_text(".//SPAREPART_GROUP")

    @property
    def store(self):
        """Returns the store identifier or description."""
        return self._get_text(".//STORE")

    def create_xml_payload(self, partnumber: str = None, brand_id: str = None) -> bytes:
        """
        Creates the XML payload for the GetStockInformation request.

        Args:
            partnumber (str): Spare part number.
            brand_id (str): Brand identifier.

        Returns:
            bytes: XML request as UTF-8 encoded bytes.
        """
        partnumber = partnumber.upper()
        message = ET.Element("MESSAGE", DTD="XMLMSG", VERSION="1.2.0.0")
        command = ET.SubElement(message, "COMMAND")
        request = ET.SubElement(
            command,
            "REQUEST",
            {
                "NAME": "GetStockInformation",
                "DTD": "ShopData",
                "VERSION": "1.1.1.0",
                "ID": self.dealer,
            },
        )
        params = [
            {"NAME": "COUNTRY_CODE", "VALUE": "DEU"},
            {"NAME": "REGION", "VALUE": self.region},
            {"NAME": "DEALER", "VALUE": self.dealer},
            {"NAME": "BRAND_ID", "VALUE": brand_id},
            {"NAME": "SPAREPART_NO", "VALUE": partnumber},
        ]
        for param in params:
            ET.SubElement(request, "PARAM", param)

        return ET.tostring(message, encoding="utf-8", xml_declaration=True)
