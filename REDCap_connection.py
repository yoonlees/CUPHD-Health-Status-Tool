import json

import requests

import config


def set_REDCap_status(new_uin, new_status):
    # Fetch REDCap record for given new_uin and load it into dictionary
    data = {
        'token': config.REDCAP_TOKEN,
        'content': 'record',
        'format': 'json',
        'type': 'flat',
        'csvDelimiter': '',
        'rawOrLabel': 'raw',
        'rawOrLabelHeaders': 'raw',
        'exportCheckboxLabel': 'false',
        'exportSurveyFields': 'false',
        'exportDataAccessGroups': 'false',
        'returnFormat': 'json',
        'filterLogic': '[test_id] = ' + new_uin
    }
    match_record_request = requests.post(config.REDCAP_API_ENDPOINT, data=data)
    if match_record_request.status_code == 200:
        match_record = match_record_request.json()
        if len(match_record) > 0:
            match_record = dict(match_record[0])
        else:
            return False, {"message": "No matching record was found"}

        # Update record with new_status and convert dictionary to string for import
        if new_status.lower() == "Quarantine".lower():
            match_record['test_status'] = '1'
        elif new_status.lower() == "Isolate".lower():
            match_record['test_status'] = '2'
        elif new_status.lower() == "Release.lower()":
            match_record['test_status'] = '3'
        import_json = json.dumps(match_record)

        # overwrite record back into REDCap
        data = {
            'token': config.REDCAP_TOKEN,
            'content': 'record',
            'format': 'json',
            'type': 'flat',
            'overwriteBehavior': 'normal',
            'forceAutoNumber': 'false',
            'data': "[" + import_json + "]",
            'returnContent': 'count',
            'returnFormat': 'json'
        }
        overwrite_request = requests.post(config.REDCAP_API_ENDPOINT, data=data)
        if overwrite_request.status_code == 200:
            result = overwrite_request.json()

            if result['count'] >= 1:
                return True, {"data": "Successfully published new status to REDCAP"}
            else:
                return False, {"message":"Cannot publish new status to REDCAP"}
        else:
            return False, {"message": "Fail to connect to REDCAP"}
    else:
        return False, {"message": "Fail to connect to REDCAP"}

if __name__ == "__main__":
    print(set_REDCap_status(new_uin="668905810", new_status="released"))