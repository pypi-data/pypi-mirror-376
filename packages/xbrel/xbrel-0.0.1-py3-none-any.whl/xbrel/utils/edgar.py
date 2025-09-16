"""
This module is a helper for the SEC EDGAR database. It provides a function to download filings from the SEC EDGAR database given the CIK and the filing type.
If a date is provided, the function will download the filing for the given date. If no date is provided, the function will download the most recent filing.

The module also provides a function for listing all filings for a given CIK and filing type.
"""

from brel import Filing
import requests, json, os, datetime, time
from typing import ClassVar, Dict, List, Union, cast
from collections import defaultdict
import pandas as pd
import re
from bs4 import BeautifulSoup as bs

SUPPORTED_FILING_TYPES = ["10-K", "10-Q", "8-K"]

session = requests.Session()

# the edgar cache dir is in the user's home directory in .brel_edgar_cache
# create the directory if it does not exist
if not os.path.exists(os.path.join(os.path.expanduser("~"), ".brel_edgar_cache")):
    os.makedirs(os.path.join(os.path.expanduser("~"), ".brel_edgar_cache"))
edgar_cache_dir = os.path.join(os.path.expanduser("~"), ".brel_edgar_cache")


def __download_metadata_for_cik(cik: str) -> bool:
    """
    Downloads the file for the cik and places it in the edgar cache dir.
    :param cik: The CIK of the company.
    :return: True if the metadata was downloaded successfully, False otherwise.
    """
    print(f"Downloading metadata for CIK {cik}")
    sec_data_uri = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"

    #JM update headers to fix 403 code from SEC website
    _headers = {
        "User-Agent": f"{int(time.time())} {int(time.time())}@gmail.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    }
    #JM: response = session.get(sec_data_uri, headers={"User-Agent": "Mozilla/5.0"})
    response = session.get(sec_data_uri, headers=_headers)
    if response.status_code != 200:
        return False

    response_json = response.json()
    with open(os.path.join(edgar_cache_dir, f"{cik.zfill(10)}.json"), "w") as f:
        json.dump(response_json, f)

    return True


def __is_cached(cik: str) -> bool:
    """
    Checks if the metadata for the given CIK is cached.
    :param cik: The CIK of the company.
    :return: True if the metadata is cached, False otherwise.
    """
    return os.path.exists(os.path.join(edgar_cache_dir, f"{cik.zfill(10)}.json"))


def open_edgar(cik: str, filing_type: str, date: str | None = None) -> Filing:
    """
    Download a filing from the SEC EDGAR database given the CIK and the filing type.

    Example usage:
    ```
    from brel.utils import open_edgar

    # The cik for Apple Inc.
    apple_cik = "320193"
    report_type = "10-K"
    filing = open_edgar(apple_cik, report_type)
    ```

    Alternatively, you can specify a date to download a filing for a specific date.
    Use the format YYYY-MM-DD for the date.

    Example usage:

    ```
    from brel.utils import open_edgar

    filing = open_edgar("320193", "10-K", "2021-01-01")
    ```

    Note that the date refers to the report date, not the filing date.

    :param cik: The CIK of the company.
    :param filing_type: The filing type. Has to be one of the following: "10-K", "10-Q", "8-K".
    :param download_dir: The directory where the filing will be downloaded.
    :param date: The date of the filing in the format YYYY-MM-DD.
    :return: The path to the downloaded filing.
    """

    # check that the date is in the correct format
    if date is not None:
        if not isinstance(date, str):
            raise ValueError("The date has to be a string in the format YYYY-MM-DD")
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Incorrect date format. The date has to be in the format YYYY-MM-DD")

    # check that the cik is a str that has at most 10 characters
    if not isinstance(cik, str) or len(cik) > 10:
        raise ValueError("The CIK has to be a string with at most 10 characters")

    # Check if the filing type is supported
    if filing_type not in SUPPORTED_FILING_TYPES:
        raise ValueError(
            f"Filing type {filing_type} is not supported. It has to be one of the following: {', '.join(SUPPORTED_FILING_TYPES)}"
        )

    # Check if the metadata for the CIK is cached
    if not __is_cached(cik):
        if not __download_metadata_for_cik(cik):
            raise ValueError(f"Failed to download metadata for CIK {cik}")
    else:
        # if the file is older than 1 day, download it again
        if (
            datetime.datetime.now()
            - datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(edgar_cache_dir, f"{cik.zfill(10)}.json")))
        ).days > 1:
            if not __download_metadata_for_cik(cik):
                raise ValueError(f"Failed to download metadata for CIK {cik}")

    # Load the metadata for the CIK
    with open(os.path.join(edgar_cache_dir, f"{cik.zfill(10)}.json"), "r") as f:
        metadata = json.load(f)

        recent = metadata["filings"]["recent"]

        def report_fits(i: int) -> bool:
            is_right_type = recent["form"][i] == filing_type
            is_xbrl = str(recent["isXBRL"][i]) == "1"
            is_right_date = date is None or recent["reportDate"][i] == date
            return is_right_type and is_xbrl and is_right_date

        right_is = [i for i in range(len(recent["form"])) if report_fits(i)]

        right_is.sort(key=lambda i: int(recent["reportDate"][i].replace("-", "")), reverse=True)

        right_i = right_is[0] if len(right_is) > 0 else None

        if right_i is None:
            raise ValueError(f"No filing found for CIK {cik}, filing type {filing_type}, and date {date}")

        accession_number = recent["accessionNumber"][right_i]
        #JM: primary_doc = recent["primaryDocument"][right_i]

        reported_date = recent["reportDate"][right_i]
        cik_mapper = SEC_Mapper()
        cik_ticker = str(cik_mapper.getTicker(cik.zfill(10))).lower()
        uri_sec = f"https://www.sec.gov/Archives/edgar/data/{cik.zfill(10)}/{accession_number.replace('-', '')}"
        xml_url_path = get_sec_xml_file(uri_sec)
        primary_doc = os.path.basename(xml_url_path)

        #JM TODO support old filings
        uri = (
            f"https://www.sec.gov/Archives/edgar/data/{cik.zfill(10)}/{accession_number.replace('-', '')}/{primary_doc}"
        )

        #JM fix SEC 403 response
        _headers = {
            "User-Agent": f"{int(time.time())} {int(time.time())}@gmail.com",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
        }
        ping = session.get(uri, headers=_headers)
        if ping.status_code != 200:
            raise ValueError(
            f"Failed to download filing from {uri}. Note that the Brel does not support .htm filings and that it cannot scrape EDGAR's website. We suggest that you search for the .xml filing on {uri_sec} and call brel.Filing.open(uri) with the correct URI."
            )
        #JM: old solution no longer needed.
        #if uri.endswith(".htm"):
        #    uri_dir = uri[: uri.rfind("/")]
        #    uri_newer = uri.replace(".htm", "_htm.xml")
        #    uri_older = uri.replace(".htm", ".xml")
        #    #JM fix SEC 403 response
        #    _headers = {
        #        "User-Agent": f"{int(time.time())} {int(time.time())}@gmail.com",
        #        "Accept-Encoding": "gzip, deflate",
        #        "Host": "www.sec.gov",
        #    }
        #    ping = session.get(uri_newer, headers=_headers)
        #    uri = uri_newer
        #    if ping.status_code != 200:
        #        print(f"This url doesnt exist because of newer filings format: {uri_newer}")
        #        print(f"Trying older url: {uri_older}")
        #        ping = session.get(uri_older, headers=_headers)
        #        uri = uri_older
        #        if ping.status_code != 200:
        #            raise ValueError(
        #            f"Failed to download filing from {uri_older}. Note that the Brel does not support .htm filings and that it cannot scrape EDGAR's website. We suggest that you search for the .xml filing on {uri_dir} and call brel.Filing.open(uri) with the correct URI."
        #            )
        print(f"Opening {filing_type} filing of {metadata['name']} ({cik}) on {recent['reportDate'][right_i]}")
        return Filing.open(uri)

