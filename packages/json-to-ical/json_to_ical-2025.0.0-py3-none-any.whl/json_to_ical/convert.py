#!/usr/bin/env python3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from ical.calendar import Calendar
from ical.calendar_stream import IcsCalendarStream
from ical.event import Event


@dataclass
class JsonEvent:
    summary: str
    description: str
    location: str
    start: datetime
    end: datetime


def parse_data(d: dict[str, Any]) -> list[JsonEvent]:
    """convert schedule json to event ready data"""

    result: list[JsonEvent] = []
    time_zone_name = d["schedule"]["conference"]["time_zone_name"]
    tz_info = ZoneInfo(time_zone_name)
    tracks = {x["name"]: x["color"] for x in d["schedule"]["conference"]["tracks"]}
    for day in d["schedule"]["conference"]["days"]:
        for room_name, room_events in day["rooms"].items():
            for room in room_events:
                start_time = datetime.fromisoformat(room["date"]).astimezone(tz_info)
                hours, minutes = map(int, room["duration"].split(":"))
                end_time = start_time + timedelta(hours=hours, minutes=minutes)
                title = (
                    room["title"]
                    if room["track"].startswith("Main")
                    else f"[{room['track']}] {room['title']}"
                )
                if room["persons"]:
                    title += f" - {room['persons'][0]['public_name']}"
                description = room["description"].replace("\r\n", "\n")
                if not description:
                    description = room["abstract"].replace("\r\n", "\n")
                result.append(
                    JsonEvent(
                        summary=title,
                        description=description,
                        location=room_name,
                        start=start_time,
                        end=end_time,
                    )
                )

    return result


def create_ical(json_data: list[JsonEvent]) -> Calendar:
    """create ical file"""
    calendar = Calendar()
    for event in json_data:
        calendar.events.append(
            Event(
                summary=event.summary,
                description=event.description,
                location=event.location,
                dtstart=event.start,
                dtend=event.end,
            )
        )
    return calendar


def write_calendar_file(filename: str, calendar: Calendar):
    with Path(filename).open("w") as f:
        f.write(IcsCalendarStream.calendar_to_ics(calendar))
