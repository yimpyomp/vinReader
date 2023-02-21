# Import statements
import csv
import pandas as pd
import itertools
import requests

nhtsa_api = 'https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/'
key_list = ['VIN Check', 'Make', 'Model', 'Year', 'Displacement (CC)', 'Displacement (CI)']
nhtsa_indexes = [4, 7, 9, 10, 71, 72]
year_file = 'vin_11_char.csv'
pd.set_option('display.max_columns', 500)
# Creating dataframes, dictionaries for vehicle specs
chevroletDF = pd.read_csv('chevrolet_specs.csv', header=0)
fordDF = pd.read_csv('ford_specs.csv', header=0)
gmDF = pd.read_csv('gm_specs.csv', header=0)
nissanDF = pd.read_csv('nissan_specs.csv', header=0)

chevroletDict = chevroletDF.to_dict()
fordDict = fordDF.to_dict()
gmDict = gmDF.to_dict()
nissanDict = nissanDF.to_dict()

specDicts = {'CHEVROLET': chevroletDict, 'FORD': fordDict, 'GM': gmDict, 'NISSAN': nissanDict}


def get_vin_data(vin):
    """
    Uses NHTSA API to decode VIN
    :param vin: String containing full 17 character VIN
    :return: Dictionary containing VIN Validation check, Make, Model, Year, and engine displacement in CC and CI
    """
    # Calling api, retrieving information
    url = nhtsa_api + str(vin) + '?format=json'
    vic_data = requests.get(url)
    # Converting requests object to json
    vic_dict = vic_data.json()
    subdictionary = vic_dict['Results']
    # Creating, populating dictionary with information
    spec_dictionary = {}
    i = 0
    for element, index in zip(key_list, nhtsa_indexes):
        spec_dictionary[element] = subdictionary[index]['Value']
        i += 1

    # Returning dictionary
    return spec_dictionary


def manufacture_date():
    """
    Accesses CSV containing model year information from VIN position 11 character
    :return: Dictionary containing corresponding VIN element and model year information
    """
    # Opening CSV containing data, encoding option prevents weird text output for first row
    with open(year_file, newline='', encoding='utf-8-sig') as f:
        # Reading file, converting to dictionary object
        reader = csv.reader(f)
        manufacture_dict = dict(reader)
    # Returning dictionary object
    return manufacture_dict


# The real question here is how to implement this dataframe
def get_capacity(filename):
    """
    Retrieves oil capacity and filter spec from csv
    :param filename: Name of file containing specifications
    :return: Dataframe with specifications
    """
    capacity_spec_df = pd.read_csv(filename, header=None)
    capacity_spec_df.columns = ['Make', 'Model', 'Displacement', 'Capacity', 'Filter']
    return capacity_spec_df


# Can you guess where the fleet data method came from? Certainly not this thing
def get_batch(vin_list):
    # String containing url for batch decode aspect of API
    batch_url = 'https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/'
    # Empty string to store formatted data
    data_string = ''
    # Adding all elements of list to string with semicolon separator
    for item in vin_list:
        data_string += (item + ';')
    # Fields for API, removing last semicolon from data string
    post_fields = {'format': 'json', 'data': data_string[:-1]}
    # Retrieving data from API, converting to dictionary
    fleet_data = requests.post(batch_url, data=post_fields)
    fleet_dict = fleet_data.json()
    # Accessing results key of dictionary, contains list of dictionaries containing data
    fleet_results = fleet_dict['Results']
    # List of relevant dictionaries
    fleet_list = []
    # Iterating through raw (ish) data
    for item in fleet_results:
        vehicle_string = item['ModelYear'] + ' ' + item['Make'] + ' ' + item['Model'] + ' ' \
                         + item['DisplacementL'] + ' L'
        fleet_list.append(vehicle_string)

    return fleet_list


def save_sheet(data, name):
    filename = name + '.xlsx'
    data.to_excel(filename)
    return None


