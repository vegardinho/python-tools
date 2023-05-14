import json
from pathlib import Path
import pyshorteners
import notify
import arrow
import mechanicalsoup as ms
import traceback
import requests

BROWSER = ms.StatefulBrowser()
BROWSER.set_user_agent('Mozilla/5.0')


def scrape_site(get_elmnts_func, get_attrs_func, get_next_url_func, site_name, out_string_format, elmnts_out_file='./in_out/elements.out',
                history_file='./in_out/history.txt', searches_file='./in_out/searches.in', max_pages=15,
                email='landsverk.vegard@gmail.com', max_notifi_entries=4, push_notification=True, pushover_token=None,
                email_notification=False, email_exceptions=True, json_request=False):
    """
    :param get_elmnts_func:     Takes mechanicalsoup object, and returns iterable mechanicalsoup object
                                of all desired html elements.
    :type  Function
    :param get_attrs_func:      Takes (mechanicalsoup html element, dict of elements, and search object
                                returned by i_o_setup, and returns updated dict.
    :type  Function
    :param get_next_url_func:  Takes (mechanicalsoup page object, page_url), and returns mechandicalsoup object of
                                next page link element in search, or None if no more pages.
    :type  Function
    :param site_name:           Name displayed in title of notification.
    :type  String
    :param out_string_format:   Takes (html link to element page, search-url, element dict object), and
                                returns formatted output to be displayed per element in notification.
    :type  Function
    :param elmnts_out_file:     File path of elements output.
    :type  String
    :param history_file:        File path for history of element urls.
    :type  String
    :param searches_file:       File path that specifies input url and names.
    :type  String
    :param max_pages:           Maximum number of pages to scrape per search.
    :type  int
    :param email:               Email to receive notifications and error messages.
    :type  String
    :param max_notifi_entries:  Maximum number of elements to be displayed in notification.
    :type  int
    :param push_notification:   Wether to send push notification on new hits.
    :type  boolean
    :param pushover_token:      Pushover API-token to be used for notifications.
    :type  String
    :param email_notification:  Wether to send notifications by email on hits.
    :type  boolean
    """

    try:
        searches = i_o_setup(elmnts_out_file, history_file, searches_file)
        new_elmnts = get_ids(searches, elmnts_out_file, get_elmnts_func, get_attrs_func, get_next_url_func, max_pages,
                             json_request)
        if new_elmnts:
            alert_write_new(site_name, new_elmnts, searches, out_string_format,
                            push_notifications=push_notification, email_notifications=email_notification,
                            output_file=history_file, max_notif_entries=max_notifi_entries,
                            pushover_token=pushover_token)
    except Exception:
        traceback.print_exc()
        # if email_exceptions:
        #     notify.mail(email, 'Feil under kjøring av hybelskript', "{}".format(traceback.format_exc()))
        # TODO: Create module that can be called to determine when (since how long?) to send error (aka propagate
        # error to cronjob) on email.


def write_with_timestamp(links, filename):
    timestamp = arrow.now().format('YYYY-MM-DD HH:mm:ss')
    with open(filename, 'a') as fp:
        fp.write(f'{timestamp}{links}\n\n')

def get_ids(searches, elmnts_out_file, get_elmnts_func, get_attrs_func, get_next_url_func, max_pages,
            json_request=False):
    cur_elements = {}

    for search in searches:
        cur_elements = process_page(search['url'], cur_elements, get_elmnts_func, get_attrs_func,
                               get_next_url_func, search, max_pages, page_num=1, json_request=json_request)

                               # , cur_elements, search, 1)

    new_elements = compare_results(elmnts_out_file, cur_elements)
    return new_elements

def compare_results(I_O_FILE, cur_elements):
    prev_elements = {}
    with open(I_O_FILE, 'r+') as fp:
        if fp.read() != "":
            fp.seek(0)
            try:
                prev_elements = json.load(fp)
            except Exception as e:
                os.remove(I_O_FILE)
                raise IOError('Could not read json. Deleting file.') from e

    with open(I_O_FILE, 'w+') as fp:
        json.dump(cur_elements, fp)

    # Alert if new elements added (mere difference could be due to deletion)
    if len(cur_elements.keys() - prev_elements.keys()) > 0:
        new = {}
        for (element_id, element) in cur_elements.items():
            if element_id not in prev_elements:
                new[element_id] = element
        return list(new.values())

    return None
    

