from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from rasa_core_sdk import Tracker
from rasa_core_sdk.executor import CollectingDispatcher

from typing import Dict, Text, Any, List

import requests
import json
from rasa_core_sdk import Action
from rasa_core_sdk import ActionExecutionRejection
from rasa_core_sdk.events import SlotSet, FollowupAction
from rasa_core_sdk.forms import FormAction, REQUESTED_SLOT
import re

ENDPOINTS = {
    "base": "https://data.medicare.gov/resource/{}.json",
    "rbry-mqwu": {
        "city_query": "?city={}",
        "zip_code_query": "?zip_code={}",
        "id_query": "?provider_id={}"
    },
    "b27b-2uc7": {
        "city_query": "?provider_city={}",
        "zip_code_query": "?provider_zip_code={}",
        "id_query": "?federal_provider_number={}"
    },
    "9wzi-peqs": {
        "city_query": "?city={}",
        "zip_code_query": "?zip={}",
        "id_query": "?provider_number={}"
    },
    "c8qv-268j": {
        "city_query": "?cty={}",
        "zip_code_query": "?where=zip like '{}%25'",
        "id_query": "?ind_enrl_id={}",
        "specialty_query": "?pri_spec={}"
    }
}

FACILITY_TYPES = {

    "hospital":
        {
            "name": "hospital",
            "resource": "rbry-mqwu"
        },
    "nursing_home":
        {
            "name": "nursing home",
            "resource": "b27b-2uc7"
        },
    "home_health":
        {
            "name": "Home Health Agency",
            "resource": "9wzi-peqs"
        },
    "doctor":
        {
            "name": "doctor",
            "resource": "c8qv-268j"
        }
}

class FindFacilityTypes(Action):

    def name(self) -> Text:

        return "find_facility_types"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List:

        buttons = []
        for t in FACILITY_TYPES:
            facility_type = FACILITY_TYPES[t]
            payload = "/inform{\"facility_type\": \"" + facility_type.get(
                "resource") + "\"}"

            buttons.append(
                {"title": "{}".format(facility_type.get("name").title()),
                 "payload": payload})

        dispatcher.utter_button_template("utter_greet", buttons, tracker,
                                         button_type="custom")
        return []


def _create_path(base: Text, resource: Text,
                 query: Text, values) -> Text:
    '''Creates a path to find provider using the endpoints.'''

    if isinstance(values, list):
        return (base + query).format(
            resource, ', '.join('"{0}"'.format(w) for w in values))
    else:
        return (base + query).format(resource, values)

def get_nearby_location():
    loc = requests.get("http://ipinfo.io")
    return loc.json()['city']

def _find_facilities(location: Text, resource: Text) -> List[Dict]:
    '''Returns json of facilities matching the search criteria.'''

    if str.isdigit(location):
        full_path = _create_path(ENDPOINTS["base"], resource,
                                 ENDPOINTS[resource]["zip_code_query"],
                                 location)
    elif "near" in location:
        location = get_nearby_location()
        full_path = _create_path(ENDPOINTS["base"], resource,
                                 ENDPOINTS[resource]["city_query"],
                                 location.upper())
    else:
        full_path = _create_path(ENDPOINTS["base"], resource,
                                 ENDPOINTS[resource]["city_query"],
                                 location.upper())

    results = requests.get(full_path).json()
    return results


def _resolve_name(facility_types, resource) ->Text:
    for key, value in facility_types.items():
        if value.get("resource") == resource:
            return value.get("name")
    return ""

def phone_format(phone_number):
    clean_phone_number = re.sub('[^0-9]+', '', phone_number)
    formatted_phone_number = re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1-", "%d" % int(clean_phone_number[:-1])) + clean_phone_number[-1]
    return formatted_phone_number