class Vehicle:
    def __init__(self, vin):
        self.vin = str(vin)
        #self.full_vin = full_vin
        self.model_year_dict = manufacture_date()
        if len(self.vin) == 17:
            self.full_vin = True
        elif len(self.vin) == 8:
            self.full_vin = False
        else:
            raise Exception('Invalid input. Enter partial (last 8 characters) or full (17 characters) VIN')

    def decode_vin(self):
        """
        Decoding VIN input
        :return: Prints information to console, does not return any data
        """
        if self.full_vin:
            vehicle_data = get_vin_data(self.vin)
            print('\n')
            print(f'VIN Input: {self.vin}')
            for key in vehicle_data.keys():
                print(f'{key}: {vehicle_data[key]}')
            #print('\n')

        else:
            year_code = self.vin[0]
            vehicle_data = self.model_year_dict[str(year_code)]
            print('\n')
            print(f'VIN Input: {self.vin}')
            print(f'Model Year: {vehicle_data}')

        return None


class Fleet:
    def __init__(self, vin_list):
        self.vin_list = vin_list
        self.model_year_dict = manufacture_date()
        if type(vin_list) != list:
            raise Exception('Invalid input. Enter list containing VINs.')

    # This method will be deprecated shortly
    def parse_input(self):
        vehicle_data = []
        sticker_miles = []
        sheetDF = pd.DataFrame(columns=['VIN Last 8', 'Mileage', 'Sticker Mileage'])
        if self.mileage:
            for item in self.mileage:
                sticker_miles.append(int(item) + 5000)

        '''for item in self.vin_list:
            if len(item) == 17:
                vehicle_data.append(get_vin_data(item))
            else:
                year_code = item[0]
                vehicle_data.append(self.model_year_dict[year_code])

        fleet_dictionary = dict(zip(self.vin_list, vehicle_data))
        for key in fleet_dictionary.keys():
            print(f'{key}: {fleet_dictionary[key]}')'''
        for item in self.vin_list:
            year_code = item[0]
            vehicle_data.append(self.model_year_dict[year_code])

        sheetDF['Model Year'] = vehicle_data
        sheetDF['VIN Last 8'] = self.vin_list
        sheetDF['Mileage'] = self.mileage
        sheetDF['Sticker Mileage'] = sticker_miles

        return sheetDF

    def fleet_data(self, mileage=None, get_specs=False):
        if mileage:
            sticker_miles = []
            if type(mileage) != list:
                raise Exception('Mileage parameter must be list of vehicle mileages')
            for item in mileage:
                sticker_miles.append(int(item) + 5000)
            sheetDF = pd.DataFrame(columns=['Vehicle', 'Fuel Type', 'Miles', 'Sticker Miles'])
        else:
            sheetDF = pd.DataFrame(columns=['Vehicle', 'Fuel Type'])

        # Let's just catch errors before they happen
        for item in self.vin_list:
            if len(item) != 17:
                indexFuckyWucky = self.vin_list.index(item)
                print(f' Item {indexFuckyWucky + 1} is incomplete.')
                raise Exception('List must contain full VIN numbers (17 characters).')
        # String containing url for batch decode aspect of API
        batch_url = 'https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/'
        # Empty string to store formatted data
        data_string = ''
        # Adding all elements of list to string with semicolon separator
        for item in self.vin_list:
            data_string += (item + ';')
        # Fields for API, removing last semicolon from data string
        post_fields = {'format': 'json', 'data': data_string[:-1]}
        # Retrieving data from API, converting to dictionary
        fleet_data = requests.post(batch_url, data=post_fields)
        fleet_dict = fleet_data.json()
        # Accessing results key of dictionary, contains list of dictionaries containing data
        fleet_results = fleet_dict['Results']
        # List of relevant dictionaries
        fleet_list = []
        fleet_fuel_types = []
        # Adding make and displacement lists to store values separately to search and return capacity and filter spec
        fleet_makes = []
        fleet_displacements = []

        # Iterating through raw (ish) data
        for item in fleet_results:
            vehicle_string = item['ModelYear'] + ' ' + item['Make'] + ' ' + item['Model'] + ' ' \
                             + item['DisplacementL'] + 'L'
            fleet_list.append(vehicle_string)
            fleet_fuel_types.append(item['FuelTypePrimary'])
            fleet_makes.append(item['Make'])
            fleet_displacements.append(item['DisplacementL'] + 'L')

        #return fleet_list
        # Fuck around with a panda why not
        sheetDF['Vehicle'] = fleet_list
        sheetDF['Fuel Type'] = fleet_fuel_types
        if mileage:
            sheetDF['Miles'] = mileage
            sheetDF['Sticker Miles'] = sticker_miles
            # Checks if vehicle is diesel powered, if yes, sticker mileage is adjusted for a 10k mile interval
            for i in range(len(sheetDF.index)):
                if sheetDF.iloc[i, 1] == 'Diesel':
                    sheetDF.iloc[i, 3] += 5000

        if get_specs:
            # Adding make, displacement columns
            sheetDF['Make'] = fleet_makes
            sheetDF['Displacement'] = fleet_displacements

            # Getting oil capacities, filters and adding to DF
            fleetCapacities = []
            fleetFilters = []

            for i in range(len(sheetDF)):
                make, displacement = sheetDF.iloc[i, 4], sheetDF.iloc[i, 5]
                # Open dictionary according to make
                target_dict = specDicts[make][displacement]
                # Get values from dictionary according to displacement, add to lists
                fleetCapacities.append(target_dict[0])
                fleetFilters.append(target_dict[1])

            # Add lists to dataframe
            sheetDF['Oil Capacity'] = fleetCapacities
            sheetDF['Oil Filter'] = fleetFilters

            # Drop make, displacement columns
            sheetDF.drop(['Make', 'Displacement'], axis=1, inplace=True)

        return sheetDF


