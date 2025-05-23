import network
import time
from machine import Pin
import neopixel
from umqtt.simple import MQTTClient
from dev.equalizer import main_loop

# === Configuration Wi-Fi ===
SSID = 'iPhonenono'
PASSWORD = 'nonolagrinta'

# === MQTT ===
BROKER = 'broker.emqx.io'
TOPIC = b'infinity/test'

# === LED ===
NUM_LEDS = 256
PIN_LED = 12  

np = neopixel.NeoPixel(Pin(PIN_LED, Pin.OUT), NUM_LEDS)

WHITE = (40, 40, 40)
BLUE = (0, 0, 40)
NONE = (0, 0, 0)
YELLOW = (40, 40, 0)
RED = (40, 0, 0)
PINK = (40, 0, 20)
GREEN = (0,40,0)
PURPLE = (20, 0, 40)
CYAN   = (0, 40, 40)
ORANGE = (40, 20, 0)

# === Icônes ===
EQUALIZER = [
    [0,0,1,0,0,0,0,0],#inver
    [0,1,0,0,0,1,0,0],
    [0,1,1,1,0,0,1,0],#inver
    [0,1,1,0,1,1,1,1],
    [1,1,1,1,0,1,1,0],#inver
    [1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1],#inver
    [1,1,1,1,1,1,1,1]
]

EQUALIZER_COLORS = [
    [PINK,PURPLE,BLUE,CYAN,GREEN,YELLOW,ORANGE,RED],
    [RED,ORANGE,YELLOW,GREEN,CYAN,BLUE,PURPLE,PINK],
    [PINK,PURPLE,BLUE,CYAN,GREEN,YELLOW,ORANGE,RED],
    [RED,ORANGE,YELLOW,GREEN,CYAN,BLUE,PURPLE,PINK],
    [PINK,PURPLE,BLUE,CYAN,GREEN,YELLOW,ORANGE,RED],
    [RED,ORANGE,YELLOW,GREEN,CYAN,BLUE,PURPLE,PINK],
    [PINK,PURPLE,BLUE,CYAN,GREEN,YELLOW,ORANGE,RED],
    [RED,ORANGE,YELLOW,GREEN,CYAN,BLUE,PURPLE,PINK],
]

DASHBOARD = [
    [1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,1],
    [1,0,0,0,0,1,1,1],
    [1,1,1,0,0,1,1,1],
    [1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1]
]

DASHBOARD_COLORS = [
    [WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE],
    [WHITE,WHITE,WHITE,RED,RED,WHITE,WHITE,WHITE],
    [WHITE,GREEN,GREEN,RED,RED,GREEN,GREEN,WHITE],
    [WHITE,GREEN,GREEN,RED,RED,PURPLE,PURPLE,WHITE],
    [WHITE,PURPLE,PURPLE,ORANGE,ORANGE,GREEN,GREEN,WHITE],
    [WHITE,GREEN,GREEN,ORANGE,ORANGE,PURPLE,PURPLE,WHITE],
    [WHITE,PURPLE,PURPLE,ORANGE,ORANGE,GREEN,GREEN,WHITE],
    [WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE],
]

CLOCK = [
    [0,0,1,1,1,1,0,0],
    [0,1,0,0,0,0,1,0],
    [1,0,0,1,0,0,0,1],
    [1,0,0,0,1,0,0,1],
    [1,0,0,1,1,1,0,1],
    [1,0,0,0,0,0,0,1],
    [0,1,0,0,0,0,1,0],
    [0,0,1,1,1,1,0,0]
]

CLOCK_COLORS = [
    [WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE],
    [WHITE,WHITE,WHITE,RED,RED,WHITE,WHITE,WHITE],
    [WHITE,WHITE,WHITE,RED,RED,RED,WHITE,WHITE],
    [WHITE,WHITE,RED,RED,RED,RED,WHITE,WHITE],
    [WHITE,WHITE,RED,RED,RED,RED,WHITE,WHITE],
    [WHITE,WHITE,WHITE,RED,RED,WHITE,WHITE,WHITE],
    [WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE],
    [WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE],
]

METEO = [
    [0,0,0,1,1,0,0,0],  # blanc
    [0,0,1,1,1,1,0,0],  # blanc
    [0,1,1,1,1,1,1,0],  # blanc
    [1,1,1,1,1,1,1,1],  # blanc
    [0,0,0,0,0,0,0,0],  # rien
    [0,1,0,1,0,1,0,0],  # pluie
    [0,1,0,1,0,1,0,0],  # pluie attention ligne inversée
    [0,0,0,1,0,1,0,1]   # pluie
]

METEO_COLORS = [
    [NONE,NONE,NONE,WHITE,WHITE,NONE,NONE,NONE],
    [NONE,NONE,WHITE,WHITE,WHITE,WHITE,NONE,NONE],
    [NONE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,NONE],
    [WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE,WHITE],
    [NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE],
    [NONE,BLUE,NONE,BLUE,NONE,BLUE,NONE,NONE],
    [BLUE,BLUE,BLUE,BLUE,BLUE,BLUE,BLUE,BLUE],
    [NONE,NONE,NONE,BLUE,NONE,BLUE,NONE,BLUE]
]

# === Outils LED ===
def clear():
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0)
    np.write()

def set_pixel(matrice_index, x, y, color):
    base = matrice_index * 64
    pos = y * 8 + x
    np[base + pos] = color

def draw_icon_color(matrice_index, pattern, colors):
    for y in range(8):
        for x in range(8):
            if pattern[y][x]:
                set_pixel(matrice_index, x, y, colors[y][x])
    np.write()


# === Modules à lancer ===
def module_equalizer():
    print("🎚️ Equalizer lancé")
    clear()
    main_loop()

def module_dashboard():
    print("📊 Dashboard lancé")
    clear()
    draw_icon(1, DASHBOARD, BLUE)

def module_horloge():
    print("⏰ Horloge lancée")
    clear()
    draw_icon(2, CLOCK, BLUE)

def module_meteo():
    print("🌦️ Météo lancée")
    clear()
    draw_icon_color(3, METEO, METEO_COLORS)

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
    draw_icon_color(0, EQUALIZER, EQUALIZER_COLORS)
    draw_icon_color(1, DASHBOARD, DASHBOARD_COLORS)
    draw_icon_color(2, CLOCK, CLOCK_COLORS)
    draw_icon_color(3, METEO, METEO_COLORS)
    print("✨ Icônes affichées")

    # Boucle principale
    print("🔄 En attente de messages MQTT...")
    while True:
        client.check_msg()
        time.sleep(0.1)

# === Lancer le programme ===
main()