class FindFacilities(Action):
    '''This action class retrieves a list of all facilities matching
    the supplied search criteria and displays buttons of random search
    results to the user to pick from.'''

    def name(self) -> Text:
        """Unique identifier of the action"""

        return "find_facilities"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List:

        location = tracker.get_slot('location')
        facility_type = tracker.get_slot('facility_type')

        results = _find_facilities(location, facility_type)
        button_name = _resolve_name(FACILITY_TYPES, facility_type)
        if len(results) == 0:
            dispatcher.utter_message(
                "Sorry, we could not find a {} in {}.".format(button_name,
                                                              location))
            return []

        buttons = []
        print("found {} facilities".format(len(results)))
        for r in results:
            if facility_type == FACILITY_TYPES["hospital"]["resource"]:
                facility_id = r.get("provider_id")
                name = r["hospital_name"]
            elif facility_type == FACILITY_TYPES["nursing_home"]["resource"]:
                facility_id = r["federal_provider_number"]
                name = r["provider_name"]
            elif facility_type == FACILITY_TYPES["doctor"]["resource"]:
                facility_id = r["ind_enrl_id"]
                name = "{} {}".format(r["frst_nm"], r["lst_nm"])
            else:
                facility_id = r["provider_number"]
                name = r["provider_name"]

            payload = "/inform{\"facility_id\":\"" + facility_id + "\"}"
            buttons.append(
                {"title": "{}".format(name.title()), "payload": payload})

        # limit number of buttons to 3 here for clear presentation purpose
        if "near" in location:
            location = "you"
            
        dispatcher.utter_button_message(
            "Here is a list of {} {}s near {}".format(len(buttons[:3]),
                                                       button_name,
                                                       location),
            buttons[:3], button_type="custom")
        # todo: note: button options are not working BUG in rasa_core

        return []


class FindHealthCareAddress(Action):
    '''This action class retrieves the address of the users
    healthcare facility choice to display it to the user.'''

    def name(self) -> Text:
        """Unique identifier of the action"""

        return "find_healthcare_address"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict]:

        facility_type = tracker.get_slot('facility_type')
        healthcare_id = tracker.get_slot("facility_id")
        full_path = _create_path(ENDPOINTS["base"], facility_type,
                                 ENDPOINTS[facility_type]["id_query"],
                                 healthcare_id)
        results = requests.get(full_path).json()
        selected = results[0]
        if facility_type == FACILITY_TYPES["hospital"]["resource"]:
            address = "{}, {}, {}".format(selected["address"].title(),
                                          selected["zip_code"].title(),
                                          selected["city"].title())
        elif facility_type == FACILITY_TYPES["nursing_home"]["resource"]:
            address = "{}, {}, {}".format(selected["provider_address"].title(),
                                          selected["provider_zip_code"].title(),
                                          selected["provider_city"].title())
        elif facility_type == FACILITY_TYPES["doctor"]["resource"]:
            adr = selected["adr_ln_1"].title()
            if "adr_ln_2" in selected.keys():
                adr += " {}".format(selected["adr_ln_2"].title())
            address = "{}, {}, {} {}\n Call {} to set up an appointment".format(adr,
                                          selected["cty"].title(),
                                          selected["st"],
                                          selected["zip"][:5].title(),
                                          phone_format(selected["phn_numbr"])
                                          )
        else:
            address = "{}, {}, {}".format(selected["address"].title(),
                                          selected["zip"].title(),
                                          selected["city"].title())

        return [
            SlotSet("facility_address", address if results is not None else "")]


class FacilityForm(FormAction):
    """Custom form action to fill all slots required to find specific type
    of healthcare facilities in a certain city or zip code."""

    def name(self) -> Text:
        """Unique identifier of the form"""

        return "facility_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""

        return ["facility_type", "location"]

    def slot_mappings(self) -> Dict[Text, Any]:
        return {
            "facility_type": self.from_entity(entity="facility_type",
                                              intent=["inform",
                                                      "search_provider"]),
            "location": self.from_entity(entity="location",
                                         intent=["inform",
                                                 "search_provider"])}

    def validate(self,
                 dispatcher: CollectingDispatcher,
                 tracker: Tracker,
                 domain: Dict[Text, Any]
                 ) -> List[Dict]:

        """Validate extracted requested slot
        else reject the execution of the form action"""

        # extract other slots that were not requested
        # but set by corresponding entity
        slot_values = self.extract_other_slots(dispatcher, tracker, domain)

        # extract requested slot
        slot_to_fill = tracker.get_slot(REQUESTED_SLOT)
        if slot_to_fill:
            slot_values.update(self.extract_requested_slot(dispatcher,
                                                           tracker, domain))
            if not slot_values:
                # reject form action execution
                # if some slot was requested but nothing was extracted
                # it will allow other policies to predict another action
                raise ActionExecutionRejection(self.name(),
                                               "Failed to validate slot {0} "
                                               "with action {1}"
                                               "".format(slot_to_fill,
                                                         self.name()))

        return [SlotSet(slot, value) for slot, value in slot_values.items()]

    def submit(self,
               dispatcher: CollectingDispatcher,
               tracker: Tracker,
               domain: Dict[Text, Any]
               ) -> List[Dict]:

        """Define what the form has to do
            after all required slots are filled"""

        # utter submit template
        dispatcher.utter_template('utter_submit', tracker)
        return [FollowupAction('find_facilities')]


