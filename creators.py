import json
import sys
import os
import datetime
from creators_py import creators_api

BASE_FOLDER = os.path.dirname(__file__)
DOWNLOAD_FOLDER = os.path.join(BASE_FOLDER, "downloads")

creators_api.api_key = "31A1CC02E73B19F8E451D74DFAC5ED94C4AA53B1"


def get_image_name_for_comic(comic_key):
    data = {
        "cap": "TIF Hi Res Strip",
        "rub": "TIF Hi Res Panel",
        "bc": "TIF Hi Res Strip",
    }
    if comic_key in data.keys():
        return data[comic_key]
    return False


def get_releases(comic_code, start_date, end_date):
    releases = creators_api.get_releases(comic_code, start_date=start_date, end_date=end_date)
    file_key = "{}_{}_{}.json".format(comic_code, start_date, end_date)
    file_path = os.path.join(BASE_FOLDER, "cache", file_key)
    with open(file_path, "w") as f:
        json.dump(releases, f)
    return releases


def get_url(data, name):
    for a_file in data["files"]:
        if a_file["description"] == name:
            return a_file["url"]


def get_filename(data, name):
    for a_file in data["files"]:
        if a_file["description"] == name:
            return a_file["filename"]


def get_file_date(data):
    date_str, time_str = data["release_date"].split(" ")
    return datetime.datetime.strptime(date_str, "%Y-%m-%d")


def get_comic_name(data):
    return data["file_code"]


def download_files(code, start_date, end_date):
    print("Processing comics for: {}".format(code))
    releases = get_releases(code, start_date, end_date)
    print("Found {} files on the server for code: {}".format(len(releases), code))
    print(releases)
    status = {"downloaded": 0, "failed": 0, "skipped": 0}
    image_name = get_image_name_for_comic(code)
    for item in releases:
        url = get_url(item, image_name)
        file_date = get_file_date(item)
        filepath = "{}{}.jpg".format(code, file_date.strftime("%y%m%d"))
        filepath = os.path.join(DOWNLOAD_FOLDER, filepath)
        if not os.path.exists(filepath):
            if creators_api.download_file(url, filepath):
                status["downloaded"] += 1
            else:
                status["failed"] += 1
        else:
            print("Skipping...")
            status["skipped"] += 1
    return status


if __name__ == '__main__':
    start_date = sys.argv[1:][0]
    start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    delta = datetime.timedelta(days=6)
    end_date_obj = start_date_obj + delta
    end_date = end_date_obj.strftime("%Y-%m-%d")
    download_files("cap", start_date, end_date)
