import time
import json
import network
from machine import Pin
import neopixel
from umqtt.simple import MQTTClient
import sys

# === CONFIG ===
TOTAL_LEDS = 256
PIN_LED = 12
MQTT_BROKER = "broker.emqx.io"
MQTT_TOPIC = b"infinity/meteo"
MQTT_TEST_TOPIC = b"infinity/test"
DEVICE_ID = b"weather01"

# Module names
MODULE_NAME = "weather"
AVAILABLE_MODULES = ["clock", "equalizer", "weather", "dashboard"]

np = neopixel.NeoPixel(Pin(PIN_LED, Pin.OUT), TOTAL_LEDS)
BACKGROUND_COLOR = (0, 0, 0)
module_active = True  # Flag to control the main loop

# Colors
WHITE = (40, 40, 40)
BLUE = (0, 0, 40)
YELLOW = (40, 40, 0)
RED = (40, 0, 0)
ORANGE = (40, 20, 0)
GREEN = (0, 40, 0)
PURPLE = (20, 0, 40)

# Weather icons
SUN = [
    [0,0,1,1,1,0,0],
    [0,1,1,1,1,1,0],
    [1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1],
    [0,1,1,1,1,1,0],
    [0,0,1,1,1,0,0]
]

CLOUD = [
    [0,0,1,1,1,0,0],
    [0,1,1,1,1,1,0],
    [1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1],
    [0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0]
]

RAIN = [
    [0,0,1,1,0,0,0],
    [0,1,1,1,1,0,0],
    [1,1,1,1,1,1,0],
    [1,1,1,1,1,1,1],
    [0,1,0,1,0,1,0],
    [0,1,0,1,0,1,0],
    [0,1,0,1,0,1,0]
]

# Font for display (3x5 pixels)
FONT = {
    '0': ['010',
          '101',
          '101',
          '101',
          '010'],
    '1': ['01',
          '11',
          '01',
          '01',
          '11'],
    '2': ['110',
          '001',
          '010',
          '100',
          '111'],
    '3': ['110',
          '001',
          '110',
          '001',
          '110'],
    '4': ['101',
          '101',
          '111',
          '001',
          '001'],
    '5': ['111',
          '100',
          '110',
          '001',
          '110'],
    '6': ['110',
          '100',
          '110',
          '101',
          '110'],
    '7': ['111',
          '001',
          '010',
          '100',
          '100'],
    '8': ['010',
          '101',
          '010',
          '101',
          '010'],
    '9': ['110',
          '101',
          '111',
          '001',
          '110'],
    ':': ['0',
          '1',
          '0',
          '1',
          '0'],
    '%': ['1001',
          '0010',
          '0100',
          '0100',
          '1001'],
    '°': ['010',
          '101',
          '010',
          '000',
          '000'],
    'C': ['011',
          '100',
          '100',
          '100',
          '011'],
    ' ': ['000',
          '000',
          '000',
          '000',
          '000']
}

def clear():
    for i in range(TOTAL_LEDS):
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

def draw_text(text, x, y, color, is_time=False):
    """Draw text at the specified position"""
    current_x = x
    if is_time:
        current_x += 1  # Shift time one pixel right
    
    for i, char in enumerate(text):
        if char == ':':
            # Special handling for colon - use 1 pixel width with 1 pixel spacing
            draw_char(char, current_x, y, color)
            current_x += 2  # 1 for the colon + 1 space on each side
        elif char == '1':
            # Special handling for number 1 - use 2 pixel width
            draw_char(char, current_x, y, color)
            current_x += 3  # 2 for the number + 1 space
        else:
            draw_char(char, current_x, y, color)
            current_x += 4  # Normal character width
    np.write()

def draw_icon(icon_matrix, x, y, color):
    """Draw an icon at the specified position"""
    for dy, row in enumerate(icon_matrix):
        for dx, pixel in enumerate(row):
            if pixel:
                # Mirror effect for x coordinate
                set_pixel_16x16(15 - (x + dx), y + dy, color)
    np.write()

