import json
import requests


def main():
    ip_addr = input("Insert the server IP address: ")
    port = input("Insert the server port: ")

    while True:
        sel = input("Insert the type (d / u) you are looking for, or use 'x' to exit: ")

        if sel == 'd':
            type = "devices"
        elif sel == 'u':
            type = "users"
        elif sel == 'x':
            break
        else:
            print("Input not valid. Use 'd' for devices, 'u' for users, 'x' for exit.")
            continue

        sel = input("Would you like to retreive information about a specific ID? (y / n): ")

        id = ""

        if sel == 'y':
            id = input("Insert the ID: ")
        elif sel != 'n':
            print("Input not valid. Use 'y' to insert ID, 'n' to not to. Continuing as 'n' was pressed...")

        get_url = f"{ip_addr}:{port}/{type}/{id}"

        print(f"[DEBUG] - Sending request to {get_url}")
        r = requests.get(get_url)

        print(f"Request status code: {r.status_code}")


# GET:
#   - uri[0]: type
#   - uri[1]: --optional-- id


if __name__ == '__main__':
    main()