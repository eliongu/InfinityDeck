import requests
import paho.mqtt.client as mqtt
import time
import json
import psutil
import GPUtil

# === CONFIG ===
API_KEY = "3e0271eafa9c0bdc281ba3152d774616"
VILLE = "Paris"
BROKER = "broker.emqx.io"
WEATHER_TOPIC = "infinity/meteo"
DASHBOARD_TOPIC = "infinity/dashboard"

# === WEATHER FUNCTIONS ===
def get_weather(ville):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={ville}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    
    # Extract required data
    weather_data = {
        "temp": round(data["main"]["temp"]),
        "humidity": data["main"]["humidity"],
        "sunrise": data["sys"]["sunrise"],
        "sunset": data["sys"]["sunset"]
    }
    
    return weather_data

# === SYSTEM STATS FUNCTIONS ===
def get_gpu_temp():
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            return int(gpus[0].temperature)
    except:
        return 0

def get_system_stats():
    return {
        "cpu": psutil.cpu_percent(interval=1),
        "ram": psutil.virtual_memory().percent,
        "gpu_temp": get_gpu_temp()
    }

# === MQTT FUNCTIONS ===
def setup_mqtt():
    client = mqtt.Client()
    client.connect(BROKER)
    return client

def send_to_mqtt(client, topic, data):
    client.publish(topic, json.dumps(data))

# === MAIN LOOP ===
def main():
    print("Starting Infinity Server...")
    client = setup_mqtt()
    last_weather_update = 0
    weather_update_interval = 3  
    
    try:
        while True:
            current_time = time.time()
            
            # Update weather data every 30 minutes
            if current_time - last_weather_update >= weather_update_interval:
                try:
                    weather_data = get_weather(VILLE)
                    print("Sending weather data:", weather_data)
                    send_to_mqtt(client, WEATHER_TOPIC, weather_data)
                    last_weather_update = current_time
                except Exception as e:
                    print("Error updating weather:", e)
            
            # Update system stats every 2 seconds
            try:
                stats = get_system_stats()
                print("Sending system stats:", stats)
                send_to_mqtt(client, DASHBOARD_TOPIC, stats)
            except Exception as e:
                print("Error updating system stats:", e)
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nShutting down Infinity Server...")
    except Exception as e:
        print("Unexpected error:", e)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main() 