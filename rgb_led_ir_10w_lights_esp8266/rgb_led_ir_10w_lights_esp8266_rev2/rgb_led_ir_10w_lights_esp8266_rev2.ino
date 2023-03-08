// Author kot.dnz@gmail.com
// 20-Sep-2018
// revision 1.2
// Scetch updates according to the changes in the ver.1.2

// WiFi / MQTT section
#include <ESP8266WiFi.h>
// do not forget to edit PubSubClient.h 
// our packet is bigger than default 128 => should be 256
#include <PubSubClient.h>
#include <ArduinoJson.h>
// IR section
// pulse parameters in usec
#define NEC_BITS 32
#define HDR_MARK 9000
#define HDR_SPACE 4500
#define BIT_MARK 560
#define ONE_SPACE 1690
#define ZERO_SPACE 560
#define NEC_RPT_SPACE 0

#define TOPBIT 0x80000000

// check the wire!!!
//const int OutputPin = D5;   // RGB IR sensor 
const int OutputPin = D4;   // RGB IR sensor 
// from RGB we get 12v and via LM7805 transform it to the 5v to the Vin
// Gnd -> Gnd
 
const char* ssid = "KartingSystemV1";
const char* password =  "6jBwdfHrMgNvxe32JaMB";
const char* mqttServer = "172.20.20.1";

//const char* ssid = "My-home-TP-LINK";
//const char* password =  "kostya-secret";
//const char* mqttServer = "10.0.0.237";

const int   mqttPort = 1883;
const char* mqttUser = "point";
const char* mqttPassword = "mqtt";
const char* mqttTopic = "second";
unsigned long previousMillis = 0;        // will store last time LED was updated
const long interval = 1000;              // interval at which to blink (milliseconds)

unsigned int toggle = 0; 
unsigned long current_color = 0;  // current color

WiFiClient espClient;
PubSubClient client(espClient);
char payload[256];

void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("WiFi connected.");
  randomSeed(micros());
  // Serial.println(WiFi.localIP());
}


// https://github.com/alistairallan/RgbIrLed/pull/1/files
const unsigned long RGB_On  =    0b111111111011000001001111; // 0xFFB04F
const unsigned long RGB_Off =    0xFFF807;
const unsigned long RGB_Red =    0b111111111001100001100111; // 0xFF9867
const unsigned long RGB_Green  = 0b111111111101100000100111; // 0xFFD827
const unsigned long RGB_Blue   = 0xFF8877;
const unsigned long RGB_Orange = 0xFF02FD; 

void send(unsigned long data) {
  char buff[200];
  sprintf(buff, "%lu", data);
  //Serial.println(buff);

  mark(HDR_MARK);
  space(HDR_SPACE);

  for(unsigned long mask = 1UL << (NEC_BITS - 1); mask; mask >>= 1){
    if(data & mask){
      mark(BIT_MARK);
      space(ONE_SPACE);
    } else {
      mark(BIT_MARK);
      space(ZERO_SPACE);
    }
  }

  mark(BIT_MARK);
  space(NEC_RPT_SPACE);
}

void mark(int time) {
  digitalWrite(OutputPin, LOW);
  delayMicroseconds(time);
}

void space(int time) {
  digitalWrite(OutputPin, HIGH);
  delayMicroseconds(time);
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  pinMode(OutputPin, OUTPUT);
  digitalWrite(OutputPin, HIGH);
  RGB_tests();  
  setup_wifi();
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callback);
}

void callback(char* topic, byte* payload, unsigned int pLength) {
    //Serial.println("msg received");
    current_color = 0;

    char* msg = new char[pLength+1]();
    memcpy(msg, payload, pLength);
    //Serial.println(msg);

    // RED flag
    if(strcmp(msg, "RED") == 0){
      //Serial.println("Red");
      current_color = RGB_Red;
    }
    // Yellow flag
    if(strcmp(msg, "YELLOW") == 0){
      //Serial.println("Yellow");   
      current_color = RGB_Orange;
    }
    
    if(strcmp(msg, "GREEN")== 0){
      //Serial.println("Green");
      current_color = RGB_Green;
    }
    // our light remembered last color
    // so blink function looks like on/off
    if(current_color != 0) {
        send(RGB_On);
        delay(50);
        send(current_color);
    } else {
        send(RGB_Off);
        delay(50);
    }
}

void RGB_tests() {
  send(RGB_On);
  delay(50);      // must have
  send(RGB_Red);
  delay(500);
  send(RGB_Green);
  delay(500);
  send(RGB_Blue);
  delay(500);
  send(RGB_Orange);
  delay(500);
  send(RGB_Off);
  delay(50);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  } 
  client.loop();
    unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
    // save the last time you blinked the LED
    previousMillis = currentMillis;
    toggle ^= 1;
    digitalWrite(LED_BUILTIN, toggle);  
  }
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    //Serial.println("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str(),mqttUser, mqttPassword)) {
      //Serial.println("MQTT connected.");
      // Once connected, publish an announcement...
      //client.publish(mqttTopic, "hello MQTT, Light 10w connected");
      // ... and resubscribe
      client.subscribe(mqttTopic);
    } else {
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}
