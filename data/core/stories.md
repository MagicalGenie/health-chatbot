## story_goodbye
* goodbye
    - utter_goodbye
    - action_restart

## story_thankyou
* thankyou
    - utter_noworries
    - action_restart

## happy_path
* greet
    - find_facility_types
* inform{"facility_type": "rbry-mqwu"}    
    - facility_form
    - form{"name": "facility_form"}
    - form{"name": null}
    - find_facilities
* inform{"facility_id": 4245}
    - find_healthcare_address
    - utter_address
    - action_restart

## happy_path_multi_requests
* greet
    - find_facility_types
* inform{"facility_type": "rbry-mqwu"}
    - facility_form
    - form{"name": "facility_form"}
    - form{"name": null}
    - find_facilities
* inform{"facility_id": "747604"}
    - find_healthcare_address
    - utter_address
* search_provider{"facility_type": "rbry-mqwu"}
    - facility_form
    - form{"name": "facility_form"}
    - form{"name": null}
    - find_facilities
* inform{"facility_id": 4245}   
    - find_healthcare_address
    - utter_address
    - action_restart

## happy_path2
* search_provider
    - facility_form
    - form{"name": "facility_form"}
    - form{"name": null}
    - find_facilities
* inform
    - find_healthcare_address
    - utter_address
    - action_restart


## triage
* symptom
    - utter_icanhelpu
    - action_triage
    - find_facilities
* inform
    - find_healthcare_address
    - utter_address
    - action_restart

## member_info
* member_info
    - utter_member_info