class ActionChitchat(Action):
    """Returns the chitchat utterance dependent on the intent"""

    def name(self) -> Text:
        """Unique identifier of the action"""

        return "action_chitchat"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List:

        intent = tracker.latest_message['intent'].get('name')

        # retrieve the correct chitchat utterance dependent on the intent
        if intent in ['ask_builder', 'ask_weather', 'ask_howdoing',
                      'ask_whatspossible', 'ask_whatisrasa', 'ask_isbot',
                      'ask_howold', 'ask_languagesbot', 'ask_restaurant',
                      'ask_time', 'ask_wherefrom', 'ask_whoami',
                      'handleinsult', 'nicetomeeyou', 'telljoke',
                      'ask_whatismyname', 'howwereyoubuilt', 'ask_whoisit']:
            dispatcher.utter_template('utter_' + intent, tracker)

        return []


def get_ts_host():
    # host = "http://tensorsearch.dev.aetnadigital.net/"
    # try:
    #     res = requests.get(host + "healthcheck")
    # except ConnectionError:
    #     print("Unable to connect to DEV env. Defaulting to local runtime.")
    # if res.status_code == 200:
    #     host += "tensorsearch"
    #     return host
    # else:
    return "http://localhost:5000/tensorsearch"

def triage_request(search_term): 
    return {"search_terms": [search_term]}

def _find_specialties(location: Text, specialty: Text, resource: Text) -> List[Dict]:
    '''Returns json of facilities matching the search criteria.'''
    values = []
    values.append(specialty)
    if str.isdigit(location):
        values.insert(0, location)
        full_path = _create_path(ENDPOINTS["base"], resource,
                                 ENDPOINTS[resource]["zip_code_query"] + ENDPOINTS[resource]["specialty_query"],
                                 values)
    elif "near" in location:
        location = get_nearby_location()
        values.insert(0, location.upper())
        full_path = _create_path(ENDPOINTS["base"], resource,
                                 ENDPOINTS[resource]["city_query"] + ENDPOINTS[resource]["specialty_query"],
                                 values)
    else:
        values.insert(0, location)
        full_path = _create_path(ENDPOINTS["base"], resource,
                                 ENDPOINTS[resource]["city_query"]  + ENDPOINTS[resource]["specialty_query"],
                                 values)

    results = requests.get(full_path).json()
    return results

class FindSpecialtyDoctor(Action):

    def name(self) -> Text:
        return "find_specialty_doctor"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List:

        location = tracker.get_slot('location')
        facility_type = tracker.get_slot('facility_type')
        specialty = tracker.get_slot('specialty')

        results = _find_specialties(location, facility_type)
        button_name = _resolve_name(FACILITY_TYPES, facility_type)
        if len(results) == 0:
            dispatcher.utter_message(
                "Sorry, we could not find a {} in {}.".format(button_name,
                                                              location))
            return []

        buttons = []
        print("found {} facilities".format(len(results)))
        for r in results:
            facility_id = r["ind_enrl_id"]
            name = "{} {}".format(r["frst_nm"], r["lst_nm"])

            payload = "/inform{\"facility_id\":\"" + facility_id + "\"}"
            buttons.append(
                {"title": "{}".format(name.title()), "payload": payload})

        # limit number of buttons to 3 here for clear presentation purpose
        if "near" in location:
            location = "you"
            
        dispatcher.utter_button_message(
            "Here is a list of {} {}s near {}".format(len(buttons[:3]),
                                                       button_name,
                                                       location),
            buttons[:3], button_type="custom")
        # todo: note: button options are not working BUG in rasa_core

        return []

class ActionTriage(Action):
    def name(self):
        return "action_triage"

    def run(self, dispatcher, tracker, domain):
        symptom = tracker.get_slot('symptom')
        host = get_ts_host()
        res = requests.post(host, json=triage_request(symptom))
        specialty = json.loads(res.json())[symptom][0][0]
        # include code to include specialty slot
        print(specialty)
        return [SlotSet("specialty", specialty),
                SlotSet("location", "nearby"),
                SlotSet("facility_type", "c8qv-268j"),
                FollowupAction('find_facilities')
                ]
