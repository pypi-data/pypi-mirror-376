from __future__ import annotations
from typing import TYPE_CHECKING
import json
from datetime import datetime
from dateutil import parser

# Import for type hints only
if TYPE_CHECKING:
    from .api import api


class Calendar:

    def __init__(self, api: api) -> None:

        self.api = api
        self.endpoint = "calendar"
        self.version = "v2"
        self.tags = {}

        self.per_page = 100
        self.offset = 0

        self.update_tags()

    def update_tags(self) -> None:
        """
        Gets the list of tags.

        Returns:
            None
        """

        url = "calendar/v2/tags?per_page=" + str(self.per_page)

        if self.offset > 0:

            url = url + "&offset=" + str(self.offset)

        resp = self.api._send_request(url)

        for tag in resp["data"]:

            self.tags[tag["attributes"]["name"]] = Tag(api=self.api, id=tag["id"])

        if "next" in resp["meta"] and "offset" in resp["meta"]["next"]:

            self.offset = resp["meta"]["next"]

            self.update_tags()

        else:

            self.offset = 0


class Tag:

    def __init__(self, api: api, id) -> None:
        self.api = api

        self.id = id
        self.type = ""
        self.attributes = {}
        self.links = {}
        self.filter = "approved"

        self.events = []
        self.per_page = 100
        self.offset = 0
        self.recent_searches = {}

        self.update_info()
        self.update_events()

        self.last_update = datetime.now()

    def update_info(self) -> None:
        """
        Update Tag Info

        Returns:
            None
        """
        resp = self.api._send_request(
            "calendar/v2/tags?where[id]=" + self.id,
        )

        self.id = resp["data"][0]["id"]
        self.type = resp["data"][0]["type"]
        self.attributes = resp["data"][0]["attributes"]
        self.links = resp["data"][0]["links"]

    def update_events(self) -> None:
        """
        Update Events that are assigned to the tag

        Returns:
            None
        """

        url = (
            "calendar/v2/tags/"
            + self.id
            + "/event_instances?filter="
            + self.filter
            + "&per_page="
            + str(self.per_page)
        )

        if self.offset > 0:

            url = url + "&offset=" + str(self.offset)

        resp = self.api._send_request(url)

        for event in resp["data"]:

            self.events.append(
                Event(
                    id=event["id"],
                    type=event["type"],
                    attributes=event["attributes"],
                    links=event["links"],
                    relationships=event["relationships"],
                )
            )

        if "next" in resp["meta"] and "offset" in resp["meta"]["next"]:

            self.offset = resp["meta"]["next"]["offset"]

            self.update_events()

        else:

            self.offset = 0

        self.last_update = datetime.now()

    def search_by_date(self, operator, date) -> list:
        """
        Search for Events that are assigned to the tag by date

        Returns:
            List
        """

        filtered_list = []

        if type(date) is str:
            date = parser.parse(date)

        for event in self.events:

            match operator:
                case "after":
                    if event.created_at > date:
                        filtered_list.append(event)
                    elif event.starts_at > date:
                        filtered_list.append(event)
                case "before":
                    if event.created_at < date:
                        filtered_list.append(event)
                    elif event.starts_at < date:
                        filtered_list.append(event)
                case "at":
                    if event.created_at == date:
                        filtered_list.append(event)
                    elif event.starts_at == date:
                        filtered_list.append(event)

        self.recent_searches[operator + "_" + date.strftime("%Y-%m-%dT%H:%M:%sZ")] = {
            "data": filtered_list,
            "date": datetime.now(),
        }

        return filtered_list

    def new_events(self, date="") -> list:
        """
        Searches for events created or started since last update

        Returns:
            List
        """

        if date == "":
            date = self.last_update

        self.update_events()

        events = self.search_by_date(operator="after", date=date)

        return events


class Event:

    def __init__(self, id, type, attributes, links, relationships) -> None:

        self.id = id
        self.type = type
        self.attributes = attributes
        self.links = links
        self.relationships = relationships

        self.created_at = parser.parse(self.attributes["created_at"])
        self.starts_at = parser.parse(self.attributes["starts_at"])
        self.ends_at = parser.parse(self.attributes["ends_at"])

        self.last_update = datetime.now()
