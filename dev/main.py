import network
import time
from machine import Pin
import neopixel
from umqtt.simple import MQTTClient

# === Configuration Wi-Fi ===
SSID = 'iPhonenono'
PASSWORD = 'nonolagrinta'

# === MQTT ===
BROKER = 'broker.emqx.io'
TOPIC = b'infinity/test'

# === LED ===
NUM_LEDS = 256
PIN_LED = 12  # GPIO 5 (D5)

np = neopixel.NeoPixel(Pin(PIN_LED, Pin.OUT), NUM_LEDS)

# === Icônes ===
EQUALIZER = [
    [0,0,1,0,0],
    [0,1,1,1,0],
    [0,1,1,1,0],
    [1,1,1,1,1],
    [1,0,1,0,1]
]
DASHBOARD = [
    [0,0,1,0,0],
    [0,1,1,0,0],
    [1,1,1,1,0],
    [1,0,1,1,1],
    [1,1,1,1,1]
]
CLOCK = [
    [0,1,1,1,0],
    [1,0,1,0,1],
    [1,1,1,1,1],
    [1,0,1,0,1],
    [0,1,1,1,0]
]
METEO = [
    [0,1,1,1,0],
    [1,1,1,1,1],
    [0,0,0,0,0],
    [0,1,0,1,0],
    [1,0,1,0,1]
]

WHITE = (40, 40, 40)
BLUE = (0, 0, 40)
YELLOW = (40, 40, 0)

# === Outils LED ===
def clear():
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0)
    np.write()

def set_pixel(matrice_index, x, y, color):
    base = matrice_index * 64
    pos = y * 8 + x
    np[base + pos] = color

def draw_icon(matrice_index, pattern, color):
    for y in range(5):
        for x in range(5):
            if pattern[y][x]:
                set_pixel(matrice_index, x+1, y+1, color)
    np.write()

# === Modules à lancer ===
def module_equalizer():
    print("🎚️ Equalizer lancé")
    clear()
    draw_icon(0, EQUALIZER, YELLOW)

def module_dashboard():
    print("📊 Dashboard lancé")
    clear()
    draw_icon(1, DASHBOARD, BLUE)

def module_horloge():
    print("⏰ Horloge lancée")
    clear()
    draw_icon(2, CLOCK, WHITE)

def module_meteo():
    print("🌦️ Météo lancée")
    clear()
    draw_icon(3, METEO, WHITE)

MODULES = {
    "equalizer": module_equalizer,
    "dashboard": module_dashboard,
    "horloge": module_horloge,
    "meteo": module_meteo
}

# === Callback MQTT ===
def mqtt_cb(topic, msg):
    payload = msg.decode().lower()
    print(f"📩 Message MQTT reçu : {payload}")
    if payload in MODULES:
        MODULES[payload]()

# === Fonction principale ===
def main():
    # Connexion Wi-Fi
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(SSID, PASSWORD)
    print("🔌 Connexion Wi-Fi...")
    while not wifi.isconnected():
        time.sleep(0.3)
    print("✅ Connecté au Wi-Fi :", wifi.ifconfig())

    # MQTT
    client = MQTTClient("esp32client", BROKER)
    client.set_callback(mqtt_cb)
    client.connect()
    client.subscribe(TOPIC)
    print(f"📡 Connecté MQTT, abonné à {TOPIC.decode()}")

    # LED : affichage initial des icônes
    clear()
    draw_icon(0, EQUALIZER, YELLOW)
    draw_icon(1, DASHBOARD, BLUE)
    draw_icon(2, CLOCK, WHITE)
    draw_icon(3, METEO, WHITE)
    print("✨ Icônes affichées")

    # Boucle principale
    print("🔄 En attente de messages MQTT...")
    while True:
        client.check_msg()
        time.sleep(0.1)

# === Lancer le programme ===
main()
