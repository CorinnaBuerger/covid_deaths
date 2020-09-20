from datetime import datetime
from matplotlib.dates import DateFormatter  # type: ignore
from sys import argv, exit
import matplotlib.pyplot as plt             # type: ignore
import pandas as pd                         # type: ignore
import requests

usage_msg = ("""Usage: covid_viewer <country> <total/daily> [--update] [--help]
    --update\t\tupdate the local COVID data copy from JHU
    --help\t\tdisplay this help message

Copyright (c) 2020 by Corinna Buerger""")

JHU_RESPONSE_MIN_LENGTH = 100000
JHU_UPDATED_DATA_FILENAME = "covid_deaths.csv"  # NOTE: potentially overrides


class CovidData():
    def __init__(self, infile="covid_deaths.csv"):
        # pd.DataFrame for total death cases
        self.df_total = pd.read_csv(infile)
        self.start = self.df_total.columns[4]
        self.today = self.df_total.columns[-1]
        self.dates = pd.date_range(self.start, self.today).date

        # no country selected yet
        self.selected = None
        self.world_data = None

        # will be filled and transformed into self.df_daily
        self.daily_deaths = {}

        # DataFrame for daily death cases
        self.df_daily = self.get_daily_deaths()

        # adds worldwide death cases to both DataFrames
        self.get_world_deaths()

    def get_world_deaths(self):
        # append to DataFrame for total deaths
        world_total = {}
        for column in self.df_total.columns:
            world_total[column] = None

        for col_idx in range(0, len(self.df_total.columns)):
            column = self.df_total.columns[col_idx]
            if col_idx < 4:
                # here is no data for death cases
                world_total[column] = "World"
            else:
                for row_idx in range(0, len(self.df_total)):
                    if row_idx == 0:
                        # for the first row (country) in each column (day)
                        # the death cases will be assigned
                        world_total[column] = self.df_total.iloc[row_idx,
                                                                 col_idx]
                    else:
                        # for all the other rows (countries) in each column
                        # (day) the death cases will be added to the previous
                        # one
                        world_total[column] += self.df_total.iloc[row_idx,
                                                                  col_idx]

        self.df_total = self.df_total.append(world_total, ignore_index=True)

        # append to DataFrame for daily deaths (works just like for total
        # deaths but uses self.df_daily)
        world_daily = {}
        for column in self.df_daily.columns:
            world_daily[column] = None

        for col_idx in range(0, len(self.df_daily.columns)):
            column = self.df_daily.columns[col_idx]
            if col_idx < 4:
                world_daily[column] = "World"
            else:
                for row_idx in range(0, len(self.df_daily)):
                    if row_idx == 0:
                        world_daily[column] = self.df_daily.iloc[row_idx,
                                                                 col_idx]
                    else:
                        world_daily[column] += self.df_daily.iloc[row_idx,
                                                                  col_idx]

        self.df_daily = self.df_daily.append(world_daily, ignore_index=True)

    def get_daily_deaths(self):
        for column in self.df_total.columns:
            self.daily_deaths[column] = []

        for row_idx in range(0, len(self.df_total)):
            for col_idx in range(0, len(self.df_total.columns)):
                column = self.df_total.columns[col_idx]
                if col_idx <= 4:
                    # concerns all columns that do not contain data of death
                    # cases as well as for the first day of documentation
                    self.daily_deaths[column].append(self.df_total.
                                                     iloc[row_idx, col_idx])
                else:
                    # calculates the difference between today and yesterday
                    self.daily_deaths[column].append(
                            self.df_total.iloc[row_idx, col_idx] -
                            self.df_total.iloc[row_idx, col_idx-1])

        # created dict can now be transformed into a DataFrame
        return pd.DataFrame(self.daily_deaths)

    def select_country(self, name="US", from_df="daily"):
        if from_df == "daily":
            s = self.df_daily[self.df_daily["Country/Region"] ==
                              name].iloc[:, 4:]
            self.world_data = self.df_daily[self.df_daily["Country/Region"]
                                            == "World"].iloc[:, 4:]
        elif from_df == "total":
            s = self.df_total[self.df_daily["Country/Region"] ==
                              name].iloc[:, 4:]
            self.world_data = self.df_total[self.df_total["Country/Region"]
                                            == "World"].iloc[:, 4:]
        else:
            raise ValueError("invalid from_df key")
        s = s.transpose()
        self.world_data = self.world_data.transpose()
        col_names = s.columns.tolist()
        if (len(col_names) > 1):
            print("changing just the first column's name to {}".format(name))
        s = s.rename(columns={col_names[0]: name})
        self.selected = s

    def plot_selected_country(self, name):
        if self.selected is None:
            raise ValueError("no country selected")

        fig, ax = plt.subplots()
        date_format = DateFormatter("%d %b %Y")
        death_cases = []
        death_cases_world = []
        dates = []
        for date_str in self.selected.index:
            date_obj = datetime.strptime(date_str, '%m/%d/%y')
            dates.append(date_obj)
        for sub_arr in self.selected.values:
            death_cases.append(sub_arr[0])
        for sub_arr in self.world_data.values:
            death_cases_world.append(sub_arr[0])

        world_plot = ax.bar(dates, death_cases_world,
                            bottom=0, color="lightgray")

        country_plot = ax.bar(dates, death_cases, bottom=0)

        ax.set(xlabel="Date", ylabel="Death Cases")
        ax.xaxis.set_major_formatter(date_format)
        fig.subplots_adjust(bottom=0.175)
        plt.xticks(rotation=35, fontsize=7)
        plt.legend((world_plot[0], country_plot[0]),
                   ("Worldwide", "{}".format(name)))
        plt.show()

    @staticmethod
    def update_local_data():
        base_url = "https://raw.githubusercontent.com/"
        url = (base_url +
               "CSSEGISandData/COVID-19/" +
               "master/csse_covid_19_data/" +
               "csse_covid_19_time_series/" +
               "time_series_covid19_deaths_global.csv")

        response = requests.get(url)

        if response.status_code == 200:
            content = response.content
            if len(content) < JHU_RESPONSE_MIN_LENGTH:
                print("got a very short response, aborting")
                exit(1)
            csv_file = open(JHU_UPDATED_DATA_FILENAME, "wb")
            csv_file.write(content)
            csv_file.close()
            print("successfully updated {}".
                  format(JHU_UPDATED_DATA_FILENAME))

    @staticmethod
    def usage():
        print(usage_msg)


if __name__ == "__main__":
    if len(argv) < 3:
        CovidData.usage()
        exit(1)

    for param in argv:
        if param == "--update":
            CovidData.update_local_data()
        if param == "--help":
            CovidData.usage()

    # TODO: validate, that country and df_type exist in df,
    #       otherwise use a sensible default
    country = argv[1].capitalize()
    df_type = argv[2].lower()

    covid_data = CovidData()
    covid_data.select_country(name=country, from_df=df_type)
    covid_data.plot_selected_country(name=country)
