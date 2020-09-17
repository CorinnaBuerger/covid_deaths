import csv
import datetime
import matplotlib.pyplot as plt
from bokeh.layouts import row
from bokeh.plotting import figure, output_file, show
from bokeh.models import CheckboxButtonGroup, Dropdown, CustomJS, Select
from bokeh.events import MenuItemClick

def get_daily_deaths(file, unimportant_columns):

    daily_deaths = []
    countries = []

    with open(file, 'rt') as f:
        data = csv.reader(f)
        for idx, row in enumerate(data):
            if idx == 0:
                continue
            else:
                if row[0] == "":
                    countries.append(row[1])
                else:
                    countries.append(row[0] + ", " + row[1])

    with open(file, 'rt') as f:
        data = csv.reader(f)
        for idx, row in enumerate(data):
            if idx == 0:
                for i in range(0, len(row)):
                    daily_deaths.append([row[i], 0])
            else:
                for i in range(0, len(row)):
                    if i < unimportant_columns:
                        continue
                    elif i == unimportant_columns:
                        daily_deaths[i][1] = int(row[i]) + int(daily_deaths[i][1])
                    else:
                        old_value = daily_deaths[i][1]
                        new_value = int(old_value) + int(row[i]) - int(row[i-1])
                        daily_deaths[i][1] = new_value
    print(countries, daily_deaths)
    for i in range(unimportant_columns):
        daily_deaths.pop(0)

    return daily_deaths, countries

def concatenate_lists(list1, list2):
    new_list = []
    for i in range(len(list1)):
        new_list.append([list1[i][0], (int(list1[i][1]) + int(list2[i][1]))])
    return new_list

def control_list(l):
    sums = 0
    for i in range(len(l)):
        sums += int(l[i][1])
        #print(l[i][0], ":", sums, "\n")
    print(sums)

def list_to_dic(ls):
    new_dic = {}
    for elem in ls:
        new_dic[elem[0]] = elem[1]
    return new_dic

def make_plot_plt(dic):
    plt.bar(range(len(dic)), list(dic.values()), align='center')
    plt.xticks(range(len(dic)), list(dic.keys()), rotation = 90)

    plt.show()

def get_date(string1):
    month, day, year = map(int, string1.split('/'))
    date = datetime.datetime(2020, month, day)
    return date

def make_plot_bokeh(dic):
    x = []
    y = []
    for key, value in dic.items():
        x.append(get_date(key))
        y.append(value)
    output_file('deaths.html')
    p = figure(title='Worldwide daily deaths caused by COVID-19', x_axis_label='date', y_axis_label="deaths", x_axis_type="datetime")
    p.vbar(x=x, top=y, width=1)
    show(p)

def get_country(country):
    y2 = []
    with open(file, 'rt') as f:
        data = csv.reader(f)
        for idx, row in enumerate(data):
            if row[1] == country: #here will be a problem for the comma seperated ones
                for i in range(4, len(row)):
                    if i == 4:
                        y2.append(int(row[i]))
                    else:
                        y2.append(int(row[i]) - int(row[i-1]))
    return y2

def make_stack_plot(world, country, filename, buttons, CLICKED=False):
    x = []
    y1 = []
    y2 = [0 for _ in range(199)]
    for key, value in world.items():
        x.append(get_date(key))
        y1.append(value)

    selecthandler = CustomJS(code="""
        var country = cb_object.value;
        var y2 = get_country(country);
        return y2;
    """)

    select = Select(title="Select a country", value="foo", options=countries)
    y2 = select.js_on_change('value', selecthandler)
    
    output_file(filename)
    p = figure(title='Worldwide daily deaths caused by COVID-19', x_axis_label='date', y_axis_label="deaths", x_axis_type="datetime")
    p.vbar(top=y1, x=x, color="blue", width=10)
    p.vbar(top=y2, x=x, color="red", width=10)

    layout = row(p, select)
    show(layout)
    
                
if __name__ == "__main__":

    world_deaths, countries = get_daily_deaths('covid-deaths.csv', 4)
    usa_deaths, countries_usa = get_daily_deaths('covid-deaths-usa.csv', 12)

    world_dic = list_to_dic(world_deaths)
    usa_dic = list_to_dic(usa_deaths)

    #control_list(usa_deaths)
    #control_list(world_deaths)

    #make_plot_bokeh(world_dic)
    filename = input("Please enter a name: ") + ".html"
    make_stack_plot(world_dic, usa_dic, filename, countries)

    

    

    

    
