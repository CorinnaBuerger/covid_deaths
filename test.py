from sys import argv, exit
import matplotlib.pyplot as plt
import pandas as pd

class CovidData():
    def __init__(self, infile="covid-deaths.csv"):
        self.df_total = pd.read_csv(infile)                                     # DataFrame for total death cases
        self.dates = pd.date_range('01/22/2020', '08/07/2020', freq='D').date
        self.selected = None                                                    # no country selected yet
        self.daily_deaths = {}                                                  # will be filled and transformed into self.df_daily
        self.df_daily = self.get_daily_deaths()                                 # DataFrame for the daily death cases

    def get_daily_deaths(self): 
        for column in self.df_total.columns:
            self.daily_deaths[column] = [] 

        for row_idx in range(0, len(self.df_total)):
            for col_idx in range(0, len(self.df_total.columns)):
                column = self.df_total.columns[col_idx]
                if col_idx <= 4: 
                    # concerns all columns that do not contain data of death cases as well as for the first day of documentation
                    self.daily_deaths[column].append(self.df_total.iloc[row_idx, col_idx])
                else: 
                    # calculates the difference between today and yesterday
                    self.daily_deaths[column].append(self.df_total.iloc[row_idx, col_idx] - self.df_total.iloc[row_idx, col_idx-1])

        # created dict can now be transformed into a DataFrame
        return pd.DataFrame(self.daily_deaths)

        
    def select_country(self, name="US", from_df="daily"):
        if from_df == "daily":
            s = self.df_daily[self.df_daily["Country/Region"] == name].iloc[:, 4:]
        elif from_df == "total":
            s = self.df_total[self.df_daily["Country/Region"] == name].iloc[:, 4:]
        else:
            raise ValueError("invalid from_df key")
        s = s.transpose()
        col_names = s.columns.tolist()
        if (len(col_names) > 1):
            print("changing just the first column's name to {}".format(name))
        s = s.rename(columns={col_names[0]: name})
        self.selected = s
        

    def plot_selected_country(self):
        if self.selected is None:
            raise ValueException("no country selected")
        self.selected.plot(kind="bar").set_xticklabels(self.dates)
        plt.show()

def usage():
    print(
"""Usage: covid_viewer: <country> <total/daily>

Copyright (c) 2020 by Corinna Buerger"""
   )

if __name__ == "__main__":
    if len(argv) < 3:
        usage()
        exit(1)

    # TODO: validate, that country and df_type exist in df, 
    #       otherwise use a sensible default
    country = argv[1]
    df_type = argv[2]

    covid_data = CovidData()
    covid_data.select_country(name=country from_df=df_type)
    covid_data.plot_selected_country()
