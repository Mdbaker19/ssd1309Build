#include <U8g2lib.h>
#include <SPI.h>
#include <Arduino.h>
// https://github.com/olikraus/u8g2/wiki/u8g2reference#drawstr
#include <EEPROM.h>
// memory ^
#include <Wire.h>
#include <RTClib.h>
// real time clock for AFK
RTC_DS3231 rtc;

// 10, 8, 9, 51, 52, pwr, gnd
U8G2_SSD1309_128X64_NONAME0_1_4W_HW_SPI u1(U8G2_R0, 10, 8, 9);
U8G2_SSD1309_128X64_NONAME0_1_4W_HW_SPI u2(U8G2_R0, 5, 3, 4);


//charSprite
const unsigned char sprite [] PROGMEM = {
    0x00, 0x00, 0x00, 0x00, 0x06, 0xC0, 0xEC, 0x40, 0xB8, 0x7F, 0x18, 0x70, 0x0C, 0x40, 0x04, 0x40, 0x44, 0x48, 0x06, 0x40, 0x02, 0x20, 0x86, 0x27, 0xC4, 0x30, 0x08, 0x18, 0xF8, 0x0F, 0x00, 0x00
};

const unsigned char coinSprite [] PROGMEM = {
    0x00, 0x10, 0x18, 0x3C, 0x24, 0x22, 0x3E, 0x00
};


void setup() {
    Wire.begin();
    rtc.begin();
    u1.begin();
    u2.begin();

    Serial.begin(9600);

    EEPROM.get(0, totalSnowmanContacts);

    if (rtc.lostPower()){
        // Serial.println("LOST POWER< SETTING DATE");
        rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
        powerWasLostToRTC = true;
    }
}


struct Vect2 {
    float x;
    float y;
};

struct Player {
    float x;
    float y;
}

struct Coin {
    Vect2 pos;
    Vect2 satCoord[4];
    int id;
};

const int maxCoins = 5;
Coin coins[maxCoins];
int currentCoins = 0;

const int potPin = A0;
int potValue = 0;
int potPos = 0;

long totalSnowmanContacts = 0;
long coinsCollected = 0;

int snowmanX = 0;
int snowmanY = 15;
int ymove = 1;
int xmove = 1;


// Will affect AFK - display a message - TODO
bool powerWasLostToRTC = false;

void loop(void) {
    // get all calc'd to ms and do math on it for afk
    DateTime moment = rtc.now();

    u1.firstPage();
    do {
        u1.setFont(u8g2_font_unifont_t_symbols);
        u1.drawGlyph(x, y, 0x2603);

        bool contactedEdge = false;
        if (x >= 118) {
            xmove *= -1;
            totalSnowmanContacts++;
            contactedEdge = true;
        } else if (x <= -5) {
            xmove *= -1;
            totalSnowmanContacts++;
            contactedEdge = true;
        }
        if (y >= 64) {
            ymove *= -1;
            totalSnowmanContacts++;
            contactedEdge = true;
        } else if (y <= 10) {
            ymove *= -1;
            totalSnowmanContacts++;
            contactedEdge = true;
        }

        if (contactedEdge) {
            EEPROM.put(0, totalSnowmanContacts);
            contactedEdge = false;
        }

        u1.setFont(u8g2_font_ncenB08_tr);
        u1.drawStr(22, 8, String(totalSnowmanContacts).c_str());
        u1.drawStr(90, 8, String(coinsCollected).c_str());
    } while (u1.nextPage());



    u2.firstPage();

    int potSum = 0;
    for (int i = 0; i < 15; ++i) {
        potSum += analogRead(potPin);
        delay(8);
    }
    potValue = potSum / 10;
    potPos = map(potValue, 0, 1023, 0, 115);
    // pot position to move an arrow over button selections
    // u2.drawButtonUTF8(62, 20, U8G2_BTN_BW2, 0,  2,  2, "Btn" );

    spriteX = constrain(potPos, 1, 115);
    int spriteYVal = spriteY;
    if (spriteX <= 2) {
        spriteYVal += 3;
    }
    if (spriteX >= 112) {
        spriteYVal -= 3;
    }
    spriteY = constrain(spriteYVal, 0, 48);
    addCoin(2, (int)random(5, 58), (int)random(9, 111));
    addCoin(3, (int)random(3, 58), (int)random(9, 111));
    addCoin(4, (int)random(5, 57), (int)random(9, 111));
    addCoin(5, (int)random(3, 55), (int)random(9, 111));

    do {

        u2.setFont(u8g2_font_ncenB08_tr);
        for (int i = 0; i < currentCoins; ++i) {
            u2.drawXBMP(coins[i].pos.x, coins[i].pos.y, 8, 8, coinSprite);
        }
        u2.drawXBMP(spriteX, spriteY, 16, 16, sprite);
        Vect2 playerSpriteSAT[4];
        Vect2* playerCoords = getSpriteSATCoords(spriteX, spriteY, 16, 16);
        for (int p = 0; p < 4; ++p) {
            playerSpriteSAT[p] = playerCoords[p];
        }
        for (int i = 0; i < currentCoins; ++i) {
            if (checkCollision(playerSpriteSAT, 4, coins[i].satCoord, 4, 1.0)) {
                coinsCollected++;
            }
        }
        u2.drawStr(55, 8, String(spriteX).c_str());
    } while (u2.nextPage());

    delay(250);


}
