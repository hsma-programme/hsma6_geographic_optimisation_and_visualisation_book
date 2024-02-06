
import re
import json
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup


def lookup_nearest_hospitals(postcode,
                             service_type):

    postcode_string_web_safe = postcode.replace(" ", "%20")

    if service_type == "ae":
        URL = "https://www.nhs.uk/service-search/find-an-accident-and-emergency-service/results/%s" %postcode_string_web_safe
    elif service_type == "utc":
        URL = "https://www.nhs.uk/service-search/find-an-urgent-treatment-centre/results/%s" %postcode_string_web_safe
    
    page = requests.get(URL, timeout=500)

    soup = BeautifulSoup(page.content, "html.parser")

    org_names = soup.find_all(id=re.compile("orgname"))
    org_names_list = [org_name.get_text() for org_name in org_names]

    addresses = soup.find_all(id=re.compile("address"))
    org_address_list = [address.get_text() for address in addresses]

    # This second needs more work as you can have multiple age ranges and separate opening times for each. 
    # They each have the same tag title and the current approach struggles as one the text is extracted it doesn't work

    # age_ranges = soup.find_all(id=re.compile("opening_hour_status_mesg_"))
    # org_age_range_list = [[re.findall((r"(\d+)"), age_range['id'])[0], 
    #                        age_range.get_text().replace("Open for ", "").replace("Closed for ", "").title()]
    #                       for age_range in age_ranges]
    
    # opening_times = soup.find_all(id=re.compile("opening_times_list"))
    # org_opening_times_list = [[re.findall((r"(\d+)"), opening_time['id'])[0], 
    #                            opening_time.get_text().replace("\n","")] 
    #                            for opening_time in opening_times]

    # opening_and_ages = []

    # for item in 1:len(org_age_range_list):
    #     opening_and_ages.append(
    #         []
    #     )

    phone_numbers = soup.find_all(id=re.compile("phone"))
    org_phone_numbers_list = [phone_number.get_text() for phone_number in phone_numbers]

    ae_hospital_df = pd.DataFrame(
        {
            "name": org_names_list,
            "address": org_address_list,
            #"age_range": org_age_range_list#,
            #"opening_times": org_opening_times_list#,
            "phone_number": org_phone_numbers_list
        }
    )

    ae_hospital_df['postcode'] = ae_hospital_df['address'].str.extract(
        r'(\w{1,4}\d{1,2}\w{0,1}\s*\d{1}\w{2})'
        )

    code_lookup = requests.post(
        "https://api.postcodes.io/postcodes",
        {"postcodes" : ae_hospital_df['postcode']},
        timeout=500
    )

    code_lookup_parsed = json.loads(code_lookup.content)

    # https://postcodes.io/
    postcode_lat_long_lookup = pd.DataFrame([{
                                                "postcode": code['result']['postcode'],
                                                "latitude": code['result']['latitude'],
                                                "longitude": code['result']['longitude']
                                                } 
                                            for code
                                            in code_lookup_parsed['result']])

    return ae_hospital_df.merge(postcode_lat_long_lookup, on="postcode")

def get_all_locations(postcode_list, service_type):

    dfs = []

    for postcode in postcode_list:
        dfs.append(
            lookup_nearest_hospitals(postcode, service_type)
            )
        print("Complete for postcode %s"%postcode)
        time.sleep(5)

    full_df = pd.concat(dfs)
    full_df['service_type'] = service_type

    return full_df.drop_duplicates()


postcode_sample = [
    "PL31 2QT", 
    "EX1 1SG",
    "IP24 2AZ",
    "WC1B 3DG",
    "NG1 6EL",
    "S60 1FD",
    "TS5 7YZ",
    "CA20 1EX",
    "OX7 5ED",
    "NE47 7AW"
]


ae_df = get_all_locations(postcode_sample, "ae")

ae_df.to_csv("uk_utc.csv")

utc_df = get_all_locations(postcode_sample, "utc")

utc_df.to_csv("uk_utc.csv")




utc_df = get_all_locations(postcode_sample, "utc")

