import requests

import config


def lookup_access_status(uin):
    headers = {
        'x-api-key': config.ACCESSCTRL_KEY,
        'Accept': 'application/json'
    }

    result = requests.get(config.ACCESSCTRL_API_ENDPOINT + '/' + str(uin), headers=headers)
    if result.status_code == 200:
        return True, {"data": result.json()}
    elif result.status_code == 404:
        return False, {"message": result.json()["message"]}
    else:
        return False, {"message": "Cannot connect to Access Control API!"}

if __name__ == "__main__":
    print(lookup_access_status(uin="123"))
    print(lookup_access_status(uin="987654321"))