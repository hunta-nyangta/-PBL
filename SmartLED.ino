#include <Wire.h>
#include <BH1750.h>

// --- 하드웨어 핀 설정 ---
const int PIN_ZC  = 2;   // Zero-Cross 감지
const int PIN_PSM = 9;   // 트라이악 트리거 신호

// --- AC 제어 타이밍 설정 (60Hz 기준) ---
const uint16_t MAX_DELAY_US = 7000; // 최저 밝기 안정화
const uint16_t MIN_DELAY_US = 1000; // 최고 밝기 안정화

// --- 필터 및 제어 설정 ---
#define WINDOW_SIZE 5             // 이동 평균 필터 크기
float luxHistory[WINDOW_SIZE] = {0,};
int luxIndex = 0;

float targetLux = 1500.0;          // 목표 조도
float Kp = 0.01;                   // 제어 Gain (G 명령으로 수정 가능)
const float DEADBAND = 5.0;        // 데드밴드 (5 Lux 이내 오차는 무시)

float currentLevel = 160.0;        // 현재 출력 레벨 (0~255)
volatile uint16_t fireDelayUs = MAX_DELAY_US;
volatile bool isOff = true;

BH1750 lightMeter;

// --- 인터럽트 서비스 루틴 ---
void onZeroCross() {
  if (isOff) return;
  delayMicroseconds(fireDelayUs);
  digitalWrite(PIN_PSM, HIGH);
  delayMicroseconds(20);
  digitalWrite(PIN_PSM, LOW);
}

// --- 이동 평균 필터 함수 ---
float getFilteredLux(float newLux) {
  luxHistory[luxIndex] = newLux;
  luxIndex = (luxIndex + 1) % WINDOW_SIZE;
  
  float sum = 0;
  for (int i = 0; i < WINDOW_SIZE; i++) sum += luxHistory[i];
  return sum / WINDOW_SIZE;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println(F("BH1750 Initialized"));
  }

  pinMode(PIN_PSM, OUTPUT);
  pinMode(PIN_ZC, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_ZC), onZeroCross, RISING);

  // 초기값으로 필터 배열 채우기
  float initLux = lightMeter.readLightLevel();
  for(int i=0; i<WINDOW_SIZE; i++) luxHistory[i] = initLux;
}

unsigned long lastControlTime = 0;
const unsigned long controlInterval = 100; // 0.1초마다 제어

void loop() {
  // 1. 실시간 파라미터 변경 (예: T1500 또는 G0.03 입력)
  if (Serial.available() > 0) {
    char type = Serial.read();
    float val = Serial.parseFloat();
    if (type == 'T') targetLux = val; 
    if (type == 'G') Kp = val;        
    while(Serial.available() > 0) Serial.read(); // 버퍼 비우기
  }

  unsigned long now = millis();
  if (now - lastControlTime >= controlInterval) {
    lastControlTime = now;

    // 2. 센서 읽기 및 필터링 (안정화 단계)
    float rawLux = lightMeter.readLightLevel();
    float filteredLux = getFilteredLux(rawLux);

    // 3. 데드밴드가 적용된 오차 기반 제어 (지능화 단계)
    float error = targetLux - filteredLux;

    if (abs(error) > DEADBAND) {
      // 오차가 데드밴드(5.0)보다 클 때만 레벨을 수정하여 헌팅 방지
      currentLevel += (error * Kp);
    }

    // 4. 범위 제한 및 출력 적용
    currentLevel = constrain(currentLevel, 12, 255);
    updateDimming((int)currentLevel);

    // 5. 파이썬 그래프용 CSV 출력 (데이터 검증 단계)
    // 형식: 시간,목표,생데이터,필터데이터,레벨,Gain
    Serial.print(now);           Serial.print(",");
    Serial.print(targetLux);     Serial.print(",");
    Serial.print(rawLux);        Serial.print(",");
    Serial.print(filteredLux);   Serial.print(",");
    Serial.print(currentLevel);  Serial.print(",");
    Serial.println(Kp);
  }
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