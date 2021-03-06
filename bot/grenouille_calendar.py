import threading, logging
from datetime import datetime, timezone
from apiclient import discovery


class Event:
    """A calendar event.

    Attributes
        start - starting TimeDate of the event
        end - ending TimeDate of the event
        summary - simple description of the event
    """

    def __init__(self, start, end, summary):
        self.start = start
        self.end = end
        self.summary = summary

    def __str__(self):
        """How the event will be displayed in chat.
        """
        now = datetime.now(timezone.utc)
        days = self.start - now
        result = ''
        if days.days > 0:
            result = 'J+{0} '.format(days.days)
        return '{0}{1} - {2} {3}'.format(result, self.start.strftime("%H:%M"), self.end.strftime("%H:%M"), self.summary)


class GrenouilleCalendar:
    """The module of the bot responsible for the calendar reading.

    Attributes
        grenouille_bot - The main class the module is linked to.

        calendar_timer - thread waiting 1hour to update the update
    """

    def __init__(self, grenouille_bot):
        self.grenouille_bot = grenouille_bot
        self.calendar_timer = None

    def start(self):
        """Start the GrenouilleCalendar module.
        Non Blocking
        """
        self.calendar_timer = threading.Timer(10, self.update_events_from_calendar).start()

    def stop(self):
        """Stop the GrenouilleCalendar module
        """
        self.calendar_timer.cancel()

    def update_events_from_calendar(self):
        """Read google calendar to update the list of event, every hour.
        """
        new_calendar = []
        try:
            service = discovery.build('calendar', 'v3',
                                           developerKey=self.grenouille_bot.config['DEFAULT']['calendar_key'],
                                           cache_discovery=False)
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='qnv4k3c3upl94sj41pui158k3c@group.calendar.google.com',
                timeMin=now,
                maxResults=5,
                singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])

            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                start = datetime.strptime(''.join(start.rsplit(':', 1)), "%Y-%m-%dT%H:%M:%S%z")
                end = event['end'].get('dateTime', event['end'].get('date'))
                end = datetime.strptime(''.join(end.rsplit(':', 1)), "%Y-%m-%dT%H:%M:%S%z")
                summary = event['summary']
                new_calendar.append(Event(start, end, summary))
        except Exception:
            logging.exception('Error while requesting calendar.')

        del self.grenouille_bot.event_list[:]
        for event in new_calendar:
            self.grenouille_bot.event_list.append(event)
        self.calendar_timer = threading.Timer(60 * 60, self.update_events_from_calendar).start()
