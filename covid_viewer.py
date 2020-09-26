from bokeh.layouts import row               # type: ignore
from bokeh.models import ColumnDataSource, CustomJS, Select   # type: ignore
from bokeh.plotting import figure           # type: ignore
from bokeh.io import output_file, show      # type: ignore
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

        # df that will be used is not specified yet
        self.current_df = None

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
            self.current_df = self.df_daily

        elif from_df == "total":
            self.current_df = self.df_total

        else:
            raise ValueError("invalid from_df key")

        s = self.current_df[self.current_df["Country/Region"] ==
                          name].iloc[:, 4:]
        self.world_data = self.current_df[self.current_df["Country/Region"]
                                        == "World"].iloc[:, 4:]

        s = s.transpose()
        self.world_data = self.world_data.transpose()

        col_names = s.columns.tolist()
        if (len(col_names) > 1):
            print("changing just the first column's name to {}".format(name))
        s = s.rename(columns={col_names[0]: name})
        self.selected = s

    def plot_selected_country(self, name, module="bokeh"):
        if self.selected is None:
            raise ValueError("no country selected")

        # create dictionary out of df that can be put into JS function
        df_dict_nested = self.current_df.groupby("Country/Region", 
                                          sort=False).apply(lambda x: x.to_dict(
                                                            orient="list")).to_dict()
        df_dict = {}
        keys_to_ignore = ["Province/State", "Country/Region", "Lat", "Long"]
        for key, value in df_dict_nested.items():
            helper_list = []
            for key_two, value_two in value.items():
                if key_two in keys_to_ignore:
                    continue
                else:
                    # sums up countries that occur multiple times
                    helper_list.append(sum(value_two))
            df_dict[key] = helper_list

        death_cases = []
        death_cases_world = []
        dates = []
        for date_str in self.selected.index:
            date_obj = datetime.strptime(date_str, '%m/%d/%y')
            dates.append(date_obj)
        df_dict["dates"] = dates
        for sub_arr in self.selected.values:
            death_cases.append(sub_arr[0])
        for sub_arr in self.world_data.values:
            death_cases_world.append(sub_arr[0])

        if module == "bokeh":

            # also necessary to make it compatible with JS function
            source = ColumnDataSource(data=df_dict)

            colors = ["lightgray", "blue"]
            p = figure(x_axis_type="datetime")
            print(df_dict)
            p.vbar(x='dates', color=colors[0], top="World", source=source,
                   width=0.9, legend_label="Worldwide")
            p.vbar(x='dates', color=colors[1], top=name, source=source,
                   width=0.9, legend_label=name)
            p.legend.location = "top_left"
            p.yaxis.axis_label = "Death Cases"
            p.xaxis.axis_label = "Date"

            output_file("test.html")

            # dropdown menu
            options = [*df_dict.keys()]
            select = Select(title="Select a country", value=name,
                            options=options)
            with open("main.js", "r") as f:
                # select.js_on_change("value", CustomJS(code="""
                #     console.log('select: value=' + this.value)
                #     """))
                # TODO: test and fix me
                select.js_on_change("value", CustomJS(args = dict(graph=source, df_dict=df_dict), code=f.read()))
            show(row(p, select))

        if module == "mpl":

            fig, ax = plt.subplots()
            date_format = DateFormatter("%d %b %Y")
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
    if argv[1].lower() == "us" or argv[1].lower() == "usa":
        country = "US"
    else:
        country = argv[1].capitalize()
    df_type = argv[2].lower()
    if argv[3] == "":
        module = "bokeh"
    else:
        module = argv[3].lower()

    covid_data = CovidData()
    covid_data.select_country(name=country, from_df=df_type)
    covid_data.plot_selected_country(name=country, module=module)
