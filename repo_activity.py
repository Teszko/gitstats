#!/usr/bin/python3

import argparse
from itertools import groupby
import datetime as dt
import matplotlib.pyplot as plt
import urllib
import json
import math
from time import sleep


class Options:
    lower_limit = 2010
    lower_month = 1
    upper_limit = 2017  # will be replaced by first and last commit date
    upper_month = 12
    from_year = 0
    to_year = 0
    display_months = False
    color = 'blue'
    bar_width = 27
    x_labels_padding = 1
    url = ''
    log = False
    years = []


def handle_arguments(options):
    parser = argparse.ArgumentParser(
        description='Program to analyze a Git repository\'s commit frequency over a time interval',
        epilog="     Example call: "+__file__+" Teszko/githubstats -t 2017 --color \'red\'"
        )
    parser.add_argument(
        '--log', '-l',
        action='store_true',
        help='sets the y-axis to be log scale.'
        )
    parser.add_argument(
        '--display-months', '-m',
        action='store_true',
        help='labels months on x-axis'
        )
    parser.add_argument('--from-year', '-f', type=int, default=0)
    parser.add_argument('--to-year', '-t', type=int, default=0)
    parser.add_argument('--bar-width', '-b', type=int, default=options.bar_width)
    parser.add_argument('--color', '-c', default=options.color)
    parser.add_argument('repo', help='GitHub :owner/:repo pair')

    args = parser.parse_args()

    options.bar_width = int(args.bar_width)
    options.color = format(args.color)
    options.url = "https://api.github.com/repos/"+format(args.repo)+"/stats/code_frequency"
    options.to_year = args.to_year
    options.from_year = args.from_year
    if args.log:
        options.log = True
    if args.display_months:
        options.display_months = True


def date_is_in_group(date, group):
    for index, element in enumerate(group):
        if date[0] == element[0] and date[1] == element[1]:
            return index
    else:
        return -1


def plot_bar_graph (options, plot_dates, plot_values):
    plt.bar(plot_dates, plot_values, options.bar_width, color=options.color, log=options.log)
    plt.xticks(plot_dates, options.years, rotation='vertical')
    # plt.xlim([min(plot_dates) - 1, max(plot_dates) + 1])

    interval = math.ceil(max(plot_values) / 10)
    digits = math.floor(math.pow(10,math.floor(math.log10(interval) + 0)))
    interval = math.ceil(interval / digits) * digits

    # plt.yticks(range(0, int(max(plot_values) * 1.05), interval))
    plt.ylabel('Anzahl geänderter Zeilen Code')
    plt.show()


def request_data(options):
    res_code = 0
    response = ''

    while res_code != 200:
        # loop until github is done computing stats.
        response = urllib.request.urlopen(options.url)
        res_code = response.getcode()

        if res_code != 200 and res_code != 202:
            print("Error quering github stats api. ", res_code)
            exit(1)

        sleep(0.2)
    data = json.loads(response.read().decode('UTF-8'))
    return data


def parse_json(data):
    year_month_pair = []
    week_total = []

    for e in data:
        year = int(dt.datetime.fromtimestamp(e[0]).strftime('%Y'))
        month = int(dt.datetime.fromtimestamp(e[0]).strftime('%m'))

        changes = int(e[1]) - int(e[2])
        if changes != 0:
            week_total.append(int(changes))
            year_month_pair.append([year, month])

    year_month_pair_cleaned = []
    month_total = []

    padding = 0
    for key, group in groupby(year_month_pair):
        group_list = list(group)
        group_len = len(group_list)
        element = group_list[0]

        year_month_pair_cleaned.append(element)
        month_total.append(sum(week_total[padding:padding+group_len]))
        padding += group_len

    return year_month_pair_cleaned, month_total


def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 2
    ym_end = (12 * end_year + end_month - 1 - 12)
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m+1


def prepare_data_for_plot(options, year_month_pairs, month_total):
    if options.from_year:
        options.lower_limit = options.from_year
    else:
        options.lower_limit = year_month_pairs[0][0]
        options.lower_month = year_month_pairs[0][1]

    if options.to_year:
        options.upper_limit = options.to_year
    else:
        options.upper_limit = year_month_pairs[-1][0]
        options.upper_month = year_month_pairs[-1][1]

    plt_dates = []
    plt_values = []
    current_year = 0

    if not options.display_months:
        options.years.extend(['.']*options.x_labels_padding)

    for month in month_year_iter(options.lower_month, options.lower_limit, options.upper_month, options.upper_limit):
        year = int(month[0])
        month = int(month[1])

        if not options.display_months:
            if year != current_year:
                options.years.append(str(year))
                current_year = year
            else:
                options.years.append('')
        else:
            options.years.append(dt.date(year, month, 1).strftime('%b %y'))

        index = date_is_in_group([year, month], year_month_pairs)
        if index != -1:
            plt_values.append(month_total[index])
        else:
            plt_values.append(0)

        plt_dates.append(dt.datetime(year=year, month=month, day=1))

    if not options.display_months:
        options.years = options.years[:-options.x_labels_padding]
    return plt_dates, plt_values


if __name__ == "__main__":
    options = Options()
    handle_arguments(options)
    data = request_data(options)
    year_month_pairs, month_total = parse_json(data)
    plot_dates, plot_values = prepare_data_for_plot(options, year_month_pairs, month_total)
    plot_bar_graph(options, plot_dates, plot_values)
