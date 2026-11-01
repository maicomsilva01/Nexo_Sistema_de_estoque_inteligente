#include <SPI.h>
#include <Wire.h>
#include <MFRC522.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// RC522 mantém os pinos originais do projeto.
constexpr uint8_t RFID_SS_PIN = 5;
constexpr uint8_t RFID_RST_PIN = 22;

// I2C do OLED usa pinos livres; GPIO 22 continua dedicado ao RST do RC522.
constexpr uint8_t OLED_SDA_PIN = 21;
constexpr uint8_t OLED_SCL_PIN = 17;
constexpr uint8_t OLED_I2C_ADDRESS = 0x3C;
constexpr int OLED_WIDTH = 128;
constexpr int OLED_HEIGHT = 64;
constexpr int OLED_RESET_PIN = -1;

MFRC522 reader(RFID_SS_PIN, RFID_RST_PIN);
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, OLED_RESET_PIN);
bool displayReady = false;

void renderDisplay(const char* status, const String& detail) {
  if (!displayReady) return;

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setTextWrap(false);
  display.setCursor(0, 0);
  display.print("NEXO ESTOQUE");
  display.drawFastHLine(0, 12, OLED_WIDTH, SSD1306_WHITE);
  display.setCursor(0, 22);
  display.print(status);
  display.setCursor(0, 42);
  display.print(detail);
  display.display();
}

void setup() {
  Serial.begin(115200);

  SPI.begin(18, 19, 23, RFID_SS_PIN);
  reader.PCD_Init();

  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
  displayReady = display.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDRESS);

  Serial.println("Nexo Estoque - leitor RC522 pronto");
  Serial.println("Aproxime uma tag para ler a UID e cadastrá-la no produto.");

  if (displayReady) {
    renderDisplay("LEITOR PRONTO", "Aproxime uma tag");
  } else {
    Serial.println("OLED indisponivel; leitura RFID continua pelo Serial Monitor.");
  }
}

void loop() {
  if (!reader.PICC_IsNewCardPresent() || !reader.PICC_ReadCardSerial()) {
    delay(40);
    return;
  }

  String uid;
  for (byte index = 0; index < reader.uid.size; index++) {
    if (reader.uid.uidByte[index] < 0x10) uid += '0';
    uid += String(reader.uid.uidByte[index], HEX);
  }
  uid.toUpperCase();

  Serial.print("RFID_UID=");
  Serial.println(uid);
  Serial.println("Copie a UID para Movimentacoes > Leitura de tag RFID.");
  renderDisplay("TAG DETECTADA", String("UID: ") + uid);

  reader.PICC_HaltA();
  reader.PCD_StopCrypto1();
  delay(1600);

  renderDisplay("LEITOR PRONTO", "Aproxime uma tag");
}
