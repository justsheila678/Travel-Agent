import flet as ft
import requests
import datetime

# get countries

def get_country_info(name):
    global country_link
    country_link = f"https://restcountries.com/v3.1/name/{name}?fullText=true"

    try:
        response = requests.get(country_link)
        if response.status_code != 200:
            return None

        data = response.json()[0]
        lat, lon = data.get("latlng", [0, 0])

        weather_response = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        )

        temp_display = "N/A"
        if weather_response.status_code == 200:
            celsius = weather_response.json().get("current_weather", {}).get("temperature")
            fahrenheit = (celsius * 9 / 5) + 32
            temp_display = f"{celsius}°C / {fahrenheit:.1f}°F"

        return {
            "official_name": data.get("name", {}).get("official", "N/A"),
            "capital": data.get("capital", ["N/A"])[0],
            "region": f"{data.get('region')} ({data.get('subregion')})",
            "population": str(data.get("population", 0)),
            "currency": ", ".join([c["name"] for c in data.get("currencies").values()]),
            "languages": ", ".join(data.get("languages").values()),
            "flag": data.get("flags", {}).get("png", ""),
            "timezones": ", ".join(data.get("timezones")),
            "weather": temp_display,
            "code": data.get("cca2"),
        }
    except:
        return None

# autocomplete

def fetch_country_suggestions(query):
    try:
        response = requests.get(f"https://restcountries.com/v3.1/name/{query}")
        return [c["name"]["common"] for c in response.json()[:5]]
    except:
        return []


def main(page: ft.Page):
    page.title = "Global Travel Agency"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive"

    # COUNTRY SEARCH

    search_input = ft.TextField(label="Enter Country Name", width=400)
    suggestions1 = ft.Column(spacing=5)
    results_area = ft.Column(visible=False, spacing=15)

    def choose_search_country(name):
        search_input.value = name
        suggestions1.controls = []
        page.update()

    def select_country(e):
        query = search_input.value.strip().lower()
        if len(query) < 2:
            suggestions1.controls = []
            page.update()
            return

        suggestions1.controls = [
            ft.TextButton(text=name, on_click=lambda e, n=name: choose_search_country(n))
            for name in fetch_country_suggestions(query)
        ]
        page.update()

    # show country info

    def handle_search(e):
        data = get_country_info(search_input.value.strip())
        if not data:
            return

        results_area.controls = [
            ft.Image(src=data["flag"], width=250, border_radius=10),
            ft.Text(data["official_name"], size=28, weight="bold"),
            ft.Text(
                f"📍 Capital: {data['capital']} | 🌡️ Weather: {data['weather']}",
                size=20, color="blue", weight="w600"
            ),
            ft.Divider(),
            ft.Text(f"Region: {data['region']}"),
            ft.Text(f"Population: {data['population']}"),
            ft.Text(f"Currency: {data['currency']}"),
            ft.Text(f"Languages: {data['languages']}"),
            ft.Text(f"Time Zones: {data['timezones']}"),
            ft.Text(f"Country Code: {data['code']}")
        ]
        results_area.visible = True
        page.update()

    search_input.on_change = select_country

    # tab 1 content

    tab1content = ft.Column(
        [
            ft.Text("🌍 Travel Agency Search Portal", size=32, weight="bold"),
            search_input,
            suggestions1,
            ft.ElevatedButton("Search", icon=ft.Icons.SEARCH, on_click=handle_search),
            ft.Divider(),
            results_area
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15)

    # TRAVEL PLAN

    destinations = []
    selected_start_date = {"value": None}
    start_date_display = ft.Text("No start date selected", italic=True, color="grey")

    # set destination from suggestions

    def choose_destination_country(name):
        destination_country.value = name
        suggestions.controls = []
        page.update()

    # autocomplete for destination input

    def select_destination(e):
        query = destination_country.value.strip().lower()
        if len(query) < 2:
            suggestions.controls = []
            page.update()
            return

        suggestions.controls = [
            ft.TextButton(text=name, on_click=lambda e, n=name: choose_destination_country(n))
            for name in fetch_country_suggestions(query)
            ]
        
        page.update()

    # date picker

    def handle_date_picked(e):
        selected_start_date["value"] = e.control.value
        formatted = e.control.value.strftime("%B %d, %Y")
        start_date_display.value = f"✈️ Departure: {formatted}"
        start_date_display.color = "white"
        start_date_display.italic = False
        page.update()

    def open_date_picker(e):
        page.open(
            ft.DatePicker(
                first_date=datetime.datetime.now(),
                last_date=datetime.datetime(2030, 12, 31),
                on_change=handle_date_picked,
            ))

    # add destination to plan

    def add_to_plan(e):
        if not client_name.value.strip() or not destination_country.value.strip() or not duration_at_destination.value.strip():
            return

        country = destination_country.value.strip()
        days = duration_at_destination.value.strip()
        extra_info = extras.value.strip()
        start_date = selected_start_date["value"]

        if start_date:
            end_date = start_date + datetime.timedelta(days=int(days))
            date_range = f"{start_date.strftime('%b %d')} → {end_date.strftime('%b %d, %Y')}"
        else:
            date_range = "Dates TBD"

        destinations.append((country, days, extra_info, date_range))
        plan_header.value = f"{client_name.value.capitalize()}'s Travel Plan"
        plan.value = "\n".join([
            f"{country}  |  {duration}  |  {days} days" + (f"  |  Notes: {extras}" if extras else "")
            for country, days, extras, duration in destinations
        ])

        # reset values

        destination_country.value = ""
        duration_at_destination.value = ""
        extras.value = ""
        selected_start_date["value"] = None
        start_date_display.value = "No start date selected"
        start_date_display.color = "grey"
        start_date_display.italic = True
        page.update()

    # check that only digits are entered for duration

    def validate_days_input(e):
        filtered = "".join(c for c in duration_at_destination.value if c.isdigit())
        if filtered != duration_at_destination.value:
            duration_at_destination.value = filtered
            page.update()

    client_name = ft.TextField(hint_text="Enter Full Name", width=400)

    destination_country = ft.TextField(hint_text="Enter Destination Country", width=400)
    destination_country.on_change = select_destination

    duration_at_destination = ft.TextField(
        hint_text="Duration (days)",
        width=265,
        on_change=validate_days_input,
        keyboard_type=ft.KeyboardType.NUMBER)

    suggestions = ft.Column(spacing=5)
    add_button = ft.ElevatedButton("Add to Plan", icon=ft.Icons.ADD, on_click=add_to_plan)
    extras = ft.TextField(hint_text="Additional Notes", width=400, multiline=True)
    plan = ft.Text("")
    plan_header = ft.Text("")

    date_picker_button = ft.ElevatedButton("Pick Start Date", icon=ft.Icons.CALENDAR_TODAY,
                        on_click=open_date_picker, width=400)

    tab2content = ft.Column(
        [
            ft.Text("Create Travel Plan", size=28, weight="bold"),
            client_name,
            destination_country,
            suggestions,
            date_picker_button,
            start_date_display,
            extras,
            ft.Row([duration_at_destination, add_button], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            plan_header,
            ft.Row([plan], alignment=ft.MainAxisAlignment.START)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

    # PRICING TAB

    tab3content = ft.Column(
        [ft.Text("Pricing Overview", size=28, weight="bold")],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # ADDING TABS

    page.add(ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Country Search", content=tab1content),
            ft.Tab(text="Travel Plan", content=tab2content),
            ft.Tab(text="Pricing", content=tab3content)
        ]))


ft.app(target=main)