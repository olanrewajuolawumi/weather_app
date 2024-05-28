import requests                              # Importing the requests library to make HTTP requests
import json                                  # Importing the json library to handle JSON data
import streamlit as st                       # Importing Streamlit for building the web application
from datetime import datetime, timedelta     # Importing datetime and timedelta for date/time operations
import pandas as pd                          # Importing Pandas for data manipulation
#import plotly.express as px                  # Importing Plotly Express for interactive plotting

# OpenWeatherMap API key for authentication
API_KEY = "5072ad7f4035efb616cf1bf99c568ef0"

# Function to make API calls to OpenWeatherMap API
def make_api_call(endpoint, params=None):
    url = f"https://api.openweathermap.org/data/2.5/{endpoint}"
    if params:
        params["appid"] = API_KEY
    else:
        params = {"appid": API_KEY}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Checking for HTTP errors
        return response.json()  # Parsing JSON response
    except requests.exceptions.HTTPError:
        return None  # Returning None if HTTP error occurs
    except json.JSONDecodeError:
        return None  # Returning None if JSON decoding error occurs

# Function to make API calls to historical OpenWeatherMap API
def make_api_call_historical(endpoint, params=None):
    url = f"https://history.openweathermap.org/data/2.5/{endpoint}"
    if params:
        params["appid"] = API_KEY
    else:
        params = {"appid": API_KEY}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Checking for HTTP errors
        return response.json()  # Parsing JSON response
    except requests.exceptions.HTTPError:
        return None  # Returning None if HTTP error occurs
    except json.JSONDecodeError:
        return None  # Returning None if JSON decoding error occurs

def build_current_weather_url(city, country):
    return f"weather?q={city},{country}"

def build_air_pollution_url(lat, lon):
    return f"air_pollution?lat={lat}&lon={lon}"

def build_historical_weather_url(lat, lon, start_date, end_date):
    return f"history/city?lat={lat}&lon={lon}&start={start_date}&end={end_date}"

def build_forecast_url(lat, lon):
    return f"forecast?lat={lat}&lon={lon}"

def get_current_weather(city, country):
    url = build_current_weather_url(city, country)
    data = make_api_call(url)
    print("API Response Data:", data)  # Debugging statement to show API response
    if data and data['cod'] == 200:
        temperature_kelvin = data['main'].get('temp')
        humidity = data['main'].get('humidity')
        weather_description = data['weather'][0].get('description')
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        temperature_celsius = round(temperature_kelvin - 273.15, 2) if temperature_kelvin is not None else None
        air_quality, pollutant = get_air_quality(data['coord']['lat'], data['coord']['lon'])
        return temperature_celsius, humidity, weather_description, current_time, air_quality, pollutant
    else:
        return None, None, None, None, None, None

def get_air_quality(lat, lon):
    url = build_air_pollution_url(lat, lon)
    data = make_api_call(url)
    if data and 'list' in data:
        main_pollutant = data['list'][0]['components']
        pollutant = max(main_pollutant, key=main_pollutant.get)
        air_quality = data['list'][0]['main']['aqi']
        return air_quality, pollutant
    else:
        return None, None

def get_historical_weather_data(lat, lon, start_date, end_date):
    endpoint = f"history/city?lat={lat}&lon={lon}&start={start_date}&end={end_date}"
    return make_api_call_historical(endpoint)

def get_forecast(lat, lon):
    url = build_forecast_url(lat, lon)
    data = make_api_call(url)
    if data and data['cod'] == '200':
        return data['list']
    else:
        return None

def display_weather(city, temperature_celsius, humidity, weather_description, air_quality, pollutant):
    st.write(f"Weather: {weather_description}")
    st.write(f"Temperature: {temperature_celsius}°C")
    st.write(f"Humidity: {humidity}%")  
    if air_quality is not None:
        st.write(f"Air Quality Index: {air_quality}")
        st.write(f"Main Pollutant: {pollutant}")

def display_historical_weather(city, data):
    st.title(f"Historical weather for past few days in {city}:")
    if not data:
        st.write("Historical weather data not found.")
        return
    if isinstance(data, dict) and 'list' in data:
        data = data['list']
    time_of_day = [datetime.utcfromtimestamp(entry['dt']).strftime('%d/%m/%Y %H:%M:%S') for entry in data]
    weather_description = [entry['weather'][0]['description'] for entry in data]
    temperature_kelvin = [entry['main']['temp'] for entry in data]
    humidity = [entry['main']['humidity'] for entry in data]
    temperature_celsius = [round(temp - 273.15, 2) for temp in temperature_kelvin]
    
    df = pd.DataFrame({
        'Time': time_of_day,
        'Temperature (°C)': temperature_celsius,
        'Humidity (%)': humidity,
        'Weather Description': weather_description
    })

    fig = px.line(df, x='Time', y=['Temperature (°C)', 'Humidity (%)'], 
                  title=f"Historical weather data for {city}")
    st.plotly_chart(fig)
    st.write("Historical Weather Data")
    st.write(df)

