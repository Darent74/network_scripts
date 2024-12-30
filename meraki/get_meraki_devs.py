import meraki
import csv
import os
import argparse
from icecream import ic
from rich import print
# import pprint
from tabulate import tabulate
#################################################################################################
##### Variables / Lists / Contstants
CLIENT_KEYS = ['site','mac','description','ip', 'recentDeviceName','switchport','status','manufacturer','id','notes','usage']
DEVICE_KEYS = ['site','name', 'serial', 'mac', 'lanIp', 'model','firmware','notes']

###### Enviroment Variables ###################################################################
# Load Meraki API key from environment variable
API_KEY = os.getenv("MERAKI_API_KEY")
organization_id = os.environ.get("ORD_ID")

########## Setup the Dashboard api call  ######################################################
dashboard = meraki.DashboardAPI(API_KEY,suppress_logging=True)   ##<<<<<<< Import call, this sets up the dashboard value

###############################################################################################
# Functions    ################################################################################
###############################################################################################

################################################################################################
# Function : list_networks
#
#  Input  : organisation_id 
#  Output : enumerated list of networks availble to the Organisation 
#  API call getNetworkClients gathers all clients connected to the network based on the netword ID
#  passed into the routine.  Total_Pages='all' is set to gather all devices.   
# 
################################################################################################   
def list_networks(organization_id):
    nets = dashboard.organizations.getOrganizationNetworks(organization_id) # API Call to get the networks held in the organisation_id ( passed in from enviroment)
    result_dict = {index: item for index, item in enumerate(nets, start=1)}
    # ic(result_dict)
    for key,value in result_dict.items():
        print(f"{key:5} : {value['name']:15}  id: { value['id']:30}")
    # print(f"The dictionary length is : {len(result_dict)}") 
    # ic(result_dict)
    return result_dict
 
################################################################################################
# Function to get clients
#  get_all_clients  routine, to gather all 
#  API call  getNetworkClients gathers all clients connected to the network based on the netword ID
#  passed into the routine.  Total_Pages='all' is set to gather all devices. 
#  
# 
################################################################################################
def get_all_clients(netid):
    try:
        devresponse = dashboard.networks.getNetworkClients(netid, total_pages='all')
        print("get_all_clients is being returned")
        # print(type(devresponse))
        
        return devresponse   # Devices returned in a 
    except meraki.APIError as e:
        print(f"Error fetching details for device clients for netid {netid}: {e}")
        return None        

################################################################################################
# Function to get device details
#  get_all_details  routine, gathers all devices 
#  Meraki call to get devices based on serial
#  Inputs : device Serial 
#  Returns : device  object , has details for the device in a dictionary
# 
################################################################################################
# Function to get details of a single device by serial
def get_device_details(serial):
    try:
        device = dashboard.devices.getDevice(serial)
        return device
    except meraki.APIError as e:
        print(f"Error fetching details for device {serial}: {e}")
        return None

################################################################################################
# Function  get_all_devices_in_network
#   Function is passed the network_id which is used to gather all devices listed
#   for that network based on  .getNetworkDevices  API
#  
################################################################################################
def get_all_devices_in_network(network_id):
    try:
        # devices = dashboard.networks.getNetworkDevices(network_id, total_pages='all')
        devices = dashboard.networks.getNetworkDevices(network_id)
        # print(f"Length of Devices is : {len(devices)}")
        return devices
    except meraki.APIError as e:
        print(f"Error fetching devices for network {network_id}: {e}")
        return None

################################################################################################
# Function : write_data_csv
#  Writes the devices to csv file, and uses the keylist as the header list.
#  Inputs : devices, output_file, keylist , net_site
#  Returns : device  object , has details for the device in a dictionary
# 
#  
############################################################################
def write_data_csv(devices,output_file=None,keylist=None,net_site=None):
    # print(f"The keys passed in are {keylist}")
    # print(f" devices passed in :")
    # ic(devices)
    # keys_to_print = ['mac','description', 'ip', 'status','manufacturer','id','notes']
    if keylist != None:
        header_keys = keylist
        if output_file != None :    
            # print(f"The net_site is : {net_site}  ")
            # print(header_keys)
            with open(output_file, mode='w', newline='') as file:
                # writer = csv.DictWriter(file, fieldnames=keylist)
                writer = csv.DictWriter(file, fieldnames=header_keys)
                writer.writeheader()
                for device in devices:
                    # print(f"The site listed in device : {device['site'] } ")
                    row1 = {key: device.get(key,'') for key in keylist}
                    if device.get('site', '') == None: 
                        merged_dict = {**row1, **{k: v for k, v in net_site.items() if v is not None}}
                        print(merged_dict)
                        writer.writerow(merged_dict)
                    else:
                        
                        writer.writerow(row1)
        
            ic("#############################################################")
            print(f"Device details written to :{output_file}")
            ic("#############################################################")
