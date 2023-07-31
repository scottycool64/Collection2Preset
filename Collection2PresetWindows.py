import requests
import json
import os
import re
import winreg
import sys
def add_preset_to_file(file_path, collection_id):
    try:
        # Load existing presets from file
        with open(file_path, 'r') as file:
            presets = json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON in file '{file_path}'.")
        return

    # Check if a preset with the same name already exists
    preset_name = get_collection_name(collection_id)
    if preset_name in presets:
        print(f"A preset with the name '{preset_name}' already exists.")
        overwrite_option = input("Select an option:\n1. Overwrite existing preset\n2. Rename the new preset\n3. Cancel\nEnter the option number: ")
        if overwrite_option == "1":
            presets.pop(preset_name)
        elif overwrite_option == "2":
            new_preset_name = input("Enter a new name for the preset: ")
            if new_preset_name == preset_name:
                print("Error: The new name cannot be the same as the existing name.")
                return
            preset_name = new_preset_name
        else:
            print("Aborted. No changes made to the presets.")
            return

    # Fetch collection details from the Steam API
    api_url_contents = "https://api.steampowered.com/ISteamRemoteStorage/GetCollectionDetails/v1/"
    data_contents = {
        "collectioncount": 1,
        "publishedfileids[0]": collection_id
    }
    try:
        response_contents = requests.post(api_url_contents, data=data_contents)
        response_contents_data = response_contents.json()
        collection_contents = response_contents_data.get("response", {}).get("collectiondetails", [])
        resultcount = response_contents_data.get("response", {}).get("resultcount")
        if resultcount == 0:
            input("Error: Not a Collection. Press Enter to Exit.")
            sys.exit()
    except requests.RequestException:
        print("Error: Failed to fetch collection contents from the Steam API.")
        return
    except json.JSONDecodeError:
        print("Error: Failed to parse API response.")
        return

    if not collection_contents:
        print(f"Error: Collection with ID '{collection_id}' not found.")
        return

    # Extract the enabled addon IDs from the collection details
    enabled_addon_ids = [item.get("publishedfileid") for item in collection_contents[0].get("children", [])]
    
    # Add the new preset to the presets dictionary
    new_preset = {
        "disabled": [],
        "enabled": enabled_addon_ids,
        "name": preset_name,
        "newAction": "disable"
    }
    presets[preset_name] = new_preset

    try:
        # Write the modified presets back to the file
        with open(file_path, 'w') as file:
            json.dump(presets, file, separators=(',', ':'))
        print(f"Preset '{preset_name}' successfully added to '{file_path}'.")
    except IOError:
        print(f"Error: Failed to write to file '{file_path}'.")
        return
    except Exception as e:
        print(f"Error: An unexpected error occurred: {str(e)}")
        return

def get_collection_name(collection_id):
    api_url_details = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
    data_details = {
        "itemcount": 1,
        "publishedfileids[0]": collection_id
    }

    try:
        response_details = requests.post(api_url_details, data=data_details)
        response_details_data = response_details.json()
        print(response_details.text)
        collection_details = response_details_data.get("response", {}).get("publishedfiledetails", [])
    except requests.RequestException:
        print("Error: Failed to fetch collection details from the Steam API.")
        return
    except json.JSONDecodeError:
        print("Error: Failed to parse API response.")
        return

    if not collection_details:
        print(f"Error: Collection with ID '{collection_id}' not found.")
        return None
    if collection_details[0].get("consumer_app_id") != 4000:
        input("Error: Collection not for Garry's Mod! Press Enter to Exit")
        sys.exit()
    return collection_details[0].get("title")

# Usage example

# Function to read the registry value
def read_registry_value(key, subkey, value_name):
    try:
        registry_key = winreg.OpenKey(key, subkey)
        value, _ = winreg.QueryValueEx(registry_key, value_name)
        winreg.CloseKey(registry_key)
        return value
    except WindowsError:
        return None

# Read SteamPath from the registry
steam_path = read_registry_value(winreg.HKEY_CURRENT_USER, "SOFTWARE\\Valve\\Steam", "SteamPath")
if steam_path is not None:
    # Append the steamapps folder to the Steam path
    steamapps_path = os.path.join(steam_path, "steamapps")

    # Read libraryfolders.vdf content
    libraryfolders_path = os.path.join(steamapps_path, "libraryfolders.vdf")
    with open(libraryfolders_path, "r") as file:
        libraryfolders_content = file.read()

    # Find the Steam directory for Garry's Mod (app ID: 4000)
    match = re.search(r"\"0\"\s+?\{\s+?\"path\"\s+?\"([^\"]+)\"", libraryfolders_content)
    if match:
        steam_directory = match.group(1)
        gmod_path = os.path.join(steam_directory, "steamapps", "common", "GarrysMod", "garrysmod", "settings")
        if not os.path.isabs(gmod_path):
            gmod_path = os.path.join(steam_path, gmod_path)
        gmod_path = os.path.normpath(gmod_path)  # Normalize the path
        addon_presets_file = gmod_path+"\\addonpresets.txt"
        if os.path.isfile(gmod_path+"\\addonpresets.txt"):
            print("Found presets file at ", gmod_path+"\\addonpresets.txt")
        else:
            print("addonpresets.txt not present. Please open gmod and make a preset first!")
    else:
        print("No Steam library folder found for Garry's Mod (app ID: 4000).")
        input("Press Enter to Exit")
        sys.exit()
else:
    print("SteamPath value not found in the registry.")
    input("Press Enter to Exit")
    sys.exit()

collection_id = input("Enter the collection ID: ")
print("Backing up preset file to presetbackup.txt.")
def copy_file(source_file, destination_file):
    destination_file_base = os.path.splitext(destination_file)[0]  # Get the base filename without extension
    destination_file_ext = os.path.splitext(destination_file)[1]  # Get the file extension

    # Check if the destination file already exists
    if os.path.exists(destination_file):
        counter = 1
        while os.path.exists(f"{destination_file_base}_{counter}{destination_file_ext}"):
            counter += 1
        destination_file = f"{destination_file_base}_{counter}{destination_file_ext}"

    with open(source_file, 'r') as source:
        with open(destination_file, 'w') as destination:
            destination.write(source.read())

destination_file = 'presetbackup.txt'

copy_file(addon_presets_file, destination_file)
print(f"Addon presets file copied to '{destination_file}' successfully.")
add_preset_to_file(addon_presets_file, collection_id)
input("Press Enter to Exit")