def display_forecast(city, data):
    st.title(f"Weather forecast for the upcoming days in {city}:")
    time_of_day = [datetime.fromisoformat(entry['dt_txt']).strftime('%d/%m/%Y %H:%M:%S') for entry in data]
    weather_description = [entry['weather'][0]['description'] for entry in data]
    temperature_kelvin = [entry['main']['temp'] for entry in data]
    humidity = [entry['main']['humidity'] for entry in data]
    temperature_celsius = [round(temp - 273.15, 2) for temp in temperature_kelvin]

    df = pd.DataFrame({
        'Time': time_of_day,
        'Temperature (°C)': temperature_celsius,
        'Humidity (%)': humidity,
        'Weather Description': weather_description
    })

    fig = px.line(df, x='Time', y=['Temperature (°C)', 'Humidity (%)'], 
                  title=f"Weather forecast for {city}")
    st.plotly_chart(fig)
    st.write("Forecast Data:")
    st.write(df)

def get_city_coordinates(city, country):
    url = build_current_weather_url(city, country)
    data = make_api_call(url)
    if data and data['cod'] == 200:
        return data['coord']['lat'], data['coord']['lon']
    else:
        return None, None

def get_countries_for_city(city):
    if not city:
        return []
    url = f"find?q={city}&type=like"
    data = make_api_call(url)
    if data and data['cod'] == "200":
        countries = {entry['sys']['country'] for entry in data['list']}
        return list(countries)
    else:
        return []

def test_current_weather(city, country):
    if city and country:
        temperature_celsius, humidity, weather_description, current_time, air_quality, pollutant = get_current_weather(city, country)
        assert temperature_celsius is not None, "Temperature data is missing"
        assert humidity is not None, "Humidity data is missing"
        assert weather_description is not None, "Weather description is missing"
        print("Current weather data retrieval successful")
    else:
        print("City or country not provided, skipping test")

def test_historical_weather(city, country, start_date, end_date):
    if city and country:
        coordinates = get_city_coordinates(city, country)
        if coordinates:
            start_date_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
            end_date_timestamp = int(datetime.combine(end_date, datetime.min.time()).timestamp())
            historical_data = get_historical_weather_data(coordinates[0], coordinates[1], start_date_timestamp, end_date_timestamp)
            assert historical_data is not None, "Historical weather data retrieval failed"
            print("Historical weather data retrieval successful")
    else:
        print("City or country not provided, skipping test")

def test_forecast(city, country):
    if city and country:
        coordinates = get_city_coordinates(city, country)
        if coordinates:
            forecast_data = get_forecast(coordinates[0], coordinates[1])
            assert forecast_data is not None, "Weather forecast data retrieval failed"
            print("Weather forecast data retrieval successful")
    else:
        print("City or country not provided, skipping test")

if __name__ == "__main__":
    st.header("Weather App For You")
    st.image("https://images.theconversation.com/files/442675/original/file-20220126-17-1i0g402.jpg?ixlib-rb-1.1.0&c")

    st.sidebar.header("Filters")
    city = st.sidebar.text_input("Enter city name", "")
    countries = get_countries_for_city(city)
    country = st.sidebar.selectbox("Select country", countries) if countries else ""
    weather_option = st.sidebar.selectbox("Select weather option", ["Current Weather", "Historical Weather", "Weather Forecast"])

    if not city:
        st.warning("Please enter a city name.")
    else:
        if weather_option == "Current Weather":
            st.subheader(f"{weather_option}")
            temperature_celsius, humidity, weather_description, current_time, air_quality, pollutant = get_current_weather(city, country)
            if temperature_celsius is not None:
                st.title(f"Current Weather in {city}, {country} at {current_time}:")
                display_weather(city, temperature_celsius, humidity, weather_description, air_quality, pollutant)
            else:
                st.error("Failed to retrieve current weather data.")
        elif weather_option == "Historical Weather":
            st.subheader(f"{weather_option}")
            current_datetime = datetime.now()
            start_date = st.sidebar.date_input("Select start date", current_datetime - timedelta(days=4), format="DD/MM/YYYY")
            end_date = st.sidebar.date_input("Select end date", current_datetime, format="DD/MM/YYYY")
            coordinates = get_city_coordinates(city, country)
            if coordinates:
                start_date_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
                end_date_timestamp = int(datetime.combine(end_date, datetime.min.time()).timestamp())
                historical_data = get_historical_weather_data(coordinates[0], coordinates[1], start_date_timestamp, end_date_timestamp)
                if historical_data is not None:
                    st.title("Historical Weather Data:")
                    display_historical_weather(city, historical_data)
                else:
                    st.error("Failed to retrieve historical weather data.")
            else:
                st.error("Failed to retrieve coordinates for the selected city.")
        elif weather_option == "Weather Forecast":
            st.subheader(f"{weather_option}")
            start_date = st.sidebar.date_input("Select start date", datetime.now(), format="DD/MM/YYYY")
            end_date = st.sidebar.date_input("Select end date", datetime.now() + timedelta(days=5), format="DD/MM/YYYY")
            coordinates = get_city_coordinates(city, country)
            if coordinates:
                forecast_data = get_forecast(coordinates[0], coordinates[1])
                if forecast_data is not None:
                    display_forecast(city, forecast_data)
                else:
                    st.error("Failed to retrieve weather forecast data.")
            else:
                st.error("Failed to retrieve coordinates for the selected city.")

    test_current_weather(city, country)
    test_historical_weather(city, country, datetime.now() - timedelta(days=5), datetime.now())
    test_forecast(city, country)
