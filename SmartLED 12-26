#include <Wire.h>
#include <BH1750.h>


// --- 하드웨어 핀 설정 ---
const int PIN_ZC  = 2;   // Zero-Cross 감지
const int PIN_PSM = 9;   // 트라이악 트리거 신호


// --- AC 제어 타이밍 설정 (60Hz 기준) ---
const uint16_t MAX_DELAY_US = 7000; // 최저 밝기 안정화 (딜레이 최대)
const uint16_t MIN_DELAY_US = 1000; // 최고 밝기 안정화 (딜레이 최소)


// --- 제어 변수 ---
volatile uint16_t fireDelayUs = MAX_DELAY_US;
volatile bool isOff = true;


BH1750 lightMeter;


// 목표 조도 관련 변수 (실시간 수정 가능하도록 const 제거)
float targetLux = 1500.0;
const float ALLOWED_ERROR = 5.0; // 허용 오차 (5 Lux 이내면 유지)
float currentLevel = 150.0;      // 현재 출력 레벨 (0~255)


// --- 인터럽트 서비스 루틴 (ISR) ---
// 제로 크로싱 발생 시 즉시 실행되어 깜빡임을 방지함
void onZeroCross() {
  if (isOff) return;
  delayMicroseconds(fireDelayUs);
  digitalWrite(PIN_PSM, HIGH);
  delayMicroseconds(20); // 트리거 유지 시간
  digitalWrite(PIN_PSM, LOW);
}


void setup() {
  Serial.begin(115200);
  Wire.begin();


  // BH1750 초기화
  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println(F("BH1750 Sensor Initialized."));
  } else {
    Serial.println(F("BH1750 Init Failed. Check Wiring."));
  }


  pinMode(PIN_PSM, OUTPUT);
  digitalWrite(PIN_PSM, LOW);
  pinMode(PIN_ZC, INPUT);
 
  // 인터럽트 설정
  attachInterrupt(digitalPinToInterrupt(PIN_ZC), onZeroCross, RISING);


  Serial.println(F("------------------------------------------"));
  Serial.println(F("Type a number in Serial Monitor to change Target Lux."));
  Serial.print(F("Current Target: ")); Serial.println(targetLux);
  Serial.println(F("------------------------------------------"));
}


unsigned long lastControlTime = 0;
const unsigned long controlInterval = 100; // 0.1초마다 제어 루프 실행


void loop() {
  // 1. 시리얼 입력 처리 (실시간 목표치 수정)
  if (Serial.available() > 0) {
    float inputVal = Serial.parseFloat(); // 숫자를 읽어들임
    if (inputVal >= 10.0 && inputVal <= 5000.0) { // 유효 범위 확인
      targetLux = inputVal;
      Serial.print(F("\n[!] Target Lux updated to: "));
      Serial.println(targetLux);
    }
    // 입력 버퍼 비우기
    while(Serial.available() > 0) Serial.read();
  }


  // 2. 주기적 피드백 제어 실행
  unsigned long now = millis();
  if (now - lastControlTime >= controlInterval) {
    lastControlTime = now;


    float currentLux = lightMeter.readLightLevel();
    float error = targetLux - currentLux;


    // 조도 오차가 허용 범위를 벗어난 경우에만 레벨 수정
    if (abs(error) > ALLOWED_ERROR) {
      // P-제어: 오차에 비례하여 수정치 결정 (0.04는 감도 조절값)
      float step = error * 0.04;
     
      // 급격한 조명 변화 방지를 위한 리미터
      if (step > 3.0) step = 3.0;
      if (step < -3.0) step = -3.0;


      currentLevel += step;
    }


    // 출력 레벨 제한 (0~255)
    if (currentLevel > 255.0) currentLevel = 255.0;
    if (currentLevel < 0.0)   currentLevel = 0.0;


    // 실제 출력 적용
    updateDimming((int)currentLevel);


    // 모니터링 출력
    Serial.print(F("Target: ")); Serial.print((int)targetLux);
    Serial.print(F(" | Current Lux: ")); Serial.print(currentLux, 1);
    Serial.print(F(" | Level: ")); Serial.println((int)currentLevel);
  }
}


// 레벨을 AC 타이밍으로 변환하는 함수
void updateDimming(int level) {
  // 저조도 구간 깜빡임 방지를 위해 12단계 이하는 Off
  if (level <= 12) {
    isOff = true;
  } else {
    isOff = false;
    uint32_t span = MAX_DELAY_US - MIN_DELAY_US;
    // 레벨이 높을수록 딜레이가 짧아짐 (더 밝아짐)
    fireDelayUs = MAX_DELAY_US - (span * (level - 12) / (255 - 12));
  }
}
