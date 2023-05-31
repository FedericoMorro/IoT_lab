import json
import requests


def main():
    ip_addr = input("Insert the server IP address: ")
    port = input("Insert the server port: ")

    while True:
        sel = input("Insert the type (d / u) you are looking for, or use 'c' to exit: ")
        if sel == 'c':
            break

        if sel == 'd':
            type = "devices"
        if sel == 'u':
            type = "users"
        else:
            print("Input not valid. Use 'd' for devices and 'u' for users.")
            continue

        sel = input("Would you like to retreive information about a specific ID? (y / n): ")

        if sel == 'y':
            id = input("Insert the ID: ")
        elif sel != 'n':
            print("Input not valid. Use 'y' to insert ID, 'n' to not to. Continuing as 'n' was pressed...")

        get_url = f"{ip_addr}:{port}/{type}/{id}"
        r = requests.get(get_url)

        print(f"Request status code: {r.status_code}")


# GET:
#   - uri[0]: type
#   - uri[1]: --optional-- id


if __name__ == '__main__':
    main()