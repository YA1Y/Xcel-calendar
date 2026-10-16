# Xcel-calendar

X-Cel Swimming **Group 5** practice and meet schedule as an Apple Calendar subscription,
transcribed from the monthly calendars on https://swimxcel.org/calendar/ and checked daily.

## Subscribe

On iPhone, tap this link:
**webcal://raw.githubusercontent.com/YA1Y/Xcel-calendar/main/xcel-grp5.ics**

Or go to Settings → Apps → Calendar → Calendar Accounts → Add Account → Other →
Add Subscribed Calendar, and paste:
`https://raw.githubusercontent.com/YA1Y/Xcel-calendar/main/xcel-grp5.ics`

On a Mac: Calendar → File → New Calendar Subscription, and paste the same URL.

The repo must stay **public** for the subscription to work. The schedule is already
public on the team website.

## Files

- `events.json`: the schedule data (one row per practice, plus all-day meets/holidays)
- `build.py`: turns `events.json` into `xcel-grp5.ics`
- `check.py`: detects new or changed month images on the team site
- `CLAUDE.md`: the daily update procedure
