import creators
import os
import sys
import datetime
import requests
import utils
from urllib.parse import urlparse
from io import BytesIO
from PIL import Image
from local_settings import *

BASE_FOLDER = os.path.dirname(__file__)
COMIC_FOLDER = os.path.join(BASE_FOLDER, "downloads")

urls = {
    "for_better_or_worse": "http://bbs.amuniversal.com/web/Content/Comic_Strips/For_Better_Or_For_Worse/fb<date>.tif",
    "peanuts": "http://bbs.amuniversal.com/web/Content/Comic_Strips/Peanuts/pt<date>.tif",
    "blondie": "http://bbs.rbma.com/repo/Blondie/<year>/<month>/BLT<date>.tif",
    "pearls_before_swine": "http://bbs.amuniversal.com/web/Content/UFS_Daily_Comics/Pearls_Before_Swine_Dailies/pb<date>.tif",
    "beetle_bailey": "http://bbs.rbma.com/repo/Beetle_Bailey/<year>/<month>/BBT<date>.tif",
    "born_loser": "http://bbs.amuniversal.com/web/content/NEA_Full_Service/Comics/Born_Loser_Dailies/bnl<date>.tif",
    "dilbert": "http://bbs.amuniversal.com/web/Content/Comic_Strips/Dilbert/dt<date>.tif",
    "frank_and_ernest": "http://bbs.amuniversal.com/web/content/NEA_Full_Service/Comics/Frank_n_Ernest_Dailies/fk<date>.tif",
    "hagar_the_horrible": "http://bbs.rbma.com/repo/Hagar_The_Horrible/<year>/<month>/HGT<date>.tif",
    "garfield": "http://bbs.amuniversal.com/web/Content/Comic_Strips/Garfield/ga<date>.tif",
    "family_circus": "http://bbs.rbma.com/repo/Family_Circus/<year>/<month>/FCT<date>.tif",
    "bridge": "http://bbs.rbma.com/repo/Becker_Bridge/<year>/<month>/Beck_<date>.tif",
    "sudoku": "http://bbs.rbma.com/repo/Sudoku_Combined/<year>/<month>/Sudoku_Combined<date>.tif",
    "hocus": "http://bbs.rbma.com/repo/Hocus_Focus/<year>/<month>/HOT<date>.tif",
    "crossword": "https://bbs.amuniversal.com/web/Content/NEA_Full_Service/Puzzles/NEA%20Daily%20Crossword/neas<date>.tif"
}

sunday_urls = {
    "bridge": "http://bbs.rbma.com/repo/Becker_Bridge/<year>/<month>/Beck_<date>.tif",
    "sudoku": "http://bbs.rbma.com/repo/Sudoku_Combined/<year>/<month>/Sudoku_Combined<date>.tif",
}


def get_creds_for_server(server_name):
    if server_name in creds.keys():
        return creds[server_name]
    return None


def build_url(comic_name, date_object, server_name):
    initial_url = urls[comic_name]
    fixed_url = None
    if "rbma" in server_name:
        fixed_url = (
            initial_url.replace("<year>", str(date_object.year))
            .replace("<month>", str(date_object.month).zfill(2))
            .replace("<date>", date_object.strftime("%Y%m%d"))
        )
    elif "amuniversal" in server_name:
        fixed_url = initial_url.replace("<date>", date_object.strftime("%y%m%d"))
    return fixed_url


def get_filetype(filename):
    name, extension = os.path.splitext(filename)
    return extension


def get_filename(url):
    parts = url.split("/")
    fname_parts = parts[-1].split(".")
    # if the file we are downloading is a tif
    # we convert that to a jpg
    if fname_parts[1] == "tif":
        return fname_parts[0] + ".jpg"
    else:
        return parts[-1]


def download(url, filename, creds_for_server):
    filepath = os.path.join(COMIC_FOLDER, filename)
    if not os.path.exists(filepath):
        r = requests.get(url, auth=(creds_for_server["username"], creds_for_server["password"]))
        if r.status_code == 404:
            return {"status": "missing"}
        filetype = get_filetype(filepath)
        if filetype == ".jpg":
            try:
                bytes_obj = BytesIO(r.content)
                i = Image.open(bytes_obj)
            except OSError:
                return {"status": "failed", "name": filename}
            i.save(filepath, "JPEG")
        elif filetype in [".txt", ".zip"]:
            with open(filepath, "wb") as f:
                f.write(r.content)
        return {"status": "downloaded"}
    else:
        return {"status": "skipped"}


def get_corrected_url(url):
    url_start = url[:-4]
    url_end = url[-4:]
    return "{}_crx{}".format(url_start, url_end)


def main():
    try:
        datestr = sys.argv[1:][0]
    except IndexError:
        print("Missing Date Value")
        sys.exit(1)

    status = {"downloaded": 0, "failed": 0, "skipped": 0, "failed_files": [], "corrections": 0}

    date_obj = datetime.datetime.strptime(datestr, "%Y-%m-%d")
    date_list = utils.build_dates(date_obj)

    for comic_key, comic_url in urls.items():
        server_name = urlparse(comic_url).netloc
        creds_for_server = get_creds_for_server(server_name)
        if creds_for_server:
            for the_date in date_list:
                url = build_url(comic_key, the_date, server_name)
                filename = get_filename(url)
                result = download(url, filename, creds_for_server)
                if result["status"] == "missing":
                    # if this is an amuniversal site, we can try appending _crx as a correction
                    correction_url = get_corrected_url(url)
                    result = download(correction_url, filename, creds_for_server)
                    if result["status"] == "downloaded":
                        status[result["status"]] += 1
                    else:
                        status["failed"] += 1
                else:
                    status[result["status"]] += 1
                if result["status"] == "failed":
                    status["failed_files"].append(result["name"])
        else:
            print("Can't find creds for server: ", server_name)
            sys.exit(1)

    for sunday_comic_key, sunday_comic_url in sunday_urls.items():
        server_name = urlparse(sunday_comic_url).netloc
        creds_for_server = get_creds_for_server(server_name)
        if creds_for_server:
            sunday_date = utils.get_sunday_date(date_obj)
            sunday_url = build_url(sunday_comic_key, sunday_date, server_name)
            filename = get_filename(sunday_url)
            result = download(sunday_url, filename, creds_for_server)
            try:
                status[result["status"]] += 1
            except KeyError:
                # print(result)
                pass
            if result["status"] == "failed":
                status["failed_files"].append(result["name"])

    cap_status = creators.download_files("cap", datestr, date_list[-1].strftime("%Y-%m-%d"))
    rubes_status = creators.download_files("rub", datestr, date_list[-1].strftime("%Y-%m-%d"))
    bc_status = creators.download_files("bc", datestr, date_list[-1].strftime("%Y-%m-%d"))

    # comic_builder_montana.move_comics(date_obj)

    status["downloaded"] += cap_status["downloaded"]
    status["downloaded"] += rubes_status["downloaded"]
    status["downloaded"] += bc_status["downloaded"]
    status["failed"] += cap_status["failed"]
    status["failed"] += rubes_status["failed"]
    status["failed"] += bc_status["failed"]

    print("Downloaded: {}".format(status["downloaded"]))
    print("Skipped: {}".format(status["skipped"]))
    print("Failed: {}".format(status["failed"]))
    print("Corrections: {}".format(status["corrections"]))
    if status["failed"]:
        print("Failed Files: ", status["failed_files"])


if __name__ == "__main__":
    main()
