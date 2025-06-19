from typing import List, Optional, Dict, Any, Callable
from pydantic import BaseModel, Field
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import openai
import requests
import os
import json
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set.")
if not OPENWEATHER_API_KEY:
    raise ValueError("OPENWEATHER_API_KEY is not set.")

# Gemini OpenAI-compatible setup
openai.api_key = gemini_api_key
openai.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

# ----------- STATE & AGENT CLASSES -----------

class WeatherState(BaseModel):
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    last_interaction: Optional[datetime] = None
    saved_locations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)

    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_interaction = datetime.now()

    def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self.conversation_history[-limit:]

    def save_location(self, location: str, data: Dict[str, Any]):
        self.saved_locations[location] = data

def tool_decorator(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.is_tool = True
    return wrapper

class WeatherAgent:
    def __init__(self, name="WeatherWise", temperature=0.7, model="gemini-2.0-flash"):
        self.state = WeatherState()
        self.name = name
        self.model = model
        self.temperature = temperature
        self.tools = self._register_tools()
        self.setup_agent()

    def _register_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get current weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City name or coordinates"}
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather_forecast",
                    "description": "Get weather forecast for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"},
                            "days": {"type": "integer"}
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_air_quality",
                    "description": "Get air quality index for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        },
                        "required": ["location"]
                    }
                }
            }
        ]

    def setup_agent(self):
        self.instructions = """You are WeatherWise, an expert weather assistant powered by Gemini.
Your job is to provide weather, forecast, air quality, and interesting facts."""

    def _parse_location(self, location: str) -> Dict[str, Any]:
        try:
            if "," in location:
                lat, lon = map(float, location.split(","))
                return {"lat": lat, "lon": lon}
            else:
                return {"q": location}
        except Exception:
            return {"q": location}

    @tool_decorator
    def get_current_weather(self, location: str) -> Dict[str, Any]:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = self._parse_location(location)
        params["appid"] = OPENWEATHER_API_KEY
        params["units"] = self.state.user_preferences.get("units", "metric")

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return {
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"]
            }
        return {"error": f"Failed to get weather data: {response.status_code}"}

    @tool_decorator
    def get_weather_forecast(self, location: str, days: int = 3) -> Dict[str, Any]:
        url = "http://api.openweathermap.org/data/2.5/forecast"
        params = self._parse_location(location)
        params["appid"] = OPENWEATHER_API_KEY
        params["units"] = self.state.user_preferences.get("units", "metric")

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return {
                "forecast": data["list"][:days],
                "city": data.get("city", {}).get("name", "Unknown")
            }
        return {"error": f"Failed to get forecast data: {response.status_code}"}

    @tool_decorator
    def get_air_quality(self, location: str) -> Dict[str, Any]:
        coords = self._parse_location(location)

        if "lat" in coords and "lon" in coords:
            lat, lon = coords["lat"], coords["lon"]
        else:
            geo_url = "http://api.openweathermap.org/geo/1.0/direct"
            response = requests.get(geo_url, params={**coords, "limit": 1, "appid": OPENWEATHER_API_KEY})
            if response.status_code == 200 and response.json():
                lat, lon = response.json()[0]["lat"], response.json()[0]["lon"]
            else:
                return {"error": "Unable to resolve location to coordinates"}

        aq_url = "http://api.openweathermap.org/data/2.5/air_pollution"
        aq_params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}
        aq_response = requests.get(aq_url, params=aq_params)
        if aq_response.status_code == 200:
            aq_data = aq_response.json()
            return {
                "aqi": aq_data["list"][0]["main"]["aqi"],
                "components": aq_data["list"][0]["components"]
            }

        return {"error": "Failed to get air quality data"}

    def save_location(self, location: str, data: Dict[str, Any]):
        self.state.save_location(location, data)

    def update_preferences(self, preferences: Dict[str, Any]):
        self.state.user_preferences.update(preferences)

    def get_state_summary(self):
        return {
            "conversation_count": len(self.state.conversation_history),
            "last_interaction": self.state.last_interaction.isoformat() if self.state.last_interaction else None,
            "saved_locations": list(self.state.saved_locations.keys()),
            "preferences": self.state.user_preferences
        }

# ----------- FASTAPI SETUP -----------

