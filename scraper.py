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
        elements_out_file: str,
        history_file: str,
        searches_file: str,
        email: str,
        log_file: str = None,
        max_notif_entries: int = 4,
        email_html: bool = True,
        logger: logging.Logger = logging.getLogger(__name__),
        json_request: bool = False,
        pushover_notifications: bool = False,
        pushover_user_key: Optional[str] = None,
        pushover_token: Optional[str] = None,
        email_notifications: bool = True,
        email_pwd_file: str = None,
        include_changes: bool = True,
    ):
        # TODO Extract log file from logger, and send these in error email
        self.site_name = site_name
        self.secrets_file = secrets_file
        self.log_file = log_file
        self.elements_out_file = elements_out_file
        self.history_file = history_file
        self.searches_file = searches_file
        self.email = email
        self.max_notif_entries = max_notif_entries
        self.email_html = email_html
        self.logger = logger
        self.json_request = json_request
        self.pushover_notifications = pushover_notifications
        self.pushover_user_key = pushover_user_key
        self.pushover_token = pushover_token
        self.email_notifications = email_notifications
        self.email_pwd_file = email_pwd_file
        self.include_changes = include_changes

    def _is_valid_url(self, url: str) -> bool:
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

    def _compare_results(
        self, cur_elements: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Compare current elements with previous elements and return new elements.

        :param cur_elements: The current elements.
        :return: A list of new elements, or None if no new elements are found.
        """
        self.logger.info("Starting compare_results function")
        prev_elements = {}
        with open(self.elements_out_file, "r+") as fp:
            if fp.read() != "":
                fp.seek(0)
                try:
                    prev_elements = json.load(fp)
                except Exception as e:
                    os.remove(self.elements_out_file)
                    self.logger.error("Could not read json. Deleting file.")
                    raise IOError("Could not read json. Deleting file.") from e

        with open(self.elements_out_file, "w+") as fp:
            json.dump(cur_elements, fp)

        new = []
        for key in cur_elements:
            add = False
            # Add changed elements if self.include_changes is True
            if self.include_changes and cur_elements.get(key) != prev_elements.get(key):
                add = True
            if key not in prev_elements:
                add = True
            if add:
                new.append(cur_elements.get(key))

        self.logger.debug(f"Previous elements: {prev_elements}")
        self.logger.debug(f"Current elements: {cur_elements}")

        if len(new) == 0:
            self.logger.info("No new elements found")
            return None

        self.logger.info(f"Found {len(new)} new elements")
        return new

    def _i_o_setup(self) -> List[Dict[str, str]]:
        """
        Set up input/output files and read search parameters.

        :return: A list of search parameters.
        """
        self.logger.info("Starting i_o_setup function")
        if not Path(self.searches_file).exists():
            self.logger.error(f"Input file '{self.searches_file}' does not exist.")
            raise Exception(f"Input file '{self.searches_file}' does not exist.")

        create_files(self.elements_out_file, self.history_file, self.searches_file)

        with open(self.searches_file, "r") as fp:
            search_data = yaml.safe_load(fp)

        search_dict = []
        for search in search_data.get("searches", []):
            search_url = search.get("search_url")
            display_url = search.get(
                "display_url", search_url
            )  # Set to search_url if display_url is not provided
            search_title = search.get("title")
            if not self._is_valid_url(search_url) or not self._is_valid_url(
                display_url
            ):
                self.logger.error(f"Invalid URL(s) found: {search_url}, {display_url}")
                raise Exception(f"Invalid URL(s) found: {search_url}, {display_url}")

            search_dict.append(
                {
                    "search_url": search_url,
                    "display_url": display_url,
                    "search_title": search_title,
                }
            )

        self.logger.info("Finished i_o_setup function")
        return search_dict

    def _alert_write_new(
        self,
        elements: List[Dict[str, Any]],
        searches: List[Dict[str, str]],
    ):
        """
        Write new elements to the alert and send notifications.

        :param elements: The list of new elements.
        :param searches: The list of search parameters.
        """
        self.logger.info("Starting alert_write_new function")
        subj = f"Nye treff på {self.site_name}-søket ditt"
        notify_text = f"Det er blitt lagt til {len(elements)} nye annonse(r) på {self.site_name}-søket ditt.\n\n"

        archive_links = ""
        for i in range(0, len(elements)):
            element = elements[i]
            if "href" in element:
                url = element["href"]
            else:
                url = element["search"]["visit_url"]
            archive_links += "\n– {}".format(url)
            element_url = pyshorteners.Shortener().tinyurl.short(url)
            if i >= self.max_notif_entries:
                continue

            search_url = pyshorteners.Shortener().tinyurl.short(
                element["search"]["visit_url"]
            )
            element_link = f'<a href="{element_url}">{element["title"]}</a>'
            search_link = (
                f"<a href=\"{search_url}\">søk: '{element['search']['name']}'</a>"
            )

            notify_text += (
                f"\n{self._ad_string_format(element_link, search_link, element)}\n"
            )

        if len(elements) > self.max_notif_entries:
            notify_text += (
                f"\n... og {len(elements) - self.max_notif_entries} annonse(r) til.\n"
            )

        short_urls = [
            [
                pyshorteners.Shortener().tinyurl.short(search["display_url"]),
                search["search_title"],
            ]
            for search in searches
        ]
        notify_text += "\n\nLenke til søk:\n"

        for url, name in short_urls:
            notify_text += f"<a href=\"{url}\">'{name}'</a>\n"

        notify_text += f"\nVennlig hilsen,\n{self.site_name}-roboten"

        if self.pushover_notifications:
            if (
                not (self.pushover_token and self.pushover_user_key)
                and not self.secrets_file
            ):
                self.logger.error("Pushover api token and user key required")
                raise Exception("Pushover api token and user key required")
            notify.push_notification(
                notify_text,
                self.pushover_token,
                self.pushover_user_key,
                self.secrets_file,
            )
        if self.email_notifications:
            notify.mail(
                self.email,
                subj,
                notify_text,
                html=self.email_html,
                pwd_path=self.email_pwd_file,
            )
        if self.history_file:
            self._write_with_timestamp(archive_links, self.history_file)
        self.logger.info("Finished alert_write_new function")

    def _run_scraper(self):
        """
        The wrapper function to run the scraper.
        """
        self.logger.info("Starting main function")

        searches = self._i_o_setup()
        cur_elements = {}

        for search in searches:
            cur_elements = self._process_page(
                search["search_url"],
                cur_elements,
                search,
                max_pages=15,
                page_num=1,
            )

        new_elements = self._compare_results(cur_elements)

        if new_elements:
            self.logger.info(f"Found {len(new_elements)} new elements")
            self._alert_write_new(
                new_elements,
                searches,
            )

        self.logger.info("Finished main function")

    def main(self):
        """
        The main function to run the scraper with error handling.
        """
        e = None
        try:
            self._run_scraper()
        except Exception as e:
            e = e
            self.logger.error(traceback.format_exc())
        try:
            email_errors(
                e,
                self.email,
                script=self.site_name,
                history_file="./data/error_email.json",
                log_file=self.log_file,
                logger=self.logger,
            )
        except Exception as e:
            self.logger.error(f"Error sending error email: {e}")
            exit(-1)

    def _write_with_timestamp(self, links: str, filename: str):
        """
        Write links to a file with a timestamp.

        :param links: The links to write.
        :param filename: The file path to write to.
        """

        timestamp = arrow.now().format("YYYY-MM-DD HH:mm:ss")
        with open(filename, "a") as fp:
            fp.write(f"{timestamp}{links}\n\n")

    def _process_page(
        self,
        page_url: str,
        elmnts_dict: Dict[str, Any],
        search: Dict[str, str],
        max_pages: int,
        page_num: int,
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
        if self.json_request:
            page = requests.get(page_url, headers=headers).json()
        else:
            page = BROWSER.get(page_url, headers=headers).soup
        elmnts = self._get_elements(page)

        for e in elmnts:
            elmnts_dict = self._get_attrs(e, elmnts_dict, search)

        next_page_url = self._get_next_page(page, page_url)
        if next_page_url:
            if page_num > max_pages:
                self.logger.error(
                    f"Max page limit of {max_pages} reached without reaching end of search."
                )
                raise Exception(
                    f"Max page limit of {max_pages} reached without reaching end of search. "
                )
            page_num += 1
            self._process_page(
                next_page_url,
                elmnts_dict,
                search,
                max_pages,
                page_num,
                headers,
            )

        self.logger.info(f"Finished processing page: {page_url}")
        return elmnts_dict

    @abstractmethod
    def _get_elements(self, page: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract elements from a page.

        :param page: The page to extract elements from.
        :return: A list of elements.
        """
        pass

    @abstractmethod
    def _get_attrs(
        self, element: Any, elmnts_dict: Dict[str, Any], search: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extract attributes from an element. Beware: must include certain elements (see "return" below).

        :param element: The element to extract attributes from.
        :param elmnts_dict: The dictionary to store attributes.
        :param search: The search parameters.
        :return: The updated attributes dictionary with at least
        {"title": String, "search": {"name": String, "visit_url": String, "search_url": String.}
        """
        pass

    @abstractmethod
    def _get_next_page(self, page: BeautifulSoup, page_url: str) -> Optional[str]:
        """
        Get the URL for the next page of results.

        :param page: The current page.
        :param page_url: The current page URL.
        :return: The URL for the next page, or None if there is no next page.
        """
        pass

    @abstractmethod
    def _ad_string_format(
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


class SiteChangedScraper(Scraper):
    """
    A subclass of Scraper that checks whether html for a site has changed.
    """

    def _get_elements(self, page: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract elements from a page. For this scraper, we will just return the entire page content.

        :param page: The page to extract elements from.
        :return: A list containing the page content.
        """
        return [{"content": str(page)}]

    def _get_attrs(
        self, element: Any, elmnts_dict: Dict[str, Any], search: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extract attributes from an element.

        :param element: The element to extract attributes from.
        :param elmnts_dict: The dictionary to store attributes.
        :param search: The search parameters.
        :return: The updated attributes dictionary.
        """
        element["search"] = {
            "name": search["search_title"],
            "visit_url": search["display_url"],
            "search_url": search["search_url"],
        }
        element["title"] = search["search_title"]
        elmnts_dict[search["search_url"]] = element
        return elmnts_dict

    def _get_next_page(self, page: BeautifulSoup, page_url: str) -> Optional[str]:
        """
        Get the URL for the next page of results. For this scraper, we will not paginate.

        :param page: The current page.
        :param page_url: The current page URL.
        :return: None, as we do not paginate.
        """
        return None

    def _ad_string_format(
        self, offer_link: str, search_link: str, offer_dict: Dict[str, Any]
    ) -> str:
        """
        Format the ad string for an offer. For this scraper, we will return a simple message.

        :param offer_link: The offer link.
        :param search_link: The search link.
        :param offer_dict: The offer dictionary.
        :return: The formatted ad string.
        """
        return f"Innhold på nettsiden {search_link} har blitt endret siden sist."

    def _run_scraper(self):
        """
        Override the run_scraper method to check if the site has changed.
        """
        self.logger.info("Starting site change check function")

        searches = self._i_o_setup()
        cur_elements = {}

        for search in searches:
            cur_elements = self._process_page(
                search["search_url"],
                cur_elements,
                search,
                max_pages=1,
                page_num=1,
            )

        new_elements = self._compare_results(cur_elements)

        if new_elements:
            self.logger.info(f"Found {len(new_elements)} new elements")
            self._alert_write_new(
                new_elements,
                searches,
            )

        self.logger.info("Finished site change check function")


class SiteTextChangedScraper(SiteChangedScraper):
    """
    A subclass of SiteTextChangedScraper that checks if text has changed on a site.
    """

    def _get_elements(self, page: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract elements from a page. For this scraper, we will return the text on a site.
        Useful to avoid triggering notification because of dynamically changing html content.

        :param page: The page to extract elements from.
        :return: A list containing the page content.
        """
        return [{"content": page.text}]
