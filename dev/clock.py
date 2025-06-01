import time
import network
from machine import Pin, RTC
import neopixel
from umqtt.simple import MQTTClient
import json
import sys

# === CONFIG ===
TOTAL_LEDS = 256
PIN_LED = 12
MQTT_BROKER = "broker.emqx.io"
MQTT_TOPIC = b"infinity/clock"
MQTT_TEST_TOPIC = b"infinity/test"
DEVICE_ID = b"clock01"

# Module names
MODULE_NAME = "clock"
AVAILABLE_MODULES = ["clock", "equalizer", "weather", "dashboard"]

np = neopixel.NeoPixel(Pin(PIN_LED, Pin.OUT), TOTAL_LEDS)
BACKGROUND_COLOR = (0, 0, 0)

# Default colors
DEFAULT_COLOR = (40, 40, 40)  # White
current_color = DEFAULT_COLOR
module_active = True  # Flag to control the main loop

# Colors
WHITE = (40, 40, 40)
BLUE = (0, 0, 40)
YELLOW = (40, 40, 0)
RED = (40, 0, 0)
ORANGE = (40, 20, 0)
GREEN = (0, 40, 0)
PURPLE = (20, 0, 40)

# Color mapping
COLOR_MAP = {
    "white": WHITE,
    "blue": BLUE,
    "yellow": YELLOW,
    "red": RED,
    "orange": ORANGE,
    "green": GREEN,
    "purple": PURPLE
}

# Font for display (8x8 pixels)
FONT = {
    '0': ['00111100',
          '01100110',
          '11000011',
          '11000011',
          '11000011',
          '11000011',
          '01100110',
          '00111100'],
    '1': ['00011000',
          '00111000',
          '00011000',
          '00011000',
          '00011000',
          '00011000',
          '00011000',
          '01111110'],
    '2': ['00111100',
          '01100110',
          '11000011',
          '00000110',
          '00001100',
          '00011000',
          '00110000',
          '11111111'],
    '3': ['00111100',
          '01100110',
          '11000011',
          '00011100',
          '00000110',
          '11000011',
          '01100110',
          '00111100'],
    '4': ['00000110',
          '00001110',
          '00011110',
          '00110110',
          '01100110',
          '11111111',
          '00000110',
          '00000110'],
    '5': ['11111111',
          '11000000',
          '11111100',
          '00000110',
          '00000011',
          '11000011',
          '01100110',
          '00111100'],
    '6': ['00111100',
          '01100110',
          '11000000',
          '11111100',
          '11000011',
          '11000011',
          '01100110',
          '00111100'],
    '7': ['11111111',
          '00000011',
          '00000110',
          '00001100',
          '00011000',
          '00110000',
          '00110000',
          '00110000'],
    '8': ['00111100',
          '01100110',
          '11000011',
          '01100110',
          '00111100',
          '11000011',
          '01100110',
          '00111100'],
    '9': ['00111100',
          '01100110',
          '11000011',
          '11000011',
          '01111110',
          '00000011',
          '01100110',
          '00111100']
}

def clear():
    for i in range(TOTAL_LEDS):
        np[i] = BACKGROUND_COLOR
    np.write()

def set_pixel_16x16(x, y, color):
    if not (0 <= x < 16 and 0 <= y < 16):
        return
    if y < 8:
        matrice = 1 if x < 8 else 2
        x_local, y_local = (x, y) if x < 8 else (x - 8, y)
    else:
        matrice = 0 if x < 8 else 3
        x_local, y_local = (x, y - 8) if x < 8 else (x - 8, y - 8)

    index = y_local * 8 + (x_local if y_local % 2 == 0 else 7 - x_local)
    led_index = matrice * 64 + index
    np[led_index] = color

def draw_char(char, x, y, color):
    """Draw a single character at the specified position"""
    if char not in FONT:
        return
    
    pattern = FONT[char]
    for dy, row in enumerate(pattern):
        for dx, pixel in enumerate(row):
            if pixel == '1':
                # Mirror effect for x coordinate
                set_pixel_16x16(15 - (x + dx), y + dy, color)

def draw_digit(digit, matrix, color):
    """Draw a digit centered in the specified matrix (0-3)"""
    if not (0 <= matrix <= 3):
        return
        
    # Calculate base position for the matrix
    base_x = 8 if matrix in [2, 3] else 0
    base_y = 8 if matrix in [0, 3] else 0
    
    # Center the digit in the matrix (8x8 font)
    x = base_x + 0  # Start from the left edge since we're using full width
    y = base_y + 0  # Start from the top since we're using full height
    
    draw_char(digit, x, y, color)
    np.write()

def display_time():
    """Display current time on the matrices"""
    # Get current time
    current_time = time.localtime()
    hours = current_time[3]
    minutes = current_time[4]
    
    # Format time as HH:MM
    time_str = f"{hours:02d}{minutes:02d}"
    
    # Clear display
    clear()
    
    # Draw each digit in its own matrix
    # Matrix order: [0][3]  Hours
    #              [1][2]  Minutes
    matrix_map = {
        0: 3,  # First digit of hours goes to matrix 0 (top left)
        1: 0,  # Second digit of hours goes to matrix 3 (top right)
        2: 2,  # First digit of minutes goes to matrix 1 (bottom left)
        3: 1   # Second digit of minutes goes to matrix 2 (bottom right)
    }
    
    for i, digit in enumerate(time_str):
        matrix = matrix_map[i]
        draw_digit(digit, matrix, current_color)
    np.write()

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(ssid, password)
        timeout = 10
        start = time.time()
        while not wlan.isconnected():
            if time.time() - start > timeout:
                print("⚠️ WiFi connection failed")
                return False
            time.sleep(0.5)
    print("✅ WiFi connected:", wlan.ifconfig())
    return True

def handle_module_switch(new_module):
    """Handle switching to a new module"""
    global module_active
    if new_module in AVAILABLE_MODULES:
        print(f"Switching to module: {new_module}")
        # Clear the display before switching
        clear()
        np.write()
        
        # Import and run the new module
        try:
            if new_module == "equalizer":
                import equalizer
                module_active = False  # Exit current module
                equalizer.module_active = True
                equalizer.main_loop(equalizer.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif new_module == "weather":
                import weather
                module_active = False  # Exit current module
                weather.module_active = True
                weather.main_loop(weather.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif new_module == "dashboard":
                import dashboard
                module_active = False  # Exit current module
                dashboard.module_active = True
                dashboard.main_loop(dashboard.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif new_module == "clock":
                # We're already in the clock module
                pass
        except Exception as e:
            print(f"Error switching to module {new_module}:", e)
            # If there's an error, stay in the current module
            display_time()
    else:
        print(f"Unknown module: {new_module}")
    return True

def mqtt_callback(topic, msg):
    global current_color, module_active
    try:
        if topic == MQTT_TOPIC:
            color_msg = msg.decode().lower()
            if color_msg in COLOR_MAP:
                current_color = COLOR_MAP[color_msg]
                print(f"Color changed to: {color_msg}")
                display_time()  # Update display with new color
        elif topic == MQTT_TEST_TOPIC:
            test_msg = msg.decode().lower()
            print(f"Received test message: {test_msg}")
            
            if test_msg == "equalizer":
                import equalizer
                module_active = False
                equalizer.module_active = True
                equalizer.main_loop(equalizer.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif test_msg == "dashboard":
                import dashboard
                module_active = False
                dashboard.module_active = True
                dashboard.main_loop(dashboard.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif test_msg == "weather":
                import weather
                module_active = False
                weather.module_active = True
                weather.main_loop(weather.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif test_msg == "clock":
                # We're already in the clock module
                pass
            elif test_msg == "clear":
                clear()
    except Exception as e:
        print(f"Error in MQTT callback: {e}")
        print(f"Topic: {topic}, Message: {msg.decode() if msg else 'None'}")

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
    client = None
    last_minute = -1  # Initialize to -1 to ensure first update
    
    while True:
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
            # Get current minute
            current_minute = time.localtime()[4]
            
            # Update display only when minute changes
            if current_minute != last_minute:
                display_time()
                last_minute = current_minute
            
            # Check for MQTT messages
            client.check_msg()
            time.sleep(0.1)
        except Exception as e:
            print("Error in main loop:", e)
            try:
                client.disconnect()
            except:
                pass
            client = None
            time.sleep(1)

def main():
    """Main function to run the clock module"""
    global module_active
    module_active = True  # Reset the flag when starting
    connect_wifi("iPhonenono", "nonolagrinta")
    mqtt_client = setup_mqtt(DEVICE_ID, MQTT_BROKER, mqtt_callback)
    main_loop(DEVICE_ID, "iPhonenono", "nonolagrinta")
    clear()  # Clean up display when exiting
    print("Clock exited")

if __name__ == "__main__":
    main() 