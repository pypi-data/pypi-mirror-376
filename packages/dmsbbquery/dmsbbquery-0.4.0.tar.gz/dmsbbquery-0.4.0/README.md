# DMSBackboneQuery

DMSBackboneQuery is a Python project that simplifes interactions with the VW Dealer Management System Backbone. It provides a small, consistent API to query stock data, business partner data, and workshop orders from a DMS Backbone server, plus a lightweight CLI to fetch stock information.

[![SemVer 0.4.0][img_version]][version-url]
[![Codestyle: black][codestyle-shield]][codestyle-url]
[![python version][python-version-shield]][python-version-url]
[![MIT Licencel][image_licence]][license-url]

## Table of Contents
* [About DMSBackboneQuery](#about)
* [Getting Started](#start)
  - [Installation](#installation)
    + [Via PyPI](#pypi)
    + [Via Gitlab](#gitlab-repo)
  - [Configuration](#config)
  - [Test your setup](#testing)
* [Usage](#usage)
  - [Module shopdata](#shopdata)
    - [Class GetStockInformation](#getstockinfo) - the corresponding class
  - [Module businesspartnerdata](#businesspartnerdata)
    - [Class GetEntry](#getentry) - query customer information
  - [Module workshoporder](#workshoporder)
    - [Class ListOrder](#listorder) - get workshoporder list
    - [Class GetOrder](#getorder) - get order details
  - [CLI: getstock](#cli-getstock)
* [Contributing](#contrib)
* [License](#license)
* [Contact](#contact)
* [Acknowledgements](#acknowledgements)

<a name="about"></a>
## About DMSBackboneQuery
DMSBackboneQuery provides a compact interface to the VW DMS Backbone. It centers around a base class, `DMSBackboneQuery`, and concrete query classes for different services.

Currently supported:

* **DMSBackbone:**
  - Base class dmsbbquery
  - AliveTest: Check system status
 
* **ShopData:**
  - GetStockInformation: Retrieve stock data
 
* **WorkshopOrder:**
  - ListOrder: List workshop orders
  - GetOrder: Retrieve specific order details
 
* **BusinessPartnerData:**
  - GetEntry: Fetch business partner entry

<a name="start"></a>
## Getting Started
There are two ways to install DMSBackboneQuery:

1. **Via PyPI:** This method provides a straightforward installation.
2. **From the GitLab Repository:** This method not only installs the package but also gives you access to a simple mock server for testing purposes outside of a production environment.

<a name="installation"></a>
### Installation

<a name="pypi"></a>
#### Via PyPI
The project is available on PyPI and can be installed with the following command:
```sh
pip install dmsbbquery
```

<a name="gitlab-repo"></a>
#### From GitLab Repository
By cloning the repository, you gain access to a simple mock server, allowing you to perform tests outside of the production environment.

1. Clone the repository:
   ```sh
   git clone https://gitlab.com/chgaida/dmsbbquery.git

   cd dmsbbquery/
   ```

2. Set up a virtual environment (recommended):
   ```sh
   python3 -m venv env

   source env/bin/activate
   ```

3. Install the package and its dependencies:
   ```sh
   pip install .
   ```

<a name="config"></a>
### Configuration
The `getstock` CLI tool requires configuration before use, but the default settings are suitable for testing purposes. Upon its initial execution, the `dmsbb.config` file will be automatically copied to `~/.config/dmsbb/`.

By default, the URL in the configuration file is set to `http://localhost:8080`, which is suitable for testing with the local mock server. In a production environment, you will need to update this URL to the appropriate DMS Backone server address and specify your three-digit dealer region and five-digit dealer number.

<a name="testing"></a>
### Test your setup
You can test the modules and the CLI tool `getstock` with a local server without running DMS Backbone and without being in your corporate network. For that, you need to edit the url in  `dmsbb.config`:
```
[dms]
url = http://localhost:8080
```

The `getstock` CLI tool will initially search for the configuration file in the current directory and then in `~/.config/dmsbb/`.

Start the mock DMS-Backbone server:
```sh
cd dmsbb_mockserver

python3 dmsbb_srv.py &
```

Try `getstock` with any dummy partnumber:
```sh
getstock abc123123
```
The output will begin with the response from the mock server, followed by the stock quantity.

<a name="usage"></a>
## Usage

<a name="shopdata"></a>
### Module shopdata

<a name="getstockinfo"></a>
#### Class GetStockInformation
The `GetStockInformation` class queries stock, price and metadata for a spare part.

- Constructor
  - `GetStockInformation(region: str, dealer: str, url: str)`

- Public method
  - `request(partnumber: str, brand_id: str = "V") -> int`
    - Sends a request for stock information. If stock is not found, a fallback with `brand_id="F"` is used.
    - Returns the HTTP status code.

- Properties (derived from the latest request)
  - `success` (bool)
  - `error_code` (str or None)
  - `error_text` (str or None)
  - `stock` (str)
  - `store` (str)
  - `invoice_text` (str)
  - `price` (str)
  - `currency` (str)
  - `tax_rate` (str)
  - `category` (str)
  - `group` (str)

Examples:

```python
>>> from dmsbbquery.shopdata import GetStockInformation
>>>
>>> # Define your region, dealer ID and the server URL
>>> region = "123"
>>> dealer_id = "45678"
>>> url = "http://lpnbb:81"
>>>
>>> # Create an instance of the GetStockInformation class
>>> stock = GetStockInformation(region, dealer, url)
>>>
>>> # Request the stock information
>>> stock.request("N  90813202")
200 # <- http status code
>>>
>>> print(f"Stock: {stock.stock}")
Stock: 201
>>> print(f"Store: {stock.store}")
Store: A3F01
>>> print(stock.rawout())  # full pretty XML response
>>> ...
```

<a name="businesspartnerdata"></a>
### Module businesspartnerdata

<a name="getentry"></a>
#### Class GetEntry
The `GetEntry` class queries customer (business partner) information.

- Constructor
  - `GetEntry(region: str, dealer: str, url: str)`

- Public method
  - `request(first_name: str = "", last_name: str = "", account_no: str = "", matchcode: str = "") -> int`
    - At least one parameter must be provided; otherwise a `ValueError` is raised.
    - Returns the HTTP status code.

- Helper function
  - `bp_list() -> list[dict]`  # returns list of accounts with ACCOUNT_NO, FIRST_NAME, LAST_NAME, MATCHCODE.

- Properties
  - `account_no`, `matchcode`, `courtesy_title`, `last_name`, `first_name`
  - `mobile`, `phone`, `email`, `address`, `zip`, `city`
  - `date_of_birth`, `last_modified`

Usage example:

```python
>>> from dmsbbquery.businesspartnerdata import GetEntry
>>>
>>> # Define your region, dealer ID and the server URL
>>> region = "123"
>>> dealer_id = "45678"
>>> url = "http://lpnbb:81"
>>>
>>> customer = GetEntry(region, dealer, url)
>>> customer.request(first_name="christian", last_name="gaida")
200 # <- http status code
>>>
>>> print(customer.rawout())  # full XML response
>>> ...
>>> print("Account No:", customer.account_no)
101
>>>
```

<a name="workshoporder"></a>
### Module workshoporder

<a name="getorder"></a>
#### Class GetOrder
Retrieve detailed information about a workshop order.

- Constructor
  - `GetOrder(region: str, dealer: str, url: str)`

- Public method
  - `request(order_id: str) -> int`
    - Retrieves information for a given workshop order number.
    - Returns the HTTP status code.

- Properties
  - `success`, `error_code`, `error_text`

Usage example:

```python
>>> from dmsbbquery.workshoporder import GetOrder
>>>
>>> region = "123"
>>> dealer = "45678"
>>> url = "http://lpnbb:81"
>>> 
>>> order = GetOrder(region, dealer, url)
>>> order.request("2025101123")
>>>
>>> print("Success:", order.success)
Success: True
>>>
>>> print(order.rawout())  # full XML response
>>> ...
```

<a name="listorder"></a>
#### Class ListOrder
Get a list of all workshop orders.

- Constructor
  - `ListOrder(region: str, dealer: str, url: str)`

- Public method
  - `get_order_numbers() -> list[str]`
    - Returns a list of order numbers parsed from the response.

Usage example:

```python
>>> from dmsbbquery.workshoporder import ListOrder
>>> 
>>> region = "123"
>>> dealer = "45678"
>>> url = "http://lpnbb:81"
>>> 
>>> lst = ListOrder(region, dealer, url)
>>> numbers = lst.get_order_numbers()
>>> print("Order numbers:", numbers)
Order numbers: ['2021102217', '2025104246', '2021103570', '2025102595', '2022101311', '2022106586', ...]
```

<a name="cli-getstock"></a>
### CLI: getstock
The getstock script exposes a small CLI to query stock information and display metadata.

Basic usage:
- Show stock for a part number:
  getstock "PARTNO"

- Show all metadata:
  getstock -a "PARTNO"

- Show raw XML:
  getstock -r "PARTNO"

- Test server status:
  getstock -A

- Show available options:
  getstock -h
  
Included options mirror the fields exposed by `GetStockInformation` (e.g., verbose, store, price, invoice-text, tax-rate, category, group, raw, alive-test, force).

Example:

```bash
getstock -v -p -i "N  90813202"
stock: 137
invoice_text: SCHRAUBE
price: 5.60
```

Type `getstock -h` to get an overview of the options and arguments.

```sh
usage: getstock [-h] [-v] [-s] [-p] [-i] [-t] [-c] [-g] [-a] [-r] [-A] [-f] [partnumber]

Query the dealer management system.

positional arguments:
  partnumber          part number to query

options:
  -h, --help          show this help message and exit
  -v, --verbose       increase output verbosity
  -s, --store         show storage location
  -p, --price         show price information
  -i, --invoice-text  show invoice text
  -t, --tax-rate      show tax rate (VAT)
  -c, --category      show category
  -g, --group         show group
  -a, --all           show all
  -r, --raw           show raw xml output
  -A, --alive-test    show server status
  -f, --force         try to get a quantity even if an exception has occured
```

<a name="contrib"></a>
## Contributing
Contributions are welcome. Please open issues for feature requests or bug reports, and submit pull requests with clear, focused changes and tests where feasible.

- Follow the existing code style (Black-compatible formatting).
- Include tests or clear examples where possible.
- Update the README/docs if you adjust public APIs.

<a name="license"></a>
## License
Distributed under the MIT License. See [LICENSE](./LICENSE) for more information.

<a name="contact"></a>
## Contact
finger(1) finger@port70.de



<!-- MARKDOWN LINKS & IMAGES -->
[codestyle-shield]: https://img.shields.io/badge/code%20style-black-000000.svg
[codestyle-url]: https://github.com/psf/black
[python-version-shield]: https://img.shields.io/badge/python-3.11-blue
[python-version-url]: https://www.python.org/downloads/release/python-370/
[image_licence]: https://img.shields.io/badge/License-MIT-blue.svg
[img_version]: https://img.shields.io/static/v1.svg?label=SemVer&message=0.4.0&color=blue
[version-url]: https://pypi.org/project/dmsbbquery/
[license-url]: https://gitlab.com/chgaida/dmsbbquery/-/blob/main/LICENSE
