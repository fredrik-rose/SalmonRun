"""
Extracts salmon run statistics from Swedish Lapland Fishing.
"""
import argparse
import datetime
import os
import pathlib
import re
import requests
import traceback

from bs4 import BeautifulSoup


URL = "http://www.swedishlaplandfishing.com/sv/fishing/om-fisket/laxvandringen/"
RIVERS = ("byskealven",
          "kalixalven",
          "linaalven",
          "pitealven-fallfors",
          "pitealven-sikfors",
          "ricklean",
          "ranealven",
          "tornealven",
          "aby-alv",
          "angesan")


def get_salmon_statistics():
    """ Extracts salmon run statistics from the server. """
    def parse_year(string):
        """ Parses the year from a string (with an expected format). """
        match = re.search("name:'([0-9]+)',", string)
        return match.group(1) if match else None

    def parse_data(string, year):
        """ Parses the data from a string (with an expected format). """
        data = {'dates': [], 'counts': []}
        match = re.search("data:\[(.*)\]", string)
        if match:
            raw_elements = match.group(1).replace('[', '').split('],')
            for element in raw_elements:
                match = re.search("Date.UTC\(([0-9]+),([0-9]+),([0-9]+)\),([0-9]+)", element)
                if match:
                    month = int(match.group(2)) + 1
                    day = int(match.group(3))
                    count = int(match.group(4))
                    try:
                        data['dates'].append(datetime.date(int(year), month, day))
                        data['counts'].append(count)
                    except ValueError:
                        traceback.print_exc()
        return data

    statistics = {}
    for river in RIVERS:
        soup = BeautifulSoup(requests.get(URL + river).content, "html.parser")
        script = soup.find("script", string=re.compile("Highcharts.Chart")).string
        script_single_line = script.replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '')
        raw = re.search('series:\[(.*)\]', script_single_line).group(1)
        raw_groups = raw.replace('{', '').split('},')
        statistics[river] = {}
        for group in raw_groups:
            year = parse_year(group)
            if year:
                statistics[river][year] = parse_data(group, year)
    return statistics


def store_salmon_statistics(statistics, file_name):
    """ Stores the salmon run statistics to a file. """
    def list_to_string(lst):
        """ Converts a list of elements to a comma separated string. """
        return ",".join(str(e) for e in lst)

    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, 'w+') as file:
        file.write(list_to_string(statistics['dates']))
        file.write("\n")
        file.write(list_to_string(statistics['counts']))
        file.write("\n")


def main():
    """ Program entry point. """
    parser = argparse.ArgumentParser("Extracts salmon run statistics from Swedish Lapland Fishing")
    parser.add_argument("--output", type=pathlib.Path,
                        default=pathlib.Path(__file__).absolute().parent / 'SwedishLaplandFishing',
                        help="Path to the output directory")
    args = parser.parse_args()
    statistics = get_salmon_statistics()
    for river, years in statistics.items():
        for year, data in years.items():
            if data['dates'] and data['counts']:
                store_salmon_statistics(data, str(args.output / (river + year + '.txt')))
            else:
                print("WARNING: No statistics available for river {}, year {}".format(river, year))


if __name__ == "__main__":
    main()
