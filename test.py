import requests
import sys

EXPECTED_MIN_LENGTH = 100000
url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"

response = requests.get(url)

if response.status_code == 200:
    content = response.content
    if len(content) < EXPECTED_MIN_LENGTH:
        print("got a very short response, aborting")
        sys.exit(1)
    csv_file = open('test_file.csv', 'wb')
    csv_file.write(content)
    csv_file.close()
