# Web and Mobile Application (container)

React single-page web app and React Native mobile app for farmers, agronomists and operations staff:
dashboards (latest telemetry with stale-data flags), alerts, irrigation control with explicit
confirmation of AI recommendations, and farm/device administration.

All calls go through the API Gateway (`https://api.ozagrimate.com.au/api/v1/...`) with a JWT from the
Identity Provider. The UI is **not implemented** in this prototype (the brief excludes it); Postman plays
its role in the demonstration.
