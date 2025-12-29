
#include <Wire.h>
#include <BH1750.h>

// --- 하드웨어 핀 설정 ---
const int PIN_ZC  = 2;   // Zero-Cross 감지
const int PIN_PSM = 9;   // 트라이악 트리거 신호

// --- AC 제어 타이밍 설정 (60Hz 기준) ---
const uint16_t MAX_DELAY_US = 7000; // 최저 밝기 (딜레이 최대)
const uint16_t MIN_DELAY_US = 1000; // 최고 밝기 (딜레이 최소)

// --- 제어 변수 ---
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
    Serial.println(F("PSM_Level,Lux")); // CSV 헤더 출력
  } else {
    while(1); // 센서 연결 실패 시 중단
  }

  pinMode(PIN_PSM, OUTPUT);
  digitalWrite(PIN_PSM, LOW);
  pinMode(PIN_ZC, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_ZC), onZeroCross, RISING);
}

void loop() {
  // 0부터 255까지 1씩 증가하며 측정
  for (int level = 0; level <= 255; level++) {
    updateDimming(level);
    
    // 센서 및 램프가 안정화될 시간 대기 (BH1750 고해상도 모드 응답시간 고려)
    delay(200); 
    
    float currentLux = lightMeter.readLightLevel();
    
    // 시리얼 플로터나 엑셀에서 바로 쓸 수 있도록 출력
    Serial.print(level);
    Serial.print(",");
    Serial.println(currentLux);
  }

  // 한 번의 스윕이 끝나면 멈춤 (필요 시 다시 시작하려면 리셋)
  Serial.println(F("--- Sweep Finished ---"));
  while(true); 
}

void updateDimming(int level) {
  if (level <= 12) {
    isOff = true;
  } else {
    isOff = false;
    uint32_t span = MAX_DELAY_US - MIN_DELAY_US;
    // 레벨이 높을수록 딜레이가 짧아짐 (위상각이 커짐)
    fireDelayUs = MAX_DELAY_US - (span * (level - 12) / (255 - 12));
  }
}

