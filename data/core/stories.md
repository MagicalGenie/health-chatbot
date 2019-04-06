## story_goodbye
* goodbye
    - utter_goodbye

## story_thankyou
* thankyou
    - utter_noworries

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
* thankyou
    - utter_noworries
    
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
       
## happy_path2
* search_provider
    - facility_form
    - form{"name": "facility_form"}
    - form{"name": null}
    - find_facilities
* inform
    - find_healthcare_address
    - utter_address
* thankyou
    - utter_noworries

## triage
* symptom
    - action_triage
    - utter_icanhelpu
    - find_facilities
* thankyou
    - utter_noworries