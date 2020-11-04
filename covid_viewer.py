from bokeh.io import output_file, show, save                 # type: ignore
from bokeh.layouts import row, column                        # type: ignore
from bokeh.models import ColumnDataSource, CustomJS, Select  # type: ignore
from bokeh.models import HoverTool, NumeralTickFormatter     # type: ignore
from bokeh.plotting import figure                            # type: ignore
from bokeh.util.browser import view                          # type: ignore
from datetime import datetime                                # type: ignore
from matplotlib.dates import DateFormatter                   # type: ignore
from sys import argv, exit
import os
import matplotlib.pyplot as plt                              # type: ignore
import pandas as pd                                          # type: ignore
import requests

usage_msg = ("""Usage: covid_viewer <country> <bokeh/mpl> <input_csv> <output_file> [--update] [--help]
    --update\t\tupdate the local COVID data copy from JHU
    --help\t\tdisplay this help message

Copyright (c) 2020 by Corinna Buerger""")

JHU_RESPONSE_MIN_LENGTH = 100000


class CovidData():
    def __init__(self, infile):
        self.INFECTIONS = False
        self.DEATHS = False

        # will be filled 
        self.daily_cases = {}
        self.df_dict_daily = {}
        self.df_dict_total = {}

        # pd.DataFrame for total cases
        self.df_total = pd.read_csv(infile)
        self.df_daily = self.get_daily_cases()

        # adds worldwide cases to both DataFrames
        self.get_world_cases()

        # not created yet
        self.dates = None
        self.dates_str = None

        # no country selected yet
        self.selected = None

        if "deaths" in infile:
            self.DEATHS = True
        else:
            self.INFECTIONS = True


    def get_daily_cases(self):
        for column_in_df in self.df_total.columns:
            self.daily_cases[column_in_df] = []

        for row_idx in range(0, len(self.df_total)):
            for col_idx in range(0, len(self.df_total.columns)):
                column = self.df_total.columns[col_idx]
                if col_idx <= 4:
                    # concerns all columns that do not contain data of 
                    # cases as well as for the first day of documentation
                    self.daily_cases[column].append(self.df_total.
                                                     iloc[row_idx, col_idx])
                else:
                    # calculates the difference between today and yesterday
                    self.daily_cases[column].append(
                            self.df_total.iloc[row_idx, col_idx] -
                            self.df_total.iloc[row_idx, col_idx-1])

        # created dict can now be transformed into a DataFrame
        return pd.DataFrame(self.daily_cases)

    def get_world_cases(self):
        # append to DataFrame for total cases
        world_total = {}
        for column_in_df in self.df_total.columns:
            world_total[column_in_df] = None

        for col_idx in range(0, len(self.df_total.columns)):
            column = self.df_total.columns[col_idx]
            if col_idx < 4:
                # here is no data for cases
                world_total[column] = "World"
            else:
                for row_idx in range(0, len(self.df_total)):
                    if row_idx == 0:
                        # for the first row (country) in each column (day)
                        # the cases will be assigned
                        world_total[column] = self.df_total.iloc[row_idx,
                                                                 col_idx]
                    else:
                        # for all the other rows (countries) in each column
                        # (day) the cases will be added to the previous
                        # one
                        world_total[column] += self.df_total.iloc[row_idx,
                                                                  col_idx]

        self.df_total = self.df_total.append(world_total, ignore_index=True)

        # append to DataFrame for daily cases (works just like for total
        # cases but uses self.df_daily)
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

    def select_country(self, name="US"):
        s_daily = self.df_daily[self.df_daily["Country/Region"]
                                == name].iloc[:, 4:]
        s_total = self.df_total[self.df_total["Country/Region"]
                                == name].iloc[:, 4:]
        self.world_data_daily = self.df_daily[self.df_daily["Country/Region"]
                                              == "World"].iloc[:, 4:]
        self.world_data_total = self.df_total[self.df_total["Country/Region"]
                                              == "World"].iloc[:, 4:]

        s_daily = s_daily.transpose()
        s_total = s_total.transpose()
        self.world_data_daily = self.world_data_daily.transpose()
        self.world_data_total = self.world_data_total.transpose()

        # only doing this for daily data can maybe lead to bugs
        col_names = s_daily.columns.tolist()
        if (len(col_names) > 1):
            print("changing just the first column's name to {}".format(name))
        s_daily = s_daily.rename(columns={col_names[0]: name})
        self.selected = s_daily

    def create_plot(self, name, dic, title, css_class):
        dic["selected"] = dic[name]

        if self.DEATHS:
            YAXIS = "Deaths"
            COLOR = "blue"
        else:
            YAXIS = "Infections"
            COLOR = "red"
        SOURCE = ColumnDataSource(data=dic)
        TITLE = title + " " + YAXIS
        CSS_CLASS = [css_class]
        XAXIS_LABEL = "Date"
        YAXIS_LABEL = YAXIS
        HEIGHT = 600
        WIDTH= 760
        SIZE = 1
        CIRCLE_SIZE = 12
        TOOLTIPS = [("Date", "@dates_str"), 
                    (f"{YAXIS} of selected country", "@selected"), 
                    (f"{YAXIS} worldwide", "@World")]
        TOOLS = [HoverTool(tooltips=TOOLTIPS), "pan", 
                 "wheel_zoom", "box_zoom", "reset"]


        # create plot
        p = figure(x_axis_type="datetime", title=TITLE, 
                   plot_height=HEIGHT, tools=TOOLS, width=WIDTH,
                   css_classes=CSS_CLASS)

        p.vbar(x='dates', top="selected", color=COLOR, line_width=SIZE, source=SOURCE)
        p.circle(x='dates', y="selected", color=COLOR, size=CIRCLE_SIZE, source=SOURCE, 
                 fill_alpha=0, line_alpha=0)
        p.yaxis.axis_label = YAXIS_LABEL
        p.xaxis.axis_label = XAXIS_LABEL
        p.yaxis.formatter=NumeralTickFormatter(format="0a")

        return p, SOURCE

    def create_dropdown(self, name, source_daily, source_total):

        # get options for dropdown

        # dates can't be sorted like this, so it has to be removed for this step
        self.df_dict_total.pop("dates")
        self.df_dict_total.pop("dates_str")
        sort_options = sorted(self.df_dict_total.items(), key=lambda x: x[1][-1],
                              reverse=True)
        options = []
        for tpl in sort_options:
            total_cases_list = list(str(tpl[1][-1]))
            total_cases_str_sep = ""
            for i, num in enumerate(total_cases_list):
                total_cases_str_sep += num
                if i == len(total_cases_list)-1:
                    continue
                elif len(total_cases_list) % 3 == 0:
                    if i % 3 == 2:
                        total_cases_str_sep += ","
                elif len(total_cases_list) % 3 == 1:
                    if i % 3 == 0:
                        total_cases_str_sep += ","
                elif len(total_cases_list) % 3 == 2:
                    if i % 3 == 1:
                        total_cases_str_sep += ","
            if tpl[0] == name:
                selected_total_cases_sep = total_cases_str_sep
            options.append(f"{tpl[0]}: {total_cases_str_sep} total cases")

        options.remove(f"selected: {selected_total_cases_sep} total cases")

        # dates need to be added again since they were removed for sorting the options
        self.df_dict_total["dates"] = self.dates
        self.df_dict_total["dates_str"] = self.dates_str

        # create dropdown

        select = Select(title="Select a country", 
                        value=f"{name}: {selected_total_cases_sep} total cases",
                        options=options, sizing_mode="scale_width")

        with open("main.js", "r") as f:
            JS_function = CustomJS(args=dict(source_d=source_daily, source_t=source_total, 
                                             df_dict_t=self.df_dict_total, 
                                             df_dict_d=self.df_dict_daily), code=f.read())
            select.js_on_change("value", JS_function)

        return select


    def plot_with_bokeh(self, name, output):
        pd, source_d = self.create_plot(name, self.df_dict_daily, 
                                        "Daily", "we-need-this-for-manip")
        pt, source_t = self.create_plot(name, self.df_dict_total, 
                                        "Total", "we-need-this-for-manip-total")

        select = self.create_dropdown(name, source_d, source_t)

        with open("template.html", "r") as f:
            template = f.read()

        output_file(output)
        plots = column(pd, pt)
        save(column(select, plots), template=template)
        view(output)

    def plot_with_mpl(self, name):
        if self.DEATHS:
            ylabel = "Death Cases"
        else:
            ylabel = "Infections"
        cases = []
        cases_world = []
        # cave: only for daily
        for sub_arr in self.selected.values:
            cases.append(sub_arr[0])
        for sub_arr in self.world_data_daily.values:
            cases_world.append(sub_arr[0])

        fig, ax = plt.subplots()
        date_format = DateFormatter("%d %b %Y")
        world_plot = ax.bar(self.dates, cases_world,
                            bottom=0, color="lightgray")
        country_plot = ax.bar(self.dates, cases, bottom=0)
        ax.set(xlabel="Date", ylabel=ylabel)
        ax.xaxis.set_major_formatter(date_format)
        fig.subplots_adjust(bottom=0.175)
        plt.xticks(rotation=35, fontsize=7)
        plt.legend((world_plot[0], country_plot[0]),
                   ("Worldwide", "{}".format(name)))
        plt.show()

    def fill_dict_for_source(self, df, dic, name):
        if self.selected is None:
            raise ValueError("no country selected")

        # create dictionary out of df that can be put into JS function
        grouped_df = df.groupby("Country/Region", sort=False)
        grouped_list = grouped_df.apply(lambda x: x.to_dict(orient="list"))
        df_dict_nested = grouped_list.to_dict()
        keys_to_ignore = ["Province/State", "Country/Region", "Lat", "Long"]
        for key, value in df_dict_nested.items():
            helper_list = []
            for key_two, value_two in value.items():
                if key_two in keys_to_ignore:
                    continue
                else:
                    # sums up countries that occur multiple times
                    helper_list.append(sum(value_two))
            dic[key] = helper_list

        # needs to be cleared since it would be doubled otherwise 
        self.dates = []
        self.dates_str = []
        for date_str in self.selected.index:
            date_obj = datetime.strptime(date_str, '%m/%d/%y')
            self.dates.append(date_obj)
            date_str_new = datetime.strptime(date_str, '%m/%d/%y').strftime('%d %b %Y')
            self.dates_str.append(date_str_new)
        dic["dates"] = self.dates
        dic["dates_str"] = self.dates_str

    def plot_selected_country(self, name, output, module):
        self.fill_dict_for_source(self.df_daily, self.df_dict_daily, name) 
        self.fill_dict_for_source(self.df_total, self.df_dict_total, name) 

        if module == "bokeh":
            self.plot_with_bokeh(name, output)

        if module == "mpl":
            self.plot_with_mpl(name)

    @staticmethod
    def update_local_data(source, input_csv):
        base_url = "https://raw.githubusercontent.com/"
        url = (base_url +
               "CSSEGISandData/COVID-19/" +
               "master/csse_covid_19_data/" +
               "csse_covid_19_time_series/" +
               f"time_series_covid19_{source}_global.csv")

        response = requests.get(url)

        if response.status_code == 200:
            content = response.content
            if len(content) < JHU_RESPONSE_MIN_LENGTH:
                print("got a very short response, aborting")
                exit(1)
            csv_file = open(input_csv, "wb")
            csv_file.write(content)
            csv_file.close()
            print("successfully updated {}".format(input_csv))

    @staticmethod
    def usage():
        print(usage_msg)


if __name__ == "__main__":
    print("current working directory: {}".format(os.getcwd()))
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    if len(argv) < 5:
        CovidData.usage()
        exit(1)

    if argv[1].lower() == "us" or argv[1].lower() == "usa":
        country = "US"
    else:
        country = argv[1].capitalize()

    module = argv[2].lower()
    input_csv = argv[3]
    output = argv[4]

    for param in argv:
        if param == "--update":
            if "deaths" in input_csv:
                source = "deaths"
            else:
                source = "confirmed"
            CovidData.update_local_data(source, input_csv)
        if param == "--help":
            CovidData.usage()

    covid_data = CovidData(input_csv)
    covid_data.select_country(name=country)
    covid_data.plot_selected_country(name=country, output=output, module=module)
