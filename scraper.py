import json
import pyshorteners
import notify
import arrow
import mechanicalsoup as ms
import requests
import os
from pathlib import Path
import logging
from urllib.parse import urlparse
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import yaml
from email_errors import email_errors
import traceback

from i_o_utilities import create_files

DEFAULT_HISTORY_FILE = "./logs/history.txt"
DEFAULT_SEARCHES_FILE = "./input/searches.yaml"
DEFAULT_ELEMENTS_OUT_FILE = "./data/elements.json"
DEFAULT_LOG_FILE = "./logs/all.log"

HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "nb,no;q=0.9,en;q=0.8,es;q=0.7",
    "dnt": "1",
    "if-none-match": '"46:1:1:349:20250219144056747"',
    "priority": "u=1, i",
    "sec-ch-ua": '"Chromium";v="133", "Not(A:Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}

BROWSER = ms.StatefulBrowser()
BROWSER.set_user_agent("Mozilla/5.0")


class Scraper(ABC):
    """
    An abstract base class for web scrapers.
    """

    def __init__(
        self,
        site_name: str,
        secrets_file: str,
        log_file: str,
        elements_out_file: str,
        history_file: str,
        searches_file: str,
        email: str,
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self.site_name = site_name
        self.secrets_file = secrets_file
        self.log_file = log_file
        self.elements_out_file = elements_out_file
        self.history_file = history_file
        self.searches_file = searches_file
        self.email = email
        self.logger = logger

    def is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid.

        :param url: The URL to check.
        :return: True if the URL is valid, False otherwise.
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def compare_results(
        self, I_O_FILE: str, cur_elements: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Compare current elements with previous elements and return new elements.

        :param I_O_FILE: The file path for input/output.
        :param cur_elements: The current elements.
        :return: A list of new elements, or None if no new elements are found.
        """
        self.logger.info("Starting compare_results function")
        prev_elements = {}
        with open(I_O_FILE, "r+") as fp:
            if fp.read() != "":
                fp.seek(0)
                try:
                    prev_elements = json.load(fp)
                except Exception as e:
                    os.remove(I_O_FILE)
                    self.logger.error("Could not read json. Deleting file.")
                    raise IOError("Could not read json. Deleting file.") from e

        with open(I_O_FILE, "w+") as fp:
            json.dump(cur_elements, fp)

        if len(cur_elements.keys() - prev_elements.keys()) > 0:
            new = {}
            for element_id, element in cur_elements.items():
                if element_id not in prev_elements:
                    new[element_id] = element
            self.logger.info(f"Found {len(new)} new elements")
            return list(new.values())

        self.logger.info("No new elements found")
        return None

    def i_o_setup(
        self, elements_file: str, history_file: str, search_file: str
    ) -> List[Dict[str, str]]:
        """
        Set up input/output files and read search parameters.

        :param elements_file: The elements output file path.
        :param history_file: The history file path.
        :param search_file: The search file path.
        :return: A list of search parameters.
        """
        self.logger.info("Starting i_o_setup function")
        if not Path(search_file).exists():
            self.logger.error(f"Input file '{search_file}' does not exist.")
            raise Exception(f"Input file '{search_file}' does not exist.")

        create_files(elements_file, history_file, search_file)

        with open(search_file, "r") as fp:
            search_data = yaml.safe_load(fp)

        search_dict = []
        for search in search_data.get("searches", []):
            url = search.get("search_url")
            visit_url = search.get(
                "display_url", None
            )  # Set to None if display_url is not provided
            name = search.get("title")
            if not self.is_valid_url(url) or not self.is_valid_url(visit_url):
                self.logger.error(f"Invalid URL(s) found: {url}, {visit_url}")
                raise Exception(f"Invalid URL(s) found: {url}, {visit_url}")

            search_dict.append({"url": url, "visit_url": visit_url, "name": name})

        self.logger.info("Finished i_o_setup function")
        return search_dict

    def alert_write_new(
        self,
        site: str,
        elements: List[Dict[str, Any]],
        searches: List[Dict[str, str]],
        push_notifications: bool,
        email_notifications: bool,
        max_notif_entries: int,
        email: str,
        pushover_token: str = None,
        pushover_key: str = None,
        output_file: str = "history.txt",
        secret_file: str = "./input/secrets.yaml",
        email_html: bool = True,
    ):
        """
        Write new elements to the alert and send notifications.

        :param site: The site name.
        :param elements: The list of new elements.
        :param searches: The list of search parameters.
        :param push_notifications: Whether to send push notifications.
        :param email_notifications: Whether to send email notifications.
        :param max_notif_entries: The maximum number of notification entries.
        :param pushover_token: The Pushover API token.
        :param email: The email address to send notifications to.
        :param pushover_key: The Pushover user key.
        :param output_file: The output file path for the alert.
        :param secret_file: The secrets file path.
        :param email_html: Whether to send the email as HTML.
        """
        self.logger.info("Starting alert_write_new function")
        subj = f"Nye treff på {site}-søket ditt"
        notify_text = f"Det er blitt lagt til {len(elements)} nye annonse(r) på {site}-søket ditt.\n\n"

        archive_links = ""
        for i in range(0, len(elements)):
            element = elements[i]
            if "href" in element:
                archive_links += "\n– {}\n".format(element["href"])
                element_url = pyshorteners.Shortener().tinyurl.short(element["href"])
            else:
                archive_links += "\n– [No element url]\n"
                element_url = "[No element url]"
            if i >= max_notif_entries:
                continue

            search_url = pyshorteners.Shortener().tinyurl.short(
                element["search"]["visit_url"]
            )
            element_link = f'<a href="{element_url}">{element["title"]}</a>'
            search_link = (
                f"<a href=\"{search_url}\">søk: '{element['search']['name']}'</a>"
            )

            notify_text += (
                f"\n{self.ad_string_format(element_link, search_link, element)}\n"
            )

        if len(elements) > max_notif_entries:
            notify_text += (
                f"\n... og {len(elements) - max_notif_entries} annonse(r) til.\n"
            )

        short_urls = [
            [
                pyshorteners.Shortener().tinyurl.short(search["visit_url"]),
                search["name"],
            ]
            for search in searches
        ]
        notify_text += "\n\nLenke til søk:\n"

        for url, name in short_urls:
            notify_text += f"<a href=\"{url}\">'{name}'</a>\n"

        notify_text += f"\nVennlig hilsen,\n{site}-roboten"

        if push_notifications:
            if not (pushover_token and pushover_key) and not secret_file:
                self.logger.error("Pushover api token and user key required")
                raise Exception("Pushover api token and user key required")
            notify.push_notification(
                notify_text, pushover_token, pushover_key, secret_file
            )
        if email_notifications:
            notify.mail(email, subj, notify_text, html=email_html)
        if output_file:
            self.write_with_timestamp(archive_links, output_file)
        self.logger.info("Finished alert_write_new function")

    def write_with_timestamp(self, links: str, filename: str):
        """
        Write links to a file with a timestamp.

        :param links: The links to write.
        :param filename: The file path to write to.
        """
        timestamp = arrow.now().format("YYYY-MM-DD HH:mm:ss")
        with open(filename, "a") as fp:
            fp.write(f"{timestamp}{links}\n\n")

    def process_page(
        self,
        page_url: str,
        elmnts_dict: Dict[str, Any],
        search: Dict[str, str],
        max_pages: int,
        page_num: int,
        json_request: bool = False,
        headers: Dict[str, str] = HEADERS,
    ) -> Dict[str, Any]:
        """
        Process a page of results.

        :param page_url: The URL of the page to process.
        :param elmnts_dict: The dictionary to store elements.
        :param search: The search parameters.
        :param max_pages: The maximum number of pages to process.
        :param page_num: The current page number.
        :param json_request: Whether the request is for JSON data.
        :param headers: The request headers.
        :return: The updated elements dictionary.
        """
        self.logger.info(f"Processing page: {page_url}")
        if json_request:
            page = requests.get(page_url, headers=headers).json()
        else:
            page = BROWSER.get(page_url, headers=headers).soup
        elmnts = self.get_elements(page)

        for e in elmnts:
            elmnts_dict = self.get_attrs(e, elmnts_dict, search)

        next_page_url = self.get_next_page(page, page_url)
        if next_page_url:
            if page_num > max_pages:
                self.logger.error(
                    f"Max page limit of {max_pages} reached without reaching end of search."
                )
                raise Exception(
                    f"Max page limit of {max_pages} reached without reaching end of search. "
                )
            page_num += 1
            self.process_page(
                next_page_url,
                elmnts_dict,
                search,
                max_pages,
                page_num,
                json_request,
                headers,
            )

        self.logger.info(f"Finished processing page: {page_url}")
        return elmnts_dict

    @abstractmethod
    def get_elements(self, page: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract elements from a page.

        :param page: The page to extract elements from.
        :return: A list of elements.
        """
        pass

    @abstractmethod
    def get_attrs(
        self, element: Any, elmnts_dict: Dict[str, Any], search: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extract attributes from an element.

        :param element: The element to extract attributes from.
        :param elmnts_dict: The dictionary to store attributes.
        :param search: The search parameters.
        :return: The updated attributes dictionary.
        """
        pass

    @abstractmethod
    def get_next_page(self, page: BeautifulSoup, page_url: str) -> Optional[str]:
        """
        Get the URL for the next page of results.

        :param page: The current page.
        :param page_url: The current page URL.
        :return: The URL for the next page, or None if there is no next page.
        """
        pass

    @abstractmethod
    def ad_string_format(
        self, offer_link: str, search_link: str, offer_dict: Dict[str, Any]
    ) -> str:
        """
        Format the ad string for an offer.

        :param offer_link: The offer link.
        :param search_link: The search link.
        :param offer_dict: The offer dictionary.
        :return: The formatted ad string.
        """
        pass

    def run_scraper(self, email_html: bool):
        """
        The wrapper function to run the scraper.
        """
        self.logger.info("Starting main function")

        searches = self.i_o_setup(
            self.elements_out_file, self.history_file, self.searches_file
        )
        cur_elements = {}

        for search in searches:
            cur_elements = self.process_page(
                search["url"],
                cur_elements,
                search,
                max_pages=15,
                page_num=1,
                json_request=True,
            )

        new_elements = self.compare_results(self.elements_out_file, cur_elements)

        if new_elements:
            self.logger.info(f"Found {len(new_elements)} new elements")
            self.alert_write_new(
                self.site_name,
                new_elements,
                searches,
                push_notifications=True,
                email_notifications=True,
                max_notif_entries=4,
                email=self.email,
                output_file=self.history_file,
                secret_file=self.secrets_file,
                email_html=email_html,
            )

        self.logger.info("Finished main function")

    def main(self):
        """
        The main function to run the scraper with error handling.
        """
        try:
            self.run_scraper()
            email_errors(
                None,
                self.email,
                script=self.site_name,
                history_file="./data/error_email.json",
                log_file=self.log_file,
                logger=self.logger,
            )
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            stack_trace = traceback.format_exc()
            with open(self.log_file, "a") as log_fp:
                log_fp.write(stack_trace)
            email_errors(
                e,
                self.email,
                script=self.site_name,
                history_file="./data/error_email.json",
                log_file=self.log_file,
                logger=self.logger,
            )
            raise