# JM: new solution to find the xml file from scraping the SEC url itself.
def get_sec_html(url):
    _headers = {
        "User-Agent": f"{int(time.time())} {int(time.time())}@gmail.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov",
    }
    resp = requests.get(url, headers=_headers)
    return resp

def get_sec_xml_file(url):
    resp = get_sec_html(url)
    html = resp.text
    soup = bs(html, 'html.parser')
    table = soup.find('table')
    hrefs = [a['href'] for a in table.find_all('a', href=True)]
    pattern_xml = r'.*\.xml'
    exclude_patterns = ("_def.xml", "_lab.xml", "_cal.xml", "_pre.xml", "FilingSummary.xml")
    filtered_urls = [url for url in [h for h in hrefs if re.match(pattern_xml, h)] if not url.endswith(exclude_patterns)]
    return f"https://www.sec.gov{filtered_urls[0]}"

def get_10k_reportdates(cik):
    _headers = {
        "User-Agent": f"{int(time.time())} {int(time.time())}@gmail.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    }
    
    ticker = SEC_Mapper().getTicker(cik.zfill(10))
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    resp = requests.get(url, headers=_headers)
    time.sleep(0.1)
    resp.raise_for_status()
    metadata = resp.json()
    forms = metadata["filings"]["recent"]["form"]
    forms_reportDate = metadata["filings"]["recent"]["reportDate"]
    form10k_pattern = r'^10-K$'
    form10k_indices = [i for i, value in enumerate(forms) if re.match(form10k_pattern, value)]
    form10k_reportDate = [forms_reportDate[i] for i in form10k_indices]

    return form10k_reportDate

# JM: add cik to ticker and ticker to cik class function
class SEC_Mapper:
    _headers = {
        "User-Agent": f"{int(time.time())} {int(time.time())}@gmail.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov",
    }

    def __init__(self):
        self.mapping_metadata = self._get_mapping_metadata_from_sec()

    def _clean_ticker(self, ticker) -> str:
        ticker_pattern = re.compile(r"[^A-Z0-9\-]+")
        return re.sub(ticker_pattern, "", ticker)
    
    def _get_mapping_metadata_from_sec(self):
        URL = 'https://www.sec.gov/files/company_tickers_exchange.json'
        resp = requests.get(URL, headers=SEC_Mapper._headers)
        resp.raise_for_status()
        data = resp.json()
        fields = data["fields"]
        field_indices = {field: fields.index(field) for field in fields}
        company_data = data["data"]
        transformed_data: List[Dict[str, str]] = []

        for cd in company_data:
            transformed_data.append(
                self.transform(field_indices, cd),
            )
        
        df = pd.DataFrame(transformed_data)
        df.sort_values(by=["CIK", "Ticker"], inplace=True, ignore_index=True)
        return df

    def cik_to_ticker(self):
        cik_col = self.mapping_metadata["CIK"]
        ticker_col = self.mapping_metadata["Ticker"]
        return self._form_kv_set_mapping(cik_col, ticker_col)

    def ticker_to_cik(self):
        cik_col = self.mapping_metadata["CIK"]
        ticker_col = self.mapping_metadata["Ticker"]
        return self._form_kv_mapping(ticker_col, cik_col)

    def getCIK(self, ticker):
        ticker_to_cik_mapper_list = self.ticker_to_cik()
        time.sleep(0.1)
        return ticker_to_cik_mapper_list[ticker]

    def getTicker(self, cik):
        cik_to_ticker_mapper_list = self.cik_to_ticker()
        time.sleep(0.1)
        return list(cik_to_ticker_mapper_list[cik])[0]
        
    def transform(
        self,
        field_indices,
        company_data,
        ) -> Dict[str, str]:
        cik = str(company_data[field_indices["cik"]])
        ticker = str(company_data[field_indices["ticker"]])
        name = str(company_data[field_indices["name"]])
        exchange = str(company_data[field_indices["exchange"]])
        return {
            "CIK": cik.zfill(10),
            "Ticker": self._clean_ticker(ticker),
            "Name": name.title(),
            "Exchange": exchange,
        }

    def _form_kv_mapping(self, keys: pd.Series, values: pd.Series) -> Dict[str, str]:
        """Form key-value mapping, ignoring blank keys and values."""
        return {k: v for k, v in zip(keys, values) if k and v}

    def _form_kv_set_mapping(self, keys: pd.Series, values: pd.Series):
        """Form mapping from key to list of values, ignoring blank keys and values.

        Example: numerous CIKs map to multiple tickers (e.g. Banco Santander),
        so we must keep a list of tickers for each unique CIK.
        """
        mapping = defaultdict(set)
        for key, value in zip(keys, values):
            # Ignore blank keys and values
            if key and value:
                mapping[key].add(value)
        return dict(mapping)