################################################################################################
# Function : check_network_selection
# Checks arguments added at command line.
#  if the network argument is valid , ie ( within the range of the valid sections) the routine will return 
#  the valid selection
#  network_arg : if the argument is not in the slection provided, the program will display a message
#  and then exit
# 
################################################################################################

def check_network_selection(network_arg,num_networks):
    # print(f"The network arg is : {network_arg}")
    if not network_arg:
        print("A Network select must be entered from command line")
        try:
            network_arg = int(input("Select the network by number: ")) 
        except ValueError as e:
            print(f"invalid input entered , program now terminating")
            exit() 
    
    # print(f"We have an network argument : {network_arg} and a num_networks {num_networks}")
    if int(network_arg)  in range(0,(num_networks + 1 )):
        value = int(network_arg)
        # print(f"The value being returned is : {value}")
        return value
    else:
        print(f"Index {network_arg} is not within valid range, try again")
        exit()  # Termionate program, - no point if the index is out of range


################################################################################################
# Function : get_site_details
# passes in device and a reference_dictionary that has all the network ID's that have been gathered
# The loop searchs the reference_dict  for the device id and if it matchs , it returns the NAME of the 
# network site back 
# 
#  
################################################################################################

def get_site_details(device_id,ref_dict):
    # print(f"The Device id is : {device_id}")
    # print(len(ref_dict))
    # print(f"The device_id being searched is  {device_id}")
    if device_id:
       for key,value in ref_dict.items():
        #    print(f"key is listed as {key} {type(key)}   j is  {value}")
           if value['id'] == device_id:  # then we have found a match and the site is now known
            #    print(f"The device ie : {device_id} belongs to site : {value['name']}  key is {key}")
               return  value['name']
    return "ID not Found" 
   

############################################################################
# Parser Routine - parse_networks_arguments
# Parser will look at the arguments and parse them with the responses required.
# network will list networks
# When no option is provided for input, the networks available will be displayed.
# -- network : specify the network number you want to look at
# --serials  : takes in a single or multiple serials as specified from the command line. 
# --csv      : for writing the displayed output to a CSV file with a header
# --clients  : for all clients known for the listed --network chosen
#
############################################################################
def parse_network_arguments():  
    parser = argparse.ArgumentParser(description="Extract Meraki device details.")
    parser.add_argument('--network', help="Select the network (by number from the list).", type=int, required=False)
    parser.add_argument('--serials', help="Comma-separated list of device serials to extract.", type=str, required=False)
    parser.add_argument('--all', help="Extract all devices in the selected network.", action='store_true')
    parser.add_argument('--csv', help="Path to output the results to a CSV file.", type=str, required=False)
    parser.add_argument('--clients', help="Extract Clients.", action='store_true')
    return parser.parse_args()

################################################################################################
# Function : add_siteinfo
#  inputs : devices dictionary, the device in question, the network dictionary and an OPTIONAL dnetid
#  if dnetid is None, ( as in if its never passed to the progam , it will be classified as None)
#  The routine gathers dev_net_id  from the devices using a get on the field : networkId
#  Using the dev_net_id,  routine dev_site_details is called and returns the site the device belongs too
# The Device  SITE is then Appended into to the Devices structure.  
#  The SITE field is not nativly in the Devices Dictionary. 
# This becomes useful later in the code when we can marry up a device to a site.
################################################################################################

def add_siteinfo(devices,device,network_dict,dnetid=None):
    if dnetid == None:
        dev_net_id = device.get('networkId','None') # This can get the NEtwork ID from the device, the network_id is the site designator
    else:
        dev_net_id = dnetid
    
    dev_belongs_to_site = get_site_details(dev_net_id,network_dict)
    network_sitename = dev_belongs_to_site
    if dev_net_id == 'None':
        print("Device Serial not found : ")
    else:
        network_sitename = dev_belongs_to_site

    if device:
        device['site'] = network_sitename
        devices.append(device)

    return(devices)

######################################################################################
# Function : output_table_from_dict.
# the input is a set of dictionarys ( data ) which have keys that match the header field
# the headers are the fields you wish to extract.
# the 1 liner  reads the data of in rows. 
def output_table_from_dict(data, headers):
    # Extract only the data from the dictionary you required that matchs the headers.
    selected_data = [[row.get(header,"") for header in headers] for row in data]  # 1 liners , reads the headers 
                                                                                  # the selected data is just the 
                                                                                  # header fields and respective data
    table = tabulate(selected_data, headers, tablefmt="pretty")                   # Formate the data in a table   
    print(table)                                                                  # print the table out 

