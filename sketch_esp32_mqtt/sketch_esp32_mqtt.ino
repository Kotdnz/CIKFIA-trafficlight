#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
 
const char* ssid = "KartingSystemV1";
const char* password =  "6jBwdfHrMgNvxe32JaMB";
const char* mqttServer = "172.20.20.1";
//const char* ssid = "My-home-TP-LINK";
//const char* password =  "kostya-secret";
//const char* mqttServer = "10.0.0.237";
const int   mqttPort = 1883;
const char* mqttUser = "point";
const char* mqttPassword = "mqtt";
const char* mqttTopic = "cloud";
bool mGREEN = false;
bool mYELLOW = false;
bool mRED = false;
int toggle = 0;

unsigned long previousMillis = 0;        // will store last time LED was updated
const long interval = 700;           // interval at which to blink (milliseconds)
 
WiFiClient espClient;
PubSubClient client(espClient);
char payload[1024];

#include <Adafruit_GFX.h>    // Core graphics library
#include <Adafruit_ST7735.h> // Hardware-specific library
#include <SPI.h>

// For the breakout, you can use any 2 or 3 pins
// These pins will also work for the 1.8" TFT shield
#define TFT_CS 16
#define TFT_RST 9  // you can also connect this to the Arduino reset
                      // in which case, set this #define pin to -1!
#define TFT_DC 17

// Option 1 (recommended): must use the hardware SPI pins
// (for UNO thats sclk = 13 and sid = 11) and pin 10 must be
// an output. This is much faster - also required if you want
// to use the microSD card (see the image drawing example)
//Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS,  TFT_DC, TFT_RST);

// Option 2: use any pins but a little slower!
#define TFT_SCLK 5   // set these to be whatever pins you like!
#define TFT_MOSI 23   // set these to be whatever pins you like!
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_MOSI, TFT_SCLK, TFT_RST);

void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    tft.print(".");
  }

  tft.println("WiFi connected.");
  randomSeed(micros());
  // Serial.println(WiFi.localIP());
}
 
void setup() {

  // Use this initializer if you're using a 1.8" TFT
  tft.initR(INITR_BLACKTAB);   // initialize a ST7735S chip, black tab
  tft.fillScreen(ST7735_BLACK);
  
  setup_wifi();
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callback); 
}
 
void callback(char* topic, byte* payload, unsigned int pLength) {
    //Serial.println("msg received");
    StaticJsonBuffer<200> jsonBuffer;

    char* msg = new char[pLength+1]();
    memcpy(msg, payload, pLength);
    //Serial.println(msg);
    JsonObject& root = jsonBuffer.parseObject(msg);
    if (!root.success())
    {
      tft.println("Parsing failed");
      delete msg;
      return;
    }
    mRED = mYELLOW = mGREEN = false;
    if (root.containsKey("RED")){
            if(root["RED"] == "ON") { 
              mRED = true;
              return;
            }
    }
    if (root.containsKey("YELLOW")){
            if(root["YELLOW"] == "ON") {
              mYELLOW = true;
              return;
            }
    }
    if (root.containsKey("GREEN")){
            if(root["GREEN"] == "ON") {
              mGREEN = true;
              return;
            }
    }
    if (root.containsKey("OFF"))
            if(root["OFF"] == "ON") 
              tft.fillScreen(ST7735_BLACK);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  } 
  client.loop();
    unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
    // save the last time you blinked
    previousMillis = currentMillis;
    toggle ^= 1;
    if(toggle){
      if(mRED) tft.fillScreen(ST7735_RED);
      if(mYELLOW) tft.fillScreen(ST7735_YELLOW);
      if(mGREEN) tft.fillScreen(ST7735_GREEN);
    } else tft.fillScreen(ST7735_BLACK);
  }
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    tft.println("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str(),mqttUser, mqttPassword)) {
      tft.println("MQTT connected.");
      // Once connected, publish an announcement...
      // client.publish(mqttTopic, "hello MQTT");
      // ... and resubscribe
      client.subscribe(mqttTopic);
    } else {
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}