# Formatting my ass
'''testVIN = Vehicle('3C6TRVDG3GE119130')
testPartial = Vehicle('GE119130')

testVIN.decode_vin()
testPartial.decode_vin()

fleetTest = ['NS20832', 'NY222609', 'PF117118', 'PE511675']
Fleet(fleetTest).parse_input()

fullTest = ['3C6TRVDG3GE119130', 'NY222609', '1N6AD0ER4FN744144']
Fleet(fullTest).parse_input()
fullTest = ['3C6TRVDG3GE119130', '1N6AD0ER4FN744144']
text = get_batch(fullTest)
'''

'''fullVins = ['3AKJHHDR4MSMA8079', '3C6TRVDG3GE119130', '1N6AD0ER4FN744144', '3HSDJAPR8FN576855']
miles = [40298, 362351, 141253, 756866]

partialReal = ['PF117118', 'NS208321', 'NY222909', 'PE511675', 'NN302963', 'NT214089',
               'NT214076', 'PF125630', 'NH193238', 'NS208063', 'NT214051', 'PF126107', 'GE119130']
milesReal = [14808, 26953, 7221, 16018, 35975, 12839, 14848, 7258, 14843, 15543, 10314, 7784, 6500]

#partialTest = Fleet(partialReal, mileage=milesReal).parse_input()
#print(partialTest)
df = Fleet(fullVins).fleet_data()

print(df['Vehicle'])
'''

# Now for a for-realsies test with real data
feb20_firesafe_vin = ['1N6ED0CE5MN706792', '1FTBR1C8XLKA23395', '1FTEX1C88GKD29200', '1FTYE1YM5KKA17983',
                      '1FTYE1YMXGKA17310', '1GCEC19038Z293325']
feb_20_miles = [38346, 83014, 136610, 70328, 171180, 195689]

firesafeSheet = Fleet(feb20_firesafe_vin)

testtype = firesafeSheet.fleet_data(mileage=feb_20_miles, get_specs=True)
save_sheet(testtype, 'fsTest')

'''# Make, Displacement columns 4, 5
capacities = []
filters = []

for i in range(len(fireSafeSheet)):
    # Assign make and displacement to variables
    make, displacement = fireSafeSheet.iloc[i, 4], fireSafeSheet.iloc[i, 5]
    # Open dictionary according to make
    target_dict = specDicts[make][displacement]
    # Get values from dictionary according to displacement
    capacities.append(target_dict[0])
    filters.append(target_dict[1])

fireSafeSheet['Capacities'] = capacities
fireSafeSheet['Filters'] = filters

print(fireSafeSheet)'''