############################################################################
# Main function to handle command-line input and extract device details
def main():
    devices = []
    client_check = 'NO'
    string1 = 'None'
    network_sitename = ''
    # padded_string = '{: <11}'.format(string1)
    
    args = parse_network_arguments()                        # Parse the input arguments
    network_dict = list_networks(organization_id)     # return the networks and the count of how many there   
    keys_to_write = ''
    if args.serials:             ##  Serials have been specified, - look for serial and process
        # Get details for specific devices (comma-separated)
        keys_to_write = DEVICE_KEYS 
        serials = [serial.strip() for serial in args.serials.split(',')]
        
        for serial in serials:
            device = get_device_details(serial)
            # ic(device)
            devices = add_siteinfo(devices,device,network_dict)

    if args.network != None:
        network_choice   = check_network_selection(args.network,len(network_dict))   # check the 
        network_id = network_dict[network_choice]['id']
        network_sitename = {'site': network_dict[network_choice]['name']}

        if args.all:                   ## If argument for ALL is selected then gather ALL devices from site/network
            devices = get_all_devices_in_network(network_id)
            new_devices = []
            for items in devices:
                devices = add_siteinfo(new_devices,items,network_dict)
            keys_to_write = DEVICE_KEYS   
        elif args.clients:
            ##  if Clients have been specified, get the clients attached for the network.
            try:
                print(f"THE NETWORK ID IS : {network_id}")
                devices = get_all_clients(network_id)
                new_devices = []
                for items in devices:
                    devices = add_siteinfo(new_devices,items,network_dict,network_id)
                client_check = 'YES'
                # keys_to_write = DEVICE_KEYS   
            except UnboundLocalError as e:
                print(f"network selection has not been made {e}, please specify  --network X where is the network with the --clients switch")
                print("Example :    --network 3 --clients  ")
        
    if client_check == 'YES':
        keys_to_write = CLIENT_KEYS     # Set the key string to use if a CSV file was written, as the client keys set CLIENT_KEYS = ['mac','description', 'ip', 'status','manufacturer','id','notes']   DEVICE_KEYS = ['name', 'serial', 'mac', 'lanIp', 'model']

    if keys_to_write != None:
       output_table_from_dict(devices, keys_to_write)    

    write_data_csv(devices,args.csv,keys_to_write,network_sitename)

if __name__ == "__main__":
    main()
    
    


############### OLD  CODE , keep around for reference ideas ###################################

################################################################################################
# Routine is redundant but useful for reference
# # Function to get details of a single device by serial
# def get_device_details2(orgz_id,serial):
#     try:
#         # device = dashboard.devices.getDevice(serial)
#         devresponse = dashboard.organizations.getOrganizationInventoryDevice(orgz_id, serial)
#         # print(f"get_device_details device being returned : {device}")
#         print(f"get_device_details device being returned : ")
#         print(f"{devresponse}")
#         pp = pprint.PrettyPrinter(depth=4)
#         pp.pprint(devresponse)
#         # print(type(devresponse))

#         return devresponse
#     except meraki.APIError as e:
#         print(f"Error fetching details for device {serial}: {e}")
#         return None


# Routine is redundant but useful for reference
# # Function to get details of a single device by serial
# def get_device_details3(netid):
#     try:
#         devresponse = dashboard.networks.getNetworkDevices(netid)

#         return devresponse
#     except meraki.APIError as e:
#         print(f"Error fetching details for device {netid}: {e}")
#         return None

################################################################################################
# # Function to write device details to a CSV file
# def write_to_csv(devices, output_file):
       
#     with open(output_file, mode='w', newline='') as file:
#         writer = csv.DictWriter(file, fieldnames=['name', 'serial', 'mac', 'lanIp', 'model'])
#         writer.writeheader()
#         for device in devices:
#             writer.writerow({
#                 'name': device.get('name', ''),
#                 'serial': device.get('serial', ''),
#                 'mac': device.get('mac', ''),
#                 'lanIp': device.get('lanIp', ''),
#                 'model': device.get('model', '')
#             })
#     print(f"Device details written to {output_file}")

# ############################################################################
# # uses the keylist to write a file,  only uses the headers and selects
# # those columns for the CSV file.
# # Code is currently not used, rewri
# ############################################################################
# def write_client_data(devices,output_file,keylist):
#     # keys_to_print = ['mac','description', 'ip', 'status','manufacturer','id','notes']
#     with open(output_file, mode='w', newline='') as file:
#         writer = csv.DictWriter(file, fieldnames=keylist)
#         writer.writeheader()
#         for device in devices:
#             row = {key: device.get(key,'') for key in keylist}
#             writer.writerow(row)
#     print(f"Device details written to {output_file}")


############################################################################
# ######################################################################################
# # Display a set of values from value passed in  dev   ,  which is devices.
# # Read through the list and print the output to the screen
# #
# #
# def display_device_details(dev,p_string):

#             print(f"Site: {dev.get('site', p_string)}, Model: {dev['model']:10} \
#                 Firmware: {dev['firmware']:15} \
#                 Serial: {dev['serial']:15}  \
#                 MAC: {dev['mac']:15}  \
#                 IP:{dev.get('lanIp', p_string)} \
#                 Name: {dev.get('name', p_string)} \
#                 Notes: {dev.get('notes', p_string)} \
#                     " )
