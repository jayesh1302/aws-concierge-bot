import requests
import json
from os import getenv
from dotenv import load_dotenv

def get_business_attributes(business, location, cuisine_type):
    attributes_dictionary = {}
    attributes_dictionary['id'] = business['id']
    attributes_dictionary['location'] = location
    attributes_dictionary['name']=business['name']
    attributes_dictionary['cuisine_type'] = cuisine_type
    attributes_dictionary['url'] = business['url']
    optional_fields = ["rating", "contact","review_count","price"]
    for opt_f in optional_fields:
        if not business.get(opt_f, None):
            continue
        attributes_dictionary[opt_f] =  business.get(opt_f)
    if not business.get("coordinates", None):
        if not business['location'].get('latitude', None):
            attributes_dictionary["latitude"] = business["coordinates"]['latitude']
        if not business['location'].get('longitude', None):
            attributes_dictionary["longitude"] = business["coordinates"]['longitude']
    if not business.get('location', None):
        if not business['location'].get('display_address', None):
            attributes_dictionary['address'] = "".join(business['location']['display_address'])
        if not business['location'].get('zip_code', None):
            attributes_dictionary['zip_code'] = business['location']['zip_code']
    return attributes_dictionary


def scrape_yelp_data(api, api_key, cuisine_type, location, amount):
    query = "?location={}".format(
        location)+"&categories={}".format(cuisine_type)+"&limit={}".format(amount)
    yelp_api = api+query
    headers = {"Authorization": "Bearer " + api_key}
    # get all the responses
    response = requests.get(yelp_api, headers=headers).json()
    offset = 0
    total_responses = response['total']
    businesses = []
    # loop until the you reach end of all the responses
    while (total_responses >= 0):
        # but json has pages. So, loop through all the pages untill its none
        if response.get("businesses", None) is not None:
            response_businesses = response["businesses"]
            # loop through businesses in the current page
            responses_in_current_page = len(response_businesses)
            # for every business in the current page, get the attribute and put it in the business array
            for business in response_businesses:
                business_attributes = get_business_attributes(
                    business, location, cuisine_type)
                businesses.append(business_attributes)
            # Decreased total responses by total responses parsed.
            total_responses -= responses_in_current_page
            # And increase the offset by number of businesses parsed
            offset += responses_in_current_page
            # call the next page like this
            response = requests.get(
                yelp_api+query+str(offset), headers=headers).json()
        else:
            break
    return businesses

def write_data(data):
    with open('restaurants.json', 'w') as file:
        json.dump(data, file)

if __name__ == '__main__':
    load_dotenv()
    YELP_API_KEY = getenv('YELP_API_KEY')
    API = 'https://api.yelp.com/v3/businesses/search'
    
    CUISINES = [
        "chinese",
        # "indpak",
        # "italian",
        # "mexican"
    ]
    AMOUNT=50
    LOCATION="manhattan"
    restaurants = []
    for cuisine in CUISINES:
        restaurants += scrape_yelp_data(API, YELP_API_KEY, cuisine, LOCATION, AMOUNT)
    write_data(restaurants)