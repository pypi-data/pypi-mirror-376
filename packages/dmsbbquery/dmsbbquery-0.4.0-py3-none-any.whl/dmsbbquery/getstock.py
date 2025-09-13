#!/usr/bin/env python3
"""
getstock.py takes a partnumber as argument and outputs the inventory and 
additional metadata depending on the options provided.

Description:
    This script utilizes the dmsbbquery module to query stock levels and 
    retrieve associated metadata.

Example Usage:
    ./getstock.py "partnumber"    - shows the amount of the spare part in stock.
    ./getstock.py -a "partnumber" - shows the quantity and all meta data.
    ./getstock.py --help          - shows options and parameters

Dependencies:
    dmsbbquery
    shopdata

Notes:
    Author: Christian Gaida
"""

import os
import sys
import shutil
import argparse
import configparser
from dmsbbquery import AliveTest
from dmsbbquery.shopdata import GetStockInformation

DEBUG = False


def output(stock, argv):
    """Prints the stock data and optional metadata based on command-line arguments.

    If the verbose flag is provided, field names will be printed along with their values.

    Args:
        stock (GetStockInformation): The stock information object containing all data fields.
        argv (argparse.Namespace): Parsed command-line arguments determining which fields to show.

    Returns:
        None
    """

    def print_field(name, value):
        """Helper function to print field name and value based on verbosity flag."""
        if argv.verbose:
            print(f"{name}: {value}")
        else:
            print(value)

    if argv.raw:
        print(stock.rawout())
    else:
        print_field("stock", stock.stock)

        fields = [
            ("store", stock.store),
            ("invoice_text", stock.invoice_text),
            ("price", stock.price),
            ("tax_rate", stock.tax_rate),
            ("category", stock.category),
            ("group", stock.group),
        ]

        for name, value in fields:
            if getattr(argv, name) or argv.all:
                print_field(name, value)


def get_config_path():
    config_dir = os.path.expanduser("~/.config/dmsbbquery/")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return os.path.join(config_dir, "dmsbb.config")


def copy_default_config():
    config_path = get_config_path()
    if not os.path.exists(config_path):
        default_config_path = os.path.join(os.path.dirname(__file__), "dmsbb.config")
        shutil.copy(default_config_path, config_path)


def read_config(filename="dmsbb.config"):
    """Reads DMS server URL and dealer information from a configuration file.

    The function first searches for the configuration file in the current working directory.
    If the file is not found there, it searches in the user's configuration directory at ~/.config/dmsbbquery/.

    Args:
        filename (str): Name of the configuration file. Defaults to "dmsbb.config".

    Returns:
        tuple: A tuple containing the DMS URL (str) and dealer info as (region, dealer ID).

    Raises:
        FileNotFoundError: If the configuration file is not found in either location.
        RuntimeError: If required configuration values are missing in the file.
    """
    current_dir = os.getcwd()
    config_file = os.path.join(current_dir, filename)

    if not os.path.exists(config_file):
        config_dir = os.path.expanduser("~/.config/dmsbbquery/")
        config_file = os.path.join(config_dir, filename)

    if not os.path.exists(config_file):
        raise FileNotFoundError(
            f"Configuration file '{filename}' not found in current directory or in '{config_dir}'."
        )

    config = configparser.ConfigParser()
    config.read(config_file)

    url = config.get("dms", "url", fallback="http://localhost:8080")
    region = config.get("dealer", "region", fallback="123")
    dealer_id = config.get("dealer", "dealer", fallback="45678")

    if not all([url, region, dealer_id]):
        raise RuntimeError("Missing required configuration values in config.ini")

    return url, (region, dealer_id)


def get_arguments():
    """Parses and returns command-line arguments.

    Returns:
        argparse.Namespace: An object containing all parsed command-line options.
    """
    parser = argparse.ArgumentParser(description="Query the dealer management system.")
    parser.add_argument("partnumber", nargs="?", type=str, help="part number to query")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase output verbosity"
    )
    parser.add_argument(
        "-s", "--store", action="store_true", help="show storage location"
    )
    parser.add_argument(
        "-p", "--price", action="store_true", help="show price information"
    )
    parser.add_argument(
        "-i", "--invoice-text", action="store_true", help="show invoice text"
    )
    parser.add_argument(
        "-t", "--tax-rate", action="store_true", help="show tax rate (VAT)"
    )
    parser.add_argument("-c", "--category", action="store_true", help="show category")
    parser.add_argument("-g", "--group", action="store_true", help="show group")
    parser.add_argument("-a", "--all", action="store_true", help="show all")
    parser.add_argument("-r", "--raw", action="store_true", help="show raw xml output")
    parser.add_argument(
        "-A", "--alive-test", action="store_true", help="show server status"
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="try to get a quantity even if an exception has occured",
    )

    argv = parser.parse_args()
    return argv


def main(argv=None) -> int:
    """Main. Runs either a server health check or a stock query.

    Args:
        argv (argparse.Namespace): Parsed command-line arguments.

    Returns:
        None
    """
    copy_default_config()

    if argv is None:
        argv = get_arguments()

    url, dealer = read_config()

    if argv.alive_test:
        alive = AliveTest(url)
        print(alive.rawout())
    elif argv.partnumber is not None:
        stock = GetStockInformation(*dealer, url)
        stock.request(argv.partnumber)
        output(stock, argv)

    return 0


if __name__ == "__main__":
    sys.exit(main())