app = FastAPI(title="WeatherWise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = WeatherAgent()

# Request models
class LocationRequest(BaseModel):
    location: str

class ForecastRequest(BaseModel):
    location: str
    days: Optional[int] = 3

class PreferencesRequest(BaseModel):
    preferences: Dict[str, Any]

class SaveLocationRequest(BaseModel):
    name: str
    data: Dict[str, Any]

# Routes
@app.get("/")
def read_root():
    return {"message": "Welcome to WeatherWise API!"}

@app.post("/weather/current")
def current_weather(req: LocationRequest):
    return agent.get_current_weather(req.location)

@app.post("/weather/forecast")
def weather_forecast(req: ForecastRequest):
    return agent.get_weather_forecast(req.location, req.days)

@app.post("/weather/air-quality")
def air_quality(req: LocationRequest):
    return agent.get_air_quality(req.location)

@app.post("/preferences")
def update_preferences(req: PreferencesRequest):
    agent.update_preferences(req.preferences)
    return {"message": "Preferences updated."}

@app.post("/locations")
def save_location(req: SaveLocationRequest):
    agent.save_location(req.name, req.data)
    return {"message": f"Location '{req.name}' saved."}

@app.get("/agent/state")
def agent_state():
    return agent.get_state_summary()


# from typing import List, Optional, Dict, Any, Callable
# from pydantic import BaseModel, Field
# from datetime import datetime
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# import openai
# import requests
# import os
# import json
# from dotenv import load_dotenv
# from functools import wraps

# # Load environment variables
# load_dotenv()
# gemini_api_key = os.getenv("GEMINI_API_KEY")
# OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# if not gemini_api_key:
#     raise ValueError("GEMINI_API_KEY is not set.")
# if not OPENWEATHER_API_KEY:
#     raise ValueError("OPENWEATHER_API_KEY is not set.")

# # Gemini as OpenAI-compatible API
# openai.api_key = gemini_api_key
# openai.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

# # ----------- STATE & AGENT CLASSES -----------

# class WeatherState(BaseModel):
#     conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
#     last_interaction: Optional[datetime] = None
#     saved_locations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
#     user_preferences: Dict[str, Any] = Field(default_factory=dict)

#     def add_to_history(self, role: str, content: str):
#         self.conversation_history.append({
#             "role": role,
#             "content": content,
#             "timestamp": datetime.now().isoformat()
#         })
#         self.last_interaction = datetime.now()

#     def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
#         return self.conversation_history[-limit:]

#     def save_location(self, location: str, data: Dict[str, Any]):
#         self.saved_locations[location] = data

# def tool_decorator(func: Callable) -> Callable:
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         return func(*args, **kwargs)
#     wrapper.is_tool = True
#     return wrapper

# class WeatherAgent:
#     def __init__(self, name="WeatherWise", temperature=0.7, model="gemini-2.0-flash"):
#         self.state = WeatherState()
#         self.name = name
#         self.model = model
#         self.temperature = temperature
#         self.tools = self._register_tools()
#         self.setup_agent()

#     def _register_tools(self):
#         return [
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "get_current_weather",
#                     "description": "Get current weather for a location",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "location": {"type": "string", "description": "City name"}
#                         },
#                         "required": ["location"]
#                     }
#                 }
#             },
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "get_weather_forecast",
#                     "description": "Get weather forecast for a location",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "location": {"type": "string"},
#                             "days": {"type": "integer"}
#                         },
#                         "required": ["location"]
#                     }
#                 }
#             },
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "get_air_quality",
#                     "description": "Get air quality index for a location",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "location": {"type": "string"}
#                         },
#                         "required": ["location"]
#                     }
#                 }
#             }
#         ]

#     def setup_agent(self):
#         self.instructions = """You are WeatherWise, an expert weather assistant powered by Gemini.
# Your job is to provide weather, forecast, air quality, and interesting facts."""

#     @tool_decorator
#     def get_current_weather(self, location: str) -> Dict[str, Any]:
#         url = f"http://api.openweathermap.org/data/2.5/weather"
#         params = {
#             "q": location,
#             "appid": OPENWEATHER_API_KEY,
#             "units": self.state.user_preferences.get("units", "metric")
#         }
#         response = requests.get(url, params=params)
#         if response.status_code == 200:
#             data = response.json()
#             return {
#                 "temperature": data["main"]["temp"],
#                 "feels_like": data["main"]["feels_like"],
#                 "humidity": data["main"]["humidity"],
#                 "description": data["weather"][0]["description"],
#                 "wind_speed": data["wind"]["speed"]
#             }
#         return {"error": f"Failed to get weather data: {response.status_code}"}

#     @tool_decorator
#     def get_weather_forecast(self, location: str, days: int = 3) -> Dict[str, Any]:
#         url = f"http://api.openweathermap.org/data/2.5/forecast"
#         params = {
#             "q": location,
#             "appid": OPENWEATHER_API_KEY,
#             "units": self.state.user_preferences.get("units", "metric")
#         }
#         response = requests.get(url, params=params)
#         if response.status_code == 200:
#             data = response.json()
#             return {
#                 "forecast": data["list"][:days],
#                 "city": data["city"]["name"]
#             }
#         return {"error": f"Failed to get forecast data: {response.status_code}"}

#     @tool_decorator
#     def get_air_quality(self, location: str) -> Dict[str, Any]:
#         geo_url = f"http://api.openweathermap.org/geo/1.0/direct"
#         params = {
#             "q": location,
#             "limit": 1,
#             "appid": OPENWEATHER_API_KEY
#         }
#         response = requests.get(geo_url, params=params)
#         if response.status_code == 200 and response.json():
#             lat, lon = response.json()[0]["lat"], response.json()[0]["lon"]
#             aq_url = f"http://api.openweathermap.org/data/2.5/air_pollution"
#             aq_params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}
#             aq_response = requests.get(aq_url, params=aq_params)
#             if aq_response.status_code == 200:
#                 aq_data = aq_response.json()
#                 return {
#                     "aqi": aq_data["list"][0]["main"]["aqi"],
#                     "components": aq_data["list"][0]["components"]
#                 }
#         return {"error": "Failed to get air quality data"}

#     def save_location(self, location: str, data: Dict[str, Any]):
#         self.state.save_location(location, data)

#     def update_preferences(self, preferences: Dict[str, Any]):
#         self.state.user_preferences.update(preferences)

#     def get_state_summary(self):
#         return {
#             "conversation_count": len(self.state.conversation_history),
#             "last_interaction": self.state.last_interaction.isoformat() if self.state.last_interaction else None,
#             "saved_locations": list(self.state.saved_locations.keys()),
#             "preferences": self.state.user_preferences
#         }

# # ----------- FASTAPI SETUP -----------

# app = FastAPI(title="WeatherWise API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# agent = WeatherAgent()

# # Request models
# class LocationRequest(BaseModel):
#     location: str

# class ForecastRequest(BaseModel):
#     location: str
#     days: Optional[int] = 3

# class PreferencesRequest(BaseModel):
#     preferences: Dict[str, Any]

# class SaveLocationRequest(BaseModel):
#     name: str
#     data: Dict[str, Any]

# # Routes
# @app.get("/")
# def read_root():
#     return {"message": "Welcome to WeatherWise API!"}

# @app.post("/weather/current")
# def current_weather(req: LocationRequest):
#     return agent.get_current_weather(req.location)

# @app.post("/weather/forecast")
# def weather_forecast(req: ForecastRequest):
#     return agent.get_weather_forecast(req.location, req.days)

# @app.post("/weather/air-quality")
# def air_quality(req: LocationRequest):
#     return agent.get_air_quality(req.location)

# @app.post("/preferences")
# def update_preferences(req: PreferencesRequest):
#     agent.update_preferences(req.preferences)
#     return {"message": "Preferences updated."}

# @app.post("/locations")
# def save_location(req: SaveLocationRequest):
#     agent.save_location(req.name, req.data)
#     return {"message": f"Location '{req.name}' saved."}

# @app.get("/agent/state")
# def agent_state():
#     return agent.get_state_summary()



# # from typing import List, Optional, Dict, Any, Callable
# # from pydantic import BaseModel, Field
# # from datetime import datetime
# # from fastapi import FastAPI
# # from fastapi.middleware.cors import CORSMiddleware
# # import openai
# # import requests
# # import os
# # import json
# # from dotenv import load_dotenv
# # from functools import wraps
# # from agents import AsyncOpenAI, OpenAIChatCompletionsModel

# # # Load environment variables
# # load_dotenv()
# # gemini_api_key = os.getenv("GEMINI_API_KEY")
# # OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# # if not gemini_api_key:
# #     raise ValueError("GEMINI_API_KEY is not set.")
# # if not OPENWEATHER_API_KEY:
# #     raise ValueError("OPENWEATHER_API_KEY is not set.")

# # # Gemini API as OpenAI compatible
# # external_client = AsyncOpenAI(
# #     api_key=gemini_api_key,
# #     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
# # )

# # model = OpenAIChatCompletionsModel(
# #     model="gemini-2.0-flash",
# #     openai_client=external_client
# # )

# # # ----------- STATE & AGENT CLASSES -----------

# # class WeatherState(BaseModel):
# #     conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
# #     last_interaction: Optional[datetime] = None
# #     saved_locations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
# #     user_preferences: Dict[str, Any] = Field(default_factory=dict)

# #     def add_to_history(self, role: str, content: str):
# #         self.conversation_history.append({
# #             "role": role,
# #             "content": content,
# #             "timestamp": datetime.now().isoformat()
# #         })
# #         self.last_interaction = datetime.now()

# #     def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
# #         return self.conversation_history[-limit:]

# #     def save_location(self, location: str, data: Dict[str, Any]):
# #         self.saved_locations[location] = data

# # def tool_decorator(func: Callable) -> Callable:
# #     @wraps(func)
# #     def wrapper(*args, **kwargs):
# #         return func(*args, **kwargs)
# #     wrapper.is_tool = True
# #     return wrapper

# # class WeatherAgent:
# #     def __init__(self, name="WeatherWise", temperature=0.7, model="gpt-4"):
# #         self.state = WeatherState()
# #         self.name = name
# #         self.model = model
# #         self.temperature = temperature
# #         self.tools = self._register_tools()
# #         self.setup_agent()

# #     def _register_tools(self):
# #         return [
# #             {
# #                 "type": "function",
# #                 "function": {
# #                     "name": "get_current_weather",
# #                     "description": "Get current weather for a location",
# #                     "parameters": {
# #                         "type": "object",
# #                         "properties": {
# #                             "location": {"type": "string", "description": "City name"}
# #                         },
# #                         "required": ["location"]
# #                     }
# #                 }
# #             },
# #             {
# #                 "type": "function",
# #                 "function": {
# #                     "name": "get_weather_forecast",
# #                     "description": "Get weather forecast for a location",
# #                     "parameters": {
# #                         "type": "object",
# #                         "properties": {
# #                             "location": {"type": "string"},
# #                             "days": {"type": "integer"}
# #                         },
# #                         "required": ["location"]
# #                     }
# #                 }
# #             },
# #             {
# #                 "type": "function",
# #                 "function": {
# #                     "name": "get_air_quality",
# #                     "description": "Get air quality index for a location",
# #                     "parameters": {
# #                         "type": "object",
# #                         "properties": {
# #                             "location": {"type": "string"}
# #                         },
# #                         "required": ["location"]
# #                     }
# #                 }
# #             }
# #         ]

# #     def setup_agent(self):
# #         self.instructions = """You are WeatherWise, an expert weather assistant powered by OpenAI.
# # Your job is to provide weather, forecast, air quality, and interesting facts."""

# #     @tool_decorator
# #     def get_current_weather(self, location: str) -> Dict[str, Any]:
# #         url = f"http://api.openweathermap.org/data/2.5/weather"
# #         params = {
# #             "q": location,
# #             "appid": OPENWEATHER_API_KEY,
# #             "units": self.state.user_preferences.get("units", "metric")
# #         }
# #         response = requests.get(url, params=params)
# #         if response.status_code == 200:
# #             data = response.json()
# #             return {
# #                 "temperature": data["main"]["temp"],
# #                 "feels_like": data["main"]["feels_like"],
# #                 "humidity": data["main"]["humidity"],
# #                 "description": data["weather"][0]["description"],
# #                 "wind_speed": data["wind"]["speed"]
# #             }
# #         return {"error": f"Failed to get weather data: {response.status_code}"}

# #     @tool_decorator
# #     def get_weather_forecast(self, location: str, days: int = 3) -> Dict[str, Any]:
# #         url = f"http://api.openweathermap.org/data/2.5/forecast"
# #         params = {
# #             "q": location,
# #             "appid": OPENWEATHER_API_KEY,
# #             "units": self.state.user_preferences.get("units", "metric")
# #         }
# #         response = requests.get(url, params=params)
# #         if response.status_code == 200:
# #             data = response.json()
# #             return {
# #                 "forecast": data["list"][:days],
# #                 "city": data["city"]["name"]
# #             }
# #         return {"error": f"Failed to get forecast data: {response.status_code}"}

# #     @tool_decorator
# #     def get_air_quality(self, location: str) -> Dict[str, Any]:
# #         geo_url = f"http://api.openweathermap.org/geo/1.0/direct"
# #         params = {
# #             "q": location,
# #             "limit": 1,
# #             "appid": OPENWEATHER_API_KEY
# #         }
# #         response = requests.get(geo_url, params=params)
# #         if response.status_code == 200 and response.json():
# #             lat, lon = response.json()[0]["lat"], response.json()[0]["lon"]
# #             aq_url = f"http://api.openweathermap.org/data/2.5/air_pollution"
# #             aq_params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}
# #             aq_response = requests.get(aq_url, params=aq_params)
# #             if aq_response.status_code == 200:
# #                 aq_data = aq_response.json()
# #                 return {
# #                     "aqi": aq_data["list"][0]["main"]["aqi"],
# #                     "components": aq_data["list"][0]["components"]
# #                 }
# #         return {"error": "Failed to get air quality data"}

# #     def save_location(self, location: str, data: Dict[str, Any]):
# #         self.state.save_location(location, data)

# #     def update_preferences(self, preferences: Dict[str, Any]):
# #         self.state.user_preferences.update(preferences)

# #     def get_state_summary(self):
# #         return {
# #             "conversation_count": len(self.state.conversation_history),
# #             "last_interaction": self.state.last_interaction.isoformat() if self.state.last_interaction else None,
# #             "saved_locations": list(self.state.saved_locations.keys()),
# #             "preferences": self.state.user_preferences
# #         }

# # # ----------- FASTAPI SETUP -----------

# # app = FastAPI(title="WeatherWise API")

# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # agent = WeatherAgent()

# # class LocationRequest(BaseModel):
# #     location: str

# # class ForecastRequest(BaseModel):
# #     location: str
# #     days: Optional[int] = 3

# # class PreferencesRequest(BaseModel):
# #     preferences: Dict[str, Any]

# # class SaveLocationRequest(BaseModel):
# #     name: str
# #     data: Dict[str, Any]

# # @app.get("/")
# # def read_root():
# #     return {"message": "Welcome to WeatherWise API!"}

# # @app.post("/weather/current")
# # def current_weather(req: LocationRequest):
# #     return agent.get_current_weather(req.location)

# # @app.post("/weather/forecast")
# # def weather_forecast(req: ForecastRequest):
# #     return agent.get_weather_forecast(req.location, req.days)

# # @app.post("/weather/air-quality")
# # def air_quality(req: LocationRequest):
# #     return agent.get_air_quality(req.location)

# # @app.post("/preferences")
# # def update_preferences(req: PreferencesRequest):
# #     agent.update_preferences(req.preferences)
# #     return {"message": "Preferences updated."}

# # @app.post("/locations")
# # def save_location(req: SaveLocationRequest):
# #     agent.save_location(req.name, req.data)
# #     return {"message": f"Location '{req.name}' saved."}

# # @app.get("/agent/state")
# # def agent_state():
# #     return agent.get_state_summary()


# from typing import List, Optional, Dict, Any, Callable
# from pydantic import BaseModel, Field
# import openai
# from datetime import datetime
# import os
# from dotenv import load_dotenv
# import requests
# import json
# from functools import wraps
# from agents import AsyncOpenAI, OpenAIChatCompletionsModel, ModelSettings

# # Load environment variables from .env file
# load_dotenv()
# gemini_api_key = os.getenv("GEMINI_API_KEY")
# OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# # Check if the API keys are present; if not, raise an error
# if not gemini_api_key:
#     raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")
# if not OPENWEATHER_API_KEY:
#     raise ValueError("OPENWEATHER_API_KEY is not set. Please ensure it is defined in your .env file.")

# #Reference: https://ai.google.dev/gemini-api/docs/openai
# external_client = AsyncOpenAI(
#     api_key=gemini_api_key,
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
# )

# model = OpenAIChatCompletionsModel(
#     model="gemini-2.0-flash",
#     openai_client=external_client
# )
# # Configure API keys


# class WeatherState(BaseModel):
#     """State management for the weather agent"""
#     conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
#     last_interaction: Optional[datetime] = None
#     saved_locations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
#     user_preferences: Dict[str, Any] = Field(default_factory=dict)
    
#     def add_to_history(self, role: str, content: str):
#         self.conversation_history.append({
#             "role": role,
#             "content": content,
#             "timestamp": datetime.now().isoformat()
#         })
#         self.last_interaction = datetime.now()
    
#     def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
#         return self.conversation_history[-limit:]
    
#     def save_location(self, location: str, data: Dict[str, Any]):
#         self.saved_locations[location] = data

# def tool_decorator(func: Callable) -> Callable:
#     """Decorator to register functions as tools"""
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         return func(*args, **kwargs)
#     wrapper.is_tool = True
#     return wrapper

# class WeatherAgent:
#     def __init__(
#         self,
#         name: str = "WeatherWise",
#         temperature: float = 0.7,
#         model: str = "gpt-4"
#     ):
#         self.state = WeatherState()
#         self.name = name
#         self.model = model
#         self.temperature = temperature
#         self.tools = self._register_tools()
#         self.setup_agent()
    
#     def _register_tools(self) -> List[Dict[str, Any]]:
#         """Register available tools"""
#         return [
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "get_current_weather",
#                     "description": "Get current weather for a location",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "location": {
#                                 "type": "string",
#                                 "description": "City name or coordinates"
#                             }
#                         },
#                         "required": ["location"]
#                     }
#                 }
#             },
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "get_weather_forecast",
#                     "description": "Get weather forecast for a location",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "location": {
#                                 "type": "string",
#                                 "description": "City name or coordinates"
#                             },
#                             "days": {
#                                 "type": "integer",
#                                 "description": "Number of days for forecast (1-5)"
#                             }
#                         },
#                         "required": ["location"]
#                     }
#                 }
#             },
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "get_air_quality",
#                     "description": "Get air quality index for a location",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "location": {
#                                 "type": "string",
#                                 "description": "City name or coordinates"
#                             }
#                         },
#                         "required": ["location"]
#                     }
#                 }
#             }
#         ]
    
#     def setup_agent(self):
#         """Initialize the agent with its core instructions and capabilities"""
#         self.instructions = """You are WeatherWise, an expert weather assistant powered by OpenAI.
        
#         YOUR EXPERTISE:
#         - Real-time weather data and forecasts
#         - Weather patterns and phenomena
#         - Climate science and meteorology
#         - Weather-related safety advice
#         - Air quality information
        
#         CAPABILITIES:
#         - Get current weather conditions
#         - Provide weather forecasts
#         - Check air quality
#         - Save and manage locations
#         - Track user preferences
        
#         STYLE:
#         - Use clear, accessible language
#         - Include interesting weather facts when relevant
#         - Be enthusiastic about meteorology
#         - Always consider user's saved locations and preferences
#         """
    
#     @tool_decorator
#     def get_current_weather(self, location: str) -> Dict[str, Any]:
#         """Get current weather for a location using OpenWeatherMap API"""
#         url = f"http://api.openweathermap.org/data/2.5/weather"
#         params = {
#             "q": location,
#             "appid": OPENWEATHER_API_KEY,
#             "units": self.state.user_preferences.get("units", "metric")
#         }
#         response = requests.get(url, params=params)
#         if response.status_code == 200:
#             data = response.json()
#             return {
#                 "temperature": data["main"]["temp"],
#                 "feels_like": data["main"]["feels_like"],
#                 "humidity": data["main"]["humidity"],
#                 "description": data["weather"][0]["description"],
#                 "wind_speed": data["wind"]["speed"]
#             }
#         else:
#             return {"error": f"Failed to get weather data: {response.status_code}"}
    
#     @tool_decorator
#     def get_weather_forecast(self, location: str, days: int = 5) -> Dict[str, Any]:
#         """Get weather forecast for a location"""
#         url = f"http://api.openweathermap.org/data/2.5/forecast"
#         params = {
#             "q": location,
#             "appid": OPENWEATHER_API_KEY,
#             "units": self.state.user_preferences.get("units", "metric")
#         }
#         response = requests.get(url, params=params)
#         if response.status_code == 200:
#             data = response.json()
#             return {
#                 "forecast": data["list"][:days],
#                 "city": data["city"]["name"]
#             }
#         else:
#             return {"error": f"Failed to get forecast data: {response.status_code}"}
    
#     @tool_decorator
#     def get_air_quality(self, location: str) -> Dict[str, Any]:
#         """Get air quality index for a location"""
#         # First get coordinates
#         url = f"http://api.openweathermap.org/geo/1.0/direct"
#         params = {
#             "q": location,
#             "limit": 1,
#             "appid": OPENWEATHER_API_KEY
#         }
#         response = requests.get(url, params=params)
#         if response.status_code == 200:
#             location_data = response.json()
#             if location_data:
#                 lat, lon = location_data[0]["lat"], location_data[0]["lon"]
                
#                 # Get air quality data
#                 aq_url = f"http://api.openweathermap.org/data/2.5/air_pollution"
#                 aq_params = {
#                     "lat": lat,
#                     "lon": lon,
#                     "appid": OPENWEATHER_API_KEY
#                 }
#                 aq_response = requests.get(aq_url, params=aq_params)
#                 if aq_response.status_code == 200:
#                     aq_data = aq_response.json()
#                     return {
#                         "aqi": aq_data["list"][0]["main"]["aqi"],
#                         "components": aq_data["list"][0]["components"]
#                     }
#         return {"error": "Failed to get air quality data"}
    
#     def process_message(self, message: str) -> str:
#         # Add user message to history
#         self.state.add_to_history("user", message)
        
#         # Prepare context from state
#         context = {
#             "recent_history": self.state.get_recent_history(),
#             "saved_locations": self.state.saved_locations,
#             "user_preferences": self.state.user_preferences
#         }
        
#         # Create the system message with context
#         system_message = {
#             "role": "system",
#             "content": f"{self.instructions}\n\nContext: {json.dumps(context, indent=2)}"
#         }
        
#         # Create the user message
#         user_message = {
#             "role": "user",
#             "content": message
#         }
        
#         # Get response from OpenAI with function calling
#         response = openai.ChatCompletion.create(
#             model=self.model,
#             messages=[system_message, user_message],
#             temperature=self.temperature,
#             functions=self.tools,
#             function_call="auto"
#         )
        
#         # Process the response
#         response_message = response.choices[0].message
        
#         # Check if the model wants to call a function
#         if response_message.get("function_call"):
#             function_name = response_message["function_call"]["name"]
#             function_args = json.loads(response_message["function_call"]["arguments"])
            
#             # Call the appropriate function
#             if function_name == "get_current_weather":
#                 result = self.get_current_weather(**function_args)
#             elif function_name == "get_weather_forecast":
#                 result = self.get_weather_forecast(**function_args)
#             elif function_name == "get_air_quality":
#                 result = self.get_air_quality(**function_args)
            
#             # Get final response with function result
#             final_response = openai.ChatCompletion.create(
#                 model=self.model,
#                 messages=[
#                     system_message,
#                     user_message,
#                     response_message,
#                     {
#                         "role": "function",
#                         "name": function_name,
#                         "content": json.dumps(result)
#                     }
#                 ],
#                 temperature=self.temperature
#             )
            
#             response_text = final_response.choices[0].message.content
#         else:
#             response_text = response_message.content
        
#         # Add response to history
#         self.state.add_to_history("assistant", response_text)
        
#         return response_text
    
#     def save_location(self, location: str, data: Dict[str, Any]):
#         """Save a location and its associated data"""
#         self.state.save_location(location, data)
    
#     def update_preferences(self, preferences: Dict[str, Any]):
#         """Update user preferences"""
#         self.state.user_preferences.update(preferences)
    
#     def get_state_summary(self) -> Dict[str, Any]:
#         """Get a summary of the agent's current state"""
#         return {
#             "conversation_count": len(self.state.conversation_history),
#             "last_interaction": self.state.last_interaction.isoformat() if self.state.last_interaction else None,
#             "saved_locations": list(self.state.saved_locations.keys()),
#             "preferences": self.state.user_preferences
#         }
