"""
businesspartnerdata.py – Querying business partner data from the DMS Backbone.

This module contains the `GetEntry` class which sends requests to the DMS Backbone
to retrieve customer (business partner) information.

The class builds XML requests with various search parameters (name, account number,
matchcode) and processes the XML responses.

It depends on the base class `DMSBackboneQuery` from the `dmsbbquery` module.
"""


import xml.etree.ElementTree as ET
from dmsbbquery import DMSBackboneQuery


class GetEntry(DMSBackboneQuery):
    """
    Implements BusinessPartnerData:GetEntry.

    This class sends queries to retrieve customer (business partner) information
    from the DMS Backbone system.

    Attributes:
        region (str): Region code.
        dealer (str): Dealer code.
        url (str): Full URL endpoint for the BusinessPartnerData service.
    """

    def __init__(self, region: str, dealer: str, url: str):
        """
        Initializes the GetEntry query with region, dealer, and base URL.

        Args:
            region (str): Region code.
            dealer (str): Dealer code.
            url (str): Base URL of the DMS server.
        """
        super().__init__(region, dealer, url, "BusinessPartnerData.bb")

    def request(
        self,
        first_name: str = "",
        last_name: str = "",
        account_no: str = "",
        matchcode: str = "",
    ):
        """
        Sends a request to retrieve customer information and parses the XML response.

        Args:
            first_name (str, optional): Customer's first name. Defaults to "".
            last_name (str, optional): Customer's last name. Defaults to "".
            account_no (str, optional): Customer account number. Defaults to "".
            matchcode (str, optional): Matchcode for customer search. Defaults to "".

        Returns:
            requests.status_code

        Raises:
            ValueError: If all search parameters are empty.
        """
        if not (first_name or last_name or account_no or matchcode):
            raise ValueError(
                "At least one search parameter must be provided: "
                "first_name, last_name, account_no, or matchcode."
            )

        xml_payload = self.create_xml_payload(
            first_name=first_name,
            last_name=last_name,
            account_no=account_no,
            matchcode=matchcode,
        )
        response = self.send_request(xml_payload)
        self._xml_root = ET.fromstring(response.text)

        return response.status_code

    def create_xml_payload(
        self,
        first_name: str = "",
        last_name: str = "",
        account_no: str = "",
        matchcode: str = "",
    ) -> bytes:
        """
        Creates the XML payload for the GetEntry request.

        Args:
            first_name (str): Customer's first name.
            last_name (str): Customer's last name.
            account_no (str): Customer account number.
            matchcode (str): Matchcode for customer search.

        Returns:
            bytes: XML payload as a UTF-8 encoded byte string.
        """
        message = ET.Element("MESSAGE", DTD="XMLMSG", VERSION="1.2.0.0")
        command = ET.SubElement(message, "COMMAND")
        request = ET.SubElement(
            command,
            "REQUEST",
            {
                "NAME": "GetEntry",
                "DTD": "BusinessPartnerData",
                "VERSION": "1.2.1.0",
                "ID": self.dealer,
            },
        )
        params = [
            {"NAME": "COUNTRY_CODE", "VALUE": "DEU"},
            {"NAME": "REGION", "VALUE": self.region},
            {"NAME": "DEALER", "VALUE": self.dealer},
            {"NAME": "LAST", "VALUE": last_name},
            {"NAME": "FIRST", "VALUE": first_name},
            {"NAME": "ACCOUNT_NO", "VALUE": account_no},
            {"NAME": "MATCHCODE", "VALUE": matchcode},
        ]
        for param in params:
            ET.SubElement(request, "PARAM", param)

        return ET.tostring(message, encoding="utf-8", xml_declaration=True)

    def bp_list(self):
        """
        Extracts a list of business partners with their account number, first name, last name, and matchcode.
    
        Returns:
            list of dict: A list of dictionaries, each containing 'ACCOUNT_NO', 'FIRST_NAME', 'LAST_NAME', and 'MATCHCODE'.

        Raises:
            RuntimeError: If the XML data has not been parsed yet.
        """
        if self._xml_root is None:
            raise RuntimeError("XML data has not been parsed. You have to call the request method first.")

        business_partners = []
        for partner in self._xml_root.findall('.//BUSINESS_PARTNER'):
            account_no = partner.find('ACCOUNT_NO').text
            first_name = partner.find("NAME[@TYPE='FIRST']").text
            last_name = partner.find("NAME[@TYPE='LAST']").text
            matchcode = partner.find('MATCHCODE').text if partner.find('MATCHCODE') is not None else ''

            business_partners.append({
                'ACCOUNT_NO': account_no,
                'FIRST_NAME': first_name,
                'LAST_NAME': last_name,
                'MATCHCODE': matchcode
            })
        return business_partners

    @property
    def account_no(self):
        """Returns the account number of the business partner."""
        return self._get_text(".//ACCOUNT_NO")

    @property
    def matchcode(self):
        """Returns the matchcode if one exists. Else None."""
        return self._get_text(".//MATCHCODE")

    @property
    def courtesy_title(self):
        """Returns the courtesy title, regardless of the TYPE attribute."""
        return self._get_text(".//COURTESY_TITLE")

    @property
    def last_name(self):
        """Returns the last name of the business partner."""
        return self._get_text(".//NAME[@TYPE='LAST']")

    @property
    def first_name(self):
        """Returns the first name of the business partner."""
        return self._get_text(".//NAME[@TYPE='FIRST']")

    @property
    def mobile(self):
        """Returns the mobile number if exists or None."""
        return self._get_text(".//CONTACT[@TYPE='PHONE']")

    @property
    def phone(self):
        """Returns the phone number if exists or None."""
        return self._get_text(".//CONTACT[@TYPE='HOME']")

    @property
    def email(self):
        """Returns the email address if exists or None."""
        return self._get_text(".//CONTACT[@TYPE='EMAIL']")

    @property
    def address(self):
        """Returns the business partners address."""
        return self._get_text(".//ADDRESS")

    @property
    def zip(self):
        """Returns the zip code."""
        return self._get_text(".//ZIP")

    @property
    def city(self):
        """Returns the city."""
        return self._get_text(".//CITY")

    @property
    def date_of_birth(self):
        """Returns the date of birty."""
        return self._get_text(".//DATE_OF_BIRTH")

    @property
    def last_modified(self):
        """Returns the last modified date."""
        return self._get_text(".//LAST_MODIFIED")
