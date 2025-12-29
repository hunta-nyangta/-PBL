#include <Wire.h>
#include <BH1750.h>

const int PIN_ZC  = 2;
const int PIN_PSM = 9;
const uint16_t MAX_DELAY_US = 7000;
const uint16_t MIN_DELAY_US = 1000;

volatile uint16_t fireDelayUs = MAX_DELAY_US;
volatile bool isOff = true;
BH1750 lightMeter;

void onZeroCross() {
  if (isOff) return;
  delayMicroseconds(fireDelayUs);
  digitalWrite(PIN_PSM, HIGH);
  delayMicroseconds(20); 
  digitalWrite(PIN_PSM, LOW);
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println(F("PSM_Level,Lux")); 
  } else {
    while(1); 
  }
  pinMode(PIN_PSM, OUTPUT);
  pinMode(PIN_ZC, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_ZC), onZeroCross, RISING);
}

void loop() {
  // 255부터 0까지 1씩 감소하며 측정
  for (int level = 255; level >= 0; level--) {
    updateDimming(level);
    delay(200); // 안정화 대기
    
    float currentLux = lightMeter.readLightLevel();
    
    Serial.print(level);
    Serial.print(",");
    Serial.println(currentLux);
  }

  Serial.println(F("--- Sweep Finished ---"));
  while(true); 
}

void updateDimming(int level) {
  if (level <= 12) {
    isOff = true;
  } else {
    isOff = false;
    uint32_t span = MAX_DELAY_US - MIN_DELAY_US;
    fireDelayUs = MAX_DELAY_US - (span * (level - 12) / (255 - 12));
  }
}