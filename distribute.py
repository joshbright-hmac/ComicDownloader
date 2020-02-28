import zipfile
import sys
import shutil
import os
import datetime
import utils

# this file
BASE_FOLDER = os.path.dirname(__file__)

# where our downloaded comics are
BASE_COMIC_FOLDER = os.path.join(BASE_FOLDER, "downloads")

# where our templates are stored at
BASE_INDESIGN_FOLDER = os.path.join(BASE_FOLDER, "templates")

# a link to the actual template
BASE_INDESIGN_COMIC_TEMPLATE = os.path.join(BASE_FOLDER, "templates", "IL_Comic_Template.indd")
BASE_INDESIGN_DIVERSIONS_TEMPLATE = os.path.join(BASE_FOLDER, "templates", "IL_Diversions_Template.indd")
BASE_INDESIGN_DIVERSIONS_SUNDAY_TEMPLATE = os.path.join(BASE_FOLDER, "templates", "IL_Diversions_Sunday_Template.indd")

# where we are going to put our dated folders
BASE_WORK_FOLDER = os.path.join(BASE_FOLDER, "work")

# mapping of names of comics to what the filename is
comic_files = {
    "comics": {
        "blondie": ["BLT<full_date>.jpg"],
        "beetle_bailey": ["BBT<full_date>.jpg"],
        "bc": ["bc<date>.jpg"],
        "the_born_loser": ["bnl<date>.jpg"],
        "andy_capp": ["cap<date>.jpg"],
        "dilbert": ["dt<date>.jpg"],
        "for_better_or_worse": ["fb<date>.jpg"],
        "frank_ernest": ["fk<date>.jpg"],
        "hagar_the_horrible": ["HGT<full_date>.jpg"],
        "pearls_before_swine": ["pb<date>.jpg"],
        "peanuts": ["pt<date>.jpg"],
        "rubes": ["rub<date>.jpg"],
        "garfield": ["ga<date>.jpg"],
        "family_circus": ["FCT<full_date>.jpg"],
    },
    "diversions": {
        "crossword": ["neas<date>.jpg"],
        "bridge": ["beck_<full_date>.jpg"],
        "sudoku": ["Sudoku_Combined<full_date>.jpg"],
        "hocus_focus": ["HOT<full_date>.jpg"],
        "jumble": ["<full_date>pzjud-a.tif"]
    },
}

sunday_comic_files = {
    "diversions": {
        "bridge": ["beck_<full_date>.jpg"],
        "sudoku": ["Sudoku_Combined<full_date>.jpg"]
    }
}


def get_lines(filepath):
    result = []
    with open(filepath, "r") as f:
        for line in f.readlines():
            result.append(line)
    return result


def process_crosswords(date_list):
    short_date_format = "%y%m%d"
    date_str = date_list[0].strftime(short_date_format)
    indesign_parent_folder = os.path.join(
        BASE_INDESIGN_FOLDER, date_list[0].strftime("%Y-%m-%d")
    )
    zip_filename = "neap{}_week".format(date_str)
    zip_ref = zipfile.ZipFile(
        os.path.join(BASE_COMIC_FOLDER, zip_filename + ".zip"), "r"
    )
    zip_ref.extractall(BASE_COMIC_FOLDER)
    zip_ref.close()
    for d in date_list:
        short_date_str = d.strftime(short_date_format)
        date_folder = os.path.join(indesign_parent_folder, d.strftime("%Y-%m-%d"))
        cross_puzzle = os.path.join(
            BASE_COMIC_FOLDER, zip_filename, "neap{}g.tif".format(short_date_str)
        )
        cross_answer = os.path.join(
            BASE_COMIC_FOLDER, zip_filename, "neap{}ag.tif".format(short_date_str)
        )
        cross_text = os.path.join(
            BASE_COMIC_FOLDER, zip_filename, "neap{}.txt".format(short_date_str)
        )
        shutil.copy(cross_puzzle, os.path.join(date_folder, "cross_puzzle.tif"))
        shutil.copy(cross_answer, os.path.join(date_folder, "cross_answer.tif"))
        shutil.copy(cross_text, os.path.join(date_folder, "cross_text.txt"))


def process_dear_abby(parent_folder):
    dear_abby_path = os.path.join(parent_folder, "dear_abby.txt")
    dear_abby_headline_path = os.path.join(parent_folder, "dear_abby_headline.txt")
    dear_abby_body_path = os.path.join(parent_folder, "dear_abby_body.txt")
    dear_abby_content = get_lines(dear_abby_path)
    body_content = "".join(dear_abby_content[4:])

    with open(dear_abby_headline_path, "w") as headline_file:
        headline_file.write(dear_abby_content[3])

    with open(dear_abby_body_path, "w") as body_file:
        body_file.writelines(body_content)


def process_astrograph(parent_folder):
    astropath = os.path.join(parent_folder, "astrograph.txt")
    lines = get_lines(astropath)
    astro_body = os.path.join(parent_folder, "astro_body.txt")
    with open(astro_body, "w") as f:
        f.writelines(lines[3:])


def process_bridge(parent_folder):
    bridge_path = os.path.join(parent_folder, "bridge.txt")
    bridge_headline_path = os.path.join(parent_folder, "bridge_headline.txt")
    bridge_body_path = os.path.join(parent_folder, "bridge_body.txt")
    bridge_content = get_lines(bridge_path)

    with open(bridge_headline_path, "w") as headline_file:
        headline_file.write(bridge_content[3])

    with open(bridge_body_path, "w") as body_file:
        body_file.writelines(bridge_content[5:])


def process_comic(comic_type, comic_name, file_name, comic_date, parent_folder):
    # single comic
    comic_date_str = comic_date.strftime("%y%m%d")
    full_date_str = comic_date.strftime("%Y-%m-%d")
    smashed_date_str = full_date_str.replace("-", "")
    # get the file type so we can use it later to build the path for the comic
    file_type = file_name.split(".")[1]

    fixed_filename = file_name.replace("<date>", comic_date_str).replace(
        "<full_date>", smashed_date_str
    )

    fixed_path = os.path.join(BASE_COMIC_FOLDER, fixed_filename)

    # path to the comic after we've copied to the new folder
    final_comic_name = "{}.{}".format(comic_name, file_type)
    indesign_comic_path = os.path.join(parent_folder, comic_type, final_comic_name)

    shutil.copy(fixed_path, indesign_comic_path)

    return (comic_name, final_comic_name)


def move_comics(date_obj):
    date_list = utils.build_dates(date_obj)
    date_str = date_obj.strftime("%Y-%m-%d")
    print("Processing Comics for {}".format(date_str))

    # create parent folder for indesign files
    indesign_parent_folder = os.path.join(BASE_WORK_FOLDER, date_str)
    if not os.path.exists(indesign_parent_folder):
        os.mkdir(indesign_parent_folder)

    # create folders for each day
    for d in date_list:
        date_folder = os.path.join(indesign_parent_folder, d.strftime("%Y-%m-%d"))
        if not os.path.exists(date_folder):
            os.mkdir(date_folder)

            for k in comic_files.keys():
                specific_comic_path = os.path.join(date_folder, k)
                os.mkdir(specific_comic_path)

        # copy indesign template to this folder
        shutil.copy(
            BASE_INDESIGN_COMIC_TEMPLATE,
            os.path.join(date_folder, "comics", "{}.indd".format(d.strftime("%Y-%m-%d")))
        )
        shutil.copy(
            BASE_INDESIGN_DIVERSIONS_TEMPLATE,
            os.path.join(date_folder, "diversions", "{}.indd".format(d.strftime("%Y-%m-%d")))
        )

        # copy comic files over to dated folder
        for comic_type, comic_data in comic_files.items():
            for k, v in comic_data.items():
                # if we just have one value for our key, its just a single file for that comic
                if len(v) == 1:
                    process_comic(comic_type, k, v[0], d, date_folder)
                elif len(v) == 2:
                    # otherwise we may have 2 files
                    # this is mainly for bridge
                    for double_comic in v:
                        process_comic(comic_type, k, double_comic, d, date_folder)

    # process sunday comics
    sunday_date = utils.get_sunday_date(date_obj)
    sunday_date_str = sunday_date.strftime("%Y-%m-%d")
    sunday_date_path = os.path.join(BASE_WORK_FOLDER, date_str, sunday_date_str)
    if not os.path.exists(sunday_date_path):
        os.mkdir(sunday_date_path)
        os.mkdir(os.path.join(sunday_date_path, "diversions"))

    shutil.copy(
        BASE_INDESIGN_DIVERSIONS_SUNDAY_TEMPLATE,
        os.path.join(sunday_date_path, "diversions", "{}.indd".format(sunday_date_str))
    )

    for comic_type, comic_data in sunday_comic_files.items():
        for k, v in comic_data.items():
            process_comic(comic_type, k, v[0], sunday_date, sunday_date_path)


def main():
    try:
        datestr = sys.argv[1:][0]
        dateobj = datetime.datetime.strptime(datestr, "%Y-%m-%d")
        move_comics(dateobj)
    except IndexError:
        print("Missing a date value")
        sys.exit()


if __name__ == "__main__":
    main()
