import time
import json
import network
from machine import Pin
import neopixel
from umqtt.simple import MQTTClient
import sys

# === CONFIG ===
NUM_LEDS = 256
PIN_LED = 12
MQTT_BROKER = "broker.emqx.io"
MQTT_TOPIC = b"infinity/dashboard"
MQTT_TEST_TOPIC = b"infinity/test"
DEVICE_ID = b"infinity01"

# Module names
MODULE_NAME = "dashboard"
AVAILABLE_MODULES = ["clock", "equalizer", "weather", "dashboard"]

np = neopixel.NeoPixel(Pin(PIN_LED, Pin.OUT), NUM_LEDS)
BACKGROUND_COLOR = (0, 0, 0)
prev_matrix = [(0, 0, 0)] * NUM_LEDS
module_active = True  # Flag to control the main loop

# Couleurs
RED = (40, 0, 0)
BLUE = (0, 0, 40)
ORANGE = (40, 20, 0)

# Police 5x7 pixels (chiffres + lettres basiques + quelques symboles)
FONT_5x7 = {
    '0': ['01110',
          '10001',
          '10011',
          '10101',
          '11001',
          '10001',
          '01110'],
    '1': ['00100',
          '01100',
          '00100',
          '00100',
          '00100',
          '00100',
          '01110'],
    '2': ['01110',
          '10001',
          '00001',
          '00010',
          '00100',
          '01000',
          '11111'],
    '3': ['11110',
          '00001',
          '00001',
          '01110',
          '00001',
          '00001',
          '11110'],
    '4': ['00010',
          '00110',
          '01010',
          '10010',
          '11111',
          '00010',
          '00010'],
    '5': ['11111',
          '10000',
          '11110',
          '00001',
          '00001',
          '10001',
          '01110'],
    '6': ['00110',
          '01000',
          '10000',
          '11110',
          '10001',
          '10001',
          '01110'],
    '7': ['11111',
          '00001',
          '00010',
          '00100',
          '01000',
          '01000',
          '01000'],
    '8': ['01110',
          '10001',
          '10001',
          '01110',
          '10001',
          '10001',
          '01110'],
    '9': ['01110',
          '10001',
          '10001',
          '01111',
          '00001',
          '00010',
          '01100'],
    ':': ['00000',
          '00100',
          '00100',
          '00000',
          '00100',
          '00100',
          '00000'],
    '%': ['11000',
          '11001',
          '00010',
          '00100',
          '01000',
          '10011',
          '00011'],
    'C': ['01110',
          '10001',
          '10000',
          '10000',
          '10000',
          '10001',
          '01110'],
    'P': ['11110',
          '10001',
          '10001',
          '11110',
          '10000',
          '10000',
          '10000'],
    'U': ['10001',
          '10001',
          '10001',
          '10001',
          '10001',
          '10001',
          '01110'],
    'R': ['11110',
          '10001',
          '10001',
          '11110',
          '10100',
          '10010',
          '10001'],
    'A': ['01110',
          '10001',
          '10001',
          '11111',
          '10001',
          '10001',
          '10001'],
    'M': ['10001',
          '11011',
          '10101',
          '10001',
          '10001',
          '10001',
          '10001'],
    'G': ['01110',
          '10001',
          '10000',
          '10111',
          '10001',
          '10001',
          '01110'],
    'T': ['11111',
          '00100',
          '00100',
          '00100',
          '00100',
          '00100',
          '00100'],
    '°': ['00100',
          '01010',
          '00100',
          '00000',
          '00000',
          '00000',
          '00000'],
    ' ': ['00000',
          '00000',
          '00000',
          '00000',
          '00000',
          '00000',
          '00000'],
}

# === FONCTIONS LED ===

def clear():
    for i in range(NUM_LEDS):
        np[i] = BACKGROUND_COLOR
    np.write()

def set_pixel_16x16(x, y, color):
    if not (0 <= x < 16 and 0 <= y < 16):
        return
    if y < 8:
        matrice = 3 if x < 8 else 0
        x_local, y_local = (x, y) if x < 8 else (x - 8, y)
    else:
        matrice = 2 if x < 8 else 1
        x_local, y_local = (x, y - 8) if x < 8 else (x - 8, y - 8)

    index = y_local * 8 + (x_local if y_local % 2 == 0 else 7 - x_local)
    led_index = matrice * 64 + index
    np[led_index] = color

def build_colored_text_buffer(text_parts):
    total_length = sum(len(tp[0]) * 6 for tp in text_parts)  # 6 px par char
    buffer = [[BACKGROUND_COLOR for _ in range(total_length)] for _ in range(16)]

    x_offset = 0
    for text, color in text_parts:
        for i, char in enumerate(text):
            pattern = FONT_5x7.get(char.upper(), FONT_5x7[' '])
            for dy, row in enumerate(pattern):
                for dx, pixel in enumerate(row):
                    if pixel == '1':
                        x = x_offset + i * 6 + dx
                        y = dy + 4  # centrage vertical
                        if 0 <= x < total_length and 0 <= y < 16:
                            buffer[y][x] = color
        x_offset += len(text) * 6
    return buffer

def scroll_colored_text(buffer, delay=0.05, mqtt_client=None):
    global module_active
    width = len(buffer[0])
    # On inverse la boucle offset pour défiler de gauche à droite
    for offset in range(width - 16, -1, -1):  # Décrémente offset
        # Check MQTT messages before each frame
        if mqtt_client:
            try:
                mqtt_client.check_msg()
            except:
                pass
                
        if not module_active:  # Check if we should stop scrolling
            return
            
        for y in range(16):
            for x in range(16):
                pos = x + offset
                if pos < width:
                    color_pixel = buffer[y][width - 1 - pos]  # Miroir toujours actif
                else:
                    color_pixel = BACKGROUND_COLOR
                set_pixel_16x16(x, y, color_pixel)
        np.write()
        time.sleep(delay)


# === WIFI & MQTT ===

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connexion WiFi en cours...")
        wlan.connect(ssid, password)
        timeout = 10  # secondes max d'attente
        start = time.time()
        while not wlan.isconnected():
            if time.time() - start > timeout:
                print("⚠️ Échec connexion WiFi")
                return False
            time.sleep(0.5)
    print("✅ WiFi connecté :", wlan.ifconfig())
    return True

def handle_module_switch(new_module):
    """Handle switching to a new module"""
    if new_module in AVAILABLE_MODULES:
        print(f"Switching to module: {new_module}")
        # Clear the display before switching
        clear()
        np.write()
        
        # Import and run the new module
        try:
            if new_module == "clock":
                import clock
                clock.main()
            elif new_module == "equalizer":
                import equalizer
                equalizer.main()
            elif new_module == "weather":
                import weather
                weather.main()
            elif new_module == "dashboard":
                # We're already in the dashboard module
                pass
        except Exception as e:
            print(f"Error switching to module {new_module}:", e)
            # If there's an error, stay in the current module
            return False
    else:
        print(f"Unknown module: {new_module}")
    return True

def mqtt_callback(topic, msg):
    global current_text_buffer, module_active
    try:
        if topic == MQTT_TOPIC:
            data = json.loads(msg.decode())
            cpu = data.get("cpu", 0)
            ram = data.get("ram", 0)
            gpu = min(data.get("gpu_temp", 0), 100)

            text_parts = [
                (f"CPU:{cpu:.0f}% ", RED),
                (f"RAM:{ram:.0f}% ", BLUE),
                (f"GPU:{gpu:.0f}° ", ORANGE),
            ]
            current_text_buffer = build_colored_text_buffer(text_parts)
            print(f"Updated dashboard data - CPU: {cpu}%, RAM: {ram}%, GPU: {gpu}°")
        elif topic == MQTT_TEST_TOPIC:
            test_msg = msg.decode().lower()
            print(f"Received test message: {test_msg}")
            
            if test_msg == "clock":
                import clock
                module_active = False
                clock.module_active = True
                clock.main_loop(clock.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif test_msg == "equalizer":
                import equalizer
                module_active = False
                equalizer.module_active = True
                equalizer.main_loop(equalizer.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif test_msg == "weather":
                import weather
                module_active = False
                weather.module_active = True
                weather.main_loop(weather.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif test_msg == "dashboard":
                # We're already in the dashboard module
                pass
            elif test_msg == "clear":
                clear()
    except Exception as e:
        print("Error parsing MQTT message:", e)
        print(f"Topic: {topic}, Message: {msg.decode() if msg else 'None'}")
        current_text_buffer = None

def setup_mqtt(client_id, broker, callback):
    client = MQTTClient(client_id, broker)
    client.set_callback(callback)
    try:
        client.connect()
        client.subscribe(MQTT_TOPIC)
        client.subscribe(MQTT_TEST_TOPIC)
        print("📡 MQTT connected & subscribed to", MQTT_TOPIC, "and", MQTT_TEST_TOPIC)
        return client
    except Exception as e:
        print("⚠️ MQTT connection failed:", e)
        return None

def main_loop(client_id, ssid, password):
    global current_text_buffer, module_active
    client = None
    current_text_buffer = None

    while module_active:  # Use module_active flag instead of while True
        # Check and reconnect WiFi if needed
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            print("WiFi lost, attempting reconnection...")
            if not connect_wifi(ssid, password):
                time.sleep(1)
                continue

        # Check and reconnect MQTT if needed
        if client is None:
            client = setup_mqtt(client_id, MQTT_BROKER, mqtt_callback)
            if client is None:
                time.sleep(1)
                continue

        try:
            # Check for MQTT messages first
            client.check_msg()
            
            # Only proceed with display if module is still active
            if not module_active:
                break
                
            # Display current text buffer or default text
            if current_text_buffer:
                scroll_colored_text(current_text_buffer, mqtt_client=client)
            else:
                # Display default text if no data received yet
                text_parts = [
                    ("CPU:0% ", RED),
                    ("RAM:0% ", BLUE),
                    ("GPU:0° ", ORANGE),
                ]
                current_text_buffer = build_colored_text_buffer(text_parts)
                scroll_colored_text(current_text_buffer, mqtt_client=client)
            
            # Check MQTT messages again after display
            client.check_msg()
            
            # Small delay to prevent CPU overload
            time.sleep(0.02)
            
        except Exception as e:
            print("Error in main loop:", e)
            try:
                client.disconnect()
            except:
                pass
            client = None
            time.sleep(1)

def main():
    """Main function to run the dashboard module"""
    global module_active
    module_active = True  # Reset the flag when starting
    ssid = "iPhonenono"
    password = "nonolagrinta"
    if connect_wifi(ssid, password):
        main_loop(DEVICE_ID, ssid, password)
    else:
        print("Unable to connect to WiFi at startup.")
    clear()  # Clean up display when exiting
    print("Dashboard exited")

if __name__ == "__main__":
    main()