def i_o_setup(elements_file, history_file, search_file):
    # Check that input file exists
    if not Path(search_file).exists():
        raise Exception(f'Input file \'{search_file}\' does not exist.')
    
    # Create directories if not existing
    Path(elements_file).parents[0].mkdir(parents=True, exist_ok=True)
    Path(history_file).parents[0].mkdir(parents=True, exist_ok=True)
    Path(search_file).parents[0].mkdir(parents=True, exist_ok=True)

    # Create files if not existing
    Path(elements_file).touch(exist_ok=True)
    Path(history_file).touch(exist_ok=True)
    Path(search_file).touch(exist_ok=True)

    # Get search urls and search names from file
    search_dict = []
    with open(search_file, 'r') as fp:
        search = fp.readline().strip('\n').split()
        if len(search) == 0:
            raise Exception('Please add url to search url file')
        elif len(search) == 1:
            raise Exception(f'Please enter name of search in search url file "{search_file}"')

        while search != []:
            search = {'url': search[0], 'name': ' '.join(search[1:])}
            search_dict.append(search)
            search = fp.readline().strip('\n').split()

    return search_dict


# Send push notification for maximum max_notif_entries, and store all links in archive file
def alert_write_new(site, elements, searches, string_format, push_notifications, email_notifications,
                    max_notif_entries, pushover_token=None, output_file='history.txt'):
    subj = f'Nye treff på {site}-søket ditt'
    notify_text = f'Det er blitt lagt til {len(elements)} nye annonse(r) på {site}-søket ditt.\n\n'

    archive_links = ''
    for i in range(0, len(elements)):
        element = elements[i]

        # Only store simple format in history (but store all)
        archive_links += '\n– {}\n'.format(element["href"])
        if i >= max_notif_entries:
            continue

        element_url = pyshorteners.Shortener().tinyurl.short(element["href"])
        search_url = pyshorteners.Shortener().tinyurl.short(element["search"]["url"])
        element_link = f'<a href="{element_url}">{element["title"]}</a>'
        search_link = f'<a href="{search_url}">søk: \'{element["search"]["name"]}\'</a>'

        notify_text += f'\n{string_format(element_link, search_link, element)}\n'

    if len(elements) > max_notif_entries:
        notify_text += f'\n... og {len(elements) - max_notif_entries} annonse(r) til.\n'

    short_urls = [[pyshorteners.Shortener().tinyurl.short(search['url']), search['name']] for search in searches]
    notify_text += f'\n\nLenke til søk:\n'

    for (url, name) in short_urls:
        notify_text += f'<a href="{url}">\'{name}\'</a>\n'

    notify_text += f'\nVennlig hilsen,\n{site}-roboten'

    if push_notifications:
        if not pushover_token:
            raise Exception("Pushover api token required")
        notify.push_notification(notify_text, pushover_token)
    if email_notifications:
        notify.mail(EMAIL, subj, notify_text)
    if output_file:
        write_with_timestamp(archive_links, output_file)


def process_page(page_url, elmnts_dict, get_elmnts_func, get_attrs_func, get_next_url_func, search, max_pages,
                 page_num, json_request=False):
    if json_request:
        page = requests.get(page_url).json()
    else:
        page = BROWSER.get(page_url).soup
    elmnts = get_elmnts_func(page)

    for e in elmnts:
        elmnts_dict = get_attrs_func(e, elmnts_dict, search)

    next_page_url = get_next_url_func(page, page_url)
    if next_page_url:
        if page_num > max_pages:
            raise Exception(f'Max page limit of {max_pages} reached without reaching end of search. ')
        page_num += 1
        process_page(next_page_url, elmnts_dict, get_elmnts_func,
                     get_attrs_func, get_next_url_func, search, max_pages, page_num, json_request)

    return elmnts_dict
