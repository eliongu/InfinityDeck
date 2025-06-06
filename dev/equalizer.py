import time
import random
import network
from machine import Pin
import neopixel
from umqtt.simple import MQTTClient
import sys

# === CONFIGURATIONS ===
NUM_LEDS = 256
PIN_LED = 12
MQTT_BROKER = "broker.emqx.io"  # À adapter
MQTT_TOPIC = b"infinity/test"
DEVICE_ID = b"equalizer01"

# Module names
MODULE_NAME = "equalizer"
AVAILABLE_MODULES = ["clock", "equalizer", "weather", "dashboard"]

np = neopixel.NeoPixel(Pin(PIN_LED, Pin.OUT), NUM_LEDS)
prev_matrix = [(0, 0, 0)] * NUM_LEDS

# Couleurs des colonnes
COLORS = [
    (0, 40, 0), (40, 40, 0), (40, 20, 0), (40, 0, 0),
    (40, 0, 20), (20, 0, 40), (0, 0, 40), (0, 40, 40)
]

BACKGROUND_COLOR = (0, 0, 0)
module_active = True  # Pour sortir de la boucle si MQTT demande autre chose

# === FONCTIONS LED ===

def clear():
    for i in range(NUM_LEDS):
        np[i] = BACKGROUND_COLOR
    np.write()

def set_pixel_16x16(x, y, color):
    if not (0 <= x < 16 and 0 <= y < 16):
        return None
    if y < 8:
        matrice = 0 if x < 8 else 3
        x_local, y_local = (x, y) if x < 8 else (x - 8, y)
    else:
        matrice = 1 if x < 8 else 2
        x_local, y_local = (x, y - 8) if x < 8 else (x - 8, y - 8)

    index = y_local * 8 + (x_local if y_local % 2 == 0 else 7 - x_local)
    led_index = matrice * 64 + index
    if np[led_index] != color:
        np[led_index] = color
        prev_matrix[led_index] = color
        return led_index
    return None

def draw_equalizer(levels):
    leds_changed = set()
    for col in range(8):
        level = levels[col]
        x_start = col * 2
        color = COLORS[col]
        for x in range(x_start, x_start + 2):
            for y in range(16):
                idx = set_pixel_16x16(x, y, color if y >= 16 - level else BACKGROUND_COLOR)
                if idx is not None:
                    leds_changed.add(idx)
    if leds_changed:
        np.write()

def interpolate(a, b, t):
    return a + (b - a) * t

def smooth_levels(curr_levels, target_levels, steps=10, delay=0.001):
    for step in range(steps + 1):
        t = step / steps
        interp_levels = [int(interpolate(c, target, t)) for c, target in zip(curr_levels, target_levels)]
        draw_equalizer(interp_levels)
        time.sleep(delay)

# === MQTT CALLBACK ===

def mqtt_callback(topic, msg):
    try:
        test_msg = msg.decode().lower()
        print(f"Received test message: {test_msg}")
        
        if test_msg == "dashboard":
            import dashboard
            dashboard.main_loop(dashboard.DEVICE_ID, "iPhonenono", "nonolagrinta")
        elif test_msg == "clock":
            import clock
            clock.main_loop(clock.DEVICE_ID, "iPhonenono", "nonolagrinta")
        elif test_msg == "weather":
            import weather
            weather.main_loop(weather.DEVICE_ID, "iPhonenono", "nonolagrinta")
        elif test_msg == "clear":
            clear()
    except Exception as e:
        print(f"Error in MQTT callback: {e}")

# === WIFI & MQTT SETUP ===

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(0.5)
    print("WiFi connecté:", wlan.ifconfig())

def setup_mqtt():
    client = MQTTClient(DEVICE_ID, MQTT_BROKER)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(MQTT_TOPIC)
    print("MQTT connecté et abonné à", MQTT_TOPIC)
    return client

# === MAIN LOOP ===

def main_loop(client_id, ssid, password):
    curr_levels = [0] * 8
    client = setup_mqtt()
    
    while True:
        target_levels = [random.randint(0, 16) for _ in range(8)]
        smooth_levels(curr_levels, target_levels, steps=10, delay=0.0001)
        curr_levels = target_levels
        client.check_msg()  # Check for MQTT messages

# === MAIN ===

def main():
    """Main function to run the equalizer module"""
    global module_active
    module_active = True  # Reset the flag when starting
    connect_wifi("iPhonenono", "nonolagrinta")
    main_loop(DEVICE_ID, "iPhonenono", "nonolagrinta")
    clear()  # Clean up display when exiting
    print("Equalizer exited")

if __name__ == "__main__":
    main()
