import json
from pathlib import Path
import pyshorteners
import notify
import arrow


def write_with_timestamp(links, filename):
    timestamp = arrow.now().format('YYYY-MM-DD HH:mm:ss')
    with open(filename, 'a') as fp:
        fp.write(f'{timestamp}{links}\n\n')

def get_ids(searches, ads_out_file, scrape_func):
    cur_ads = {}

    for search in searches:
        cur_ads = scrape_func(search['url'], cur_ads, search, 1)

    new_ad_dicts = compare_results(ads_out_file, cur_ads)
    return new_ad_dicts

def compare_results(FILE_NAME, cur_ads):
    prev_ads = {}
    with open(FILE_NAME, 'r+') as fp:
        if fp.read() != "":
            fp.seek(0)
            try:
                prev_ads = json.load(fp)
            except Exception as e:
                os.remove(FILE_NAME)
                raise IOError('Could not read json. Deleting file.') from e

    with open(FILE_NAME, 'w+') as fp:
        json.dump(cur_ads, fp)

    # Alert if new ads added (mere difference could be due to deletion)
    if len(cur_ads.keys() - prev_ads.keys()) > 0:
        new = {}
        for (ad_id, ad_dict) in cur_ads.items():
            if ad_id not in prev_ads:
                new[ad_id] = ad_dict
        return list(new.values())

    return None
    

def i_o_setup(ADS_FILE, HISTORY_FILE, SEARCH_URL_FILE):
    # Create files if not existing
    Path(ADS_FILE).touch(exist_ok=True)
    Path(HISTORY_FILE).touch(exist_ok=True)
    Path(SEARCH_URL_FILE).touch(exist_ok=True)

    search_dict = []

    # Get search url from file
    with open(SEARCH_URL_FILE, 'r') as fp:
        search = fp.readline().strip('\n').split()
        if len(search) == 0:
            raise Exception('Please add url to search url file')

        try:
            while search != []:
                search = {'url': search[0], 'name': search[1]}
                search_dict.append(search)

                search = fp.readline().strip('\n').split()
        except IndexError:
            raise Exception(f'Please enter name of search in search url file "{SEARCH_URL_FILE}"')

    return search_dict


# Send push notification for maximum max_notif_entries, and store all links in archive file
def alert_write_new(site, ad_dicts, searches, ad_string_format, push_notifications, email_notifications,
                    output_file, max_notif_entries, api_token=None):
    subj = f'Nye treff på {site}-søket ditt'
    notify_text = f'Det er blitt lagt til {len(ad_dicts)} nye annonse(r) på {site}-søket ditt.\n\n'

    archive_links = ''
    for i in range(0, len(ad_dicts)):
        ad_dict = ad_dicts[i]

        # Only store simple format in history (but store all)
        archive_links += '\n– {}\n'.format(ad_dict["href"])
        if i >= max_notif_entries:
            continue

        ad_url = pyshorteners.Shortener().tinyurl.short(ad_dict["href"])
        search_url = pyshorteners.Shortener().tinyurl.short(ad_dict["search"]["url"])
        ad_link = f'<a href="{ad_url}">{ad_dict["title"]}</a>'
        search_link = f'<a href="{search_url}">søk: \'{ad_dict["search"]["name"]}\'</a>'

        notify_text += f'\n{ad_string_format(ad_link, search_link, ad_dict)}\n'

    if len(ad_dicts) > max_notif_entries:
        notify_text += f'\n... og {len(ad_dicts) - max_notif_entries} annonse(r) til.\n'

    short_urls = [pyshorteners.Shortener().tinyurl.short(search['url']) for search in searches]
    notify_text += f'\n\nLenke til søk:\n'

    for i in range(0, len(short_urls)):
        notify_text += f'<a href="{short_urls[i]}">\'{ad_dict["search"]["name"]}\'</a>\n'

    notify_text += f'\nVennlig hilsen,\n{site}-roboten'

    if push_notifications:
        if not api_token:
            raise Exception("Pushover api token required")
        notify.push_notification(notify_text, api_token)
    if email_notifications:
        notify.mail(EMAIL, subj, notify_text)
    if output_file:
        write_with_timestamp(archive_links, output_file)