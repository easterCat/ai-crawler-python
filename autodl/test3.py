import json


def main():
    with open("./scan_result-2023_07_21_14:30.json", 'r') as f:
        f_data = json.load(f)
        for item in f_data:
            print(item)


main()