def format_time(timestamp):
    """Convert Unix timestamp to HH:MM"""
    hours = (timestamp % 86400) // 3600
    minutes = (timestamp % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"

def display_weather_data(data, mqtt_client):
    """Display weather data on the 2x2 matrix display"""
    global module_active
    # Extract data
    temp = data.get('temp', 0)
    humidity = data.get('humidity', 0)
    sunrise = data.get('sunrise', 0)
    sunset = data.get('sunset', 0)
    
    # Create display lines with icon
    lines = []
    
    # Add weather icon
    if temp > 20:
        lines.append((SUN, YELLOW, True, False))  # Added is_time parameter
    elif temp > 15:
        lines.append((CLOUD, WHITE, True, False))
    else:
        lines.append((RAIN, BLUE, True, False))
    
    # Add text lines with extra spacing after icon
    lines.extend([
        (f"{temp}°C", ORANGE, False, False),
        (f"{humidity}%", BLUE, False, False),
        (format_time(sunrise), YELLOW, False, True),
        (format_time(sunset), PURPLE, False, True)
    ])
    
    # Calculate total width for each line
    def calculate_text_width(text, is_time=False):
        width = 0
        if is_time:
            width += 1  # Add one pixel for time shift
        for char in text:
            if char == ':':
                width += 2  # 1 for colon + 1 space
            elif char == '1':
                width += 3  # 2 for number + 1 space
            else:
                width += 4  # Normal character width
        return width
    
    # Scroll the lines vertically
    offset = 0
    while module_active:  # Use module_active flag to control the loop
        # Check for new MQTT message before each frame
        try:
            if mqtt_client:
                mqtt_client.check_msg()
        except Exception as e:
            print("Error checking MQTT message:", e)
            
        clear()
        
        # Draw all lines
        for i, (content, color, is_icon, is_time) in enumerate(lines):
            # Calculate y position with offset
            if i == 0:  # Icon
                y_pos = i * 6 - offset
            else:  # Text lines with extra spacing after icon
                y_pos = i * 6 - offset + 2  # Add 2 pixels extra spacing after icon
            
            if is_icon:
                # Center icon horizontally
                x_pos = (16 - len(content[0])) // 2
                draw_icon(content, x_pos, y_pos, color)
            else:
                # Center text horizontally with special colon handling
                text_width = calculate_text_width(content, is_time)
                x_pos = (16 - text_width) // 2
                draw_text(content, x_pos, y_pos, color, is_time)
        
        # Update offset for next frame
        offset = (offset + 1) % 48
        time.sleep(0.2)  # Faster frame rate for smoother scrolling

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
            if new_module == "clock":
                import clock
                module_active = False  # Exit current module
                clock.module_active = True
                clock.main_loop(clock.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif new_module == "equalizer":
                import equalizer
                module_active = False  # Exit current module
                equalizer.module_active = True
                equalizer.main_loop(equalizer.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif new_module == "dashboard":
                import dashboard
                module_active = False  # Exit current module
                dashboard.module_active = True
                dashboard.main_loop(dashboard.DEVICE_ID, "iPhonenono", "nonolagrinta")
            elif new_module == "weather":
                # We're already in the weather module
                pass
        except Exception as e:
            print(f"Error switching to module {new_module}:", e)
            # If there's an error, stay in the current module
            return False
    else:
        print(f"Unknown module: {new_module}")
    return True

def mqtt_callback(topic, msg):
    try:
        if topic == MQTT_TOPIC:
            data = json.loads(msg.decode())
            # Store the data globally
            global current_weather_data
            current_weather_data = data
        elif topic == MQTT_TEST_TOPIC:
            test_msg = msg.decode().lower()
            print(f"Received test message: {test_msg}")
            if test_msg in AVAILABLE_MODULES:
                if handle_module_switch(test_msg):
                    module_active = False  # Exit the main loop only if switch was successful
            elif test_msg == "clear":
                clear()
    except Exception as e:
        print(f"Error in MQTT callback: {e}")
        print(f"Topic: {topic}, Message: {msg.decode() if msg else 'None'}")

# Global variable to store current weather data
current_weather_data = None

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
    global current_weather_data, module_active
    client = None
    
    while module_active:  # Use module_active flag to control the loop
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
            client.check_msg()
            # Display current weather data if available
            if current_weather_data:
                display_weather_data(current_weather_data, client)
            time.sleep(0.02)  # Reduced from 0.05 to 0.02 for faster response
        except Exception as e:
            print("Error in main loop:", e)
            try:
                client.disconnect()
            except:
                pass
            client = None
            time.sleep(1)

def main():
    """Main function to run the weather module"""
    global module_active
    module_active = True  # Reset the flag when starting
    connect_wifi("iPhonenono", "nonolagrinta")
    mqtt_client = setup_mqtt(DEVICE_ID, MQTT_BROKER, mqtt_callback)
    main_loop(DEVICE_ID, "iPhonenono", "nonolagrinta")
    clear()  # Clean up display when exiting
    print("Weather exited")

if __name__ == "__main__":
    main() 