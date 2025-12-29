import serial
import matplotlib.pyplot as plt
import pandas as pd
import time
from datetime import datetime

# --- 1. 통신 및 파일 설정 ---
PORT = 'COM6'  # 본인의 아두이노 포트 번호로 수정하세요
BAUD = 115200
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
FILENAME = f"sweep_data_{current_time}.csv"

# 데이터 저장을 위한 리스트
levels = []
lux_values = []

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2) # 연결 안정화
    ser.reset_input_buffer()
    print(f"연결 성공: {PORT}. 스캔 데이터를 기다리는 중...")
except Exception as e:
    print(f"연결 오류: {e}")
    exit()

# --- 2. 그래프 실시간 설정 ---
plt.style.use('seaborn-v0_8-whitegrid') # 그래프 스타일 설정
fig, ax = plt.subplots(figsize=(10, 6))
line, = ax.plot([], [], 'b-o', markersize=3, label='Measured Lux')
ax.set_title("Lux vs PSM Level Characteristic Curve", fontsize=14)
ax.set_xlabel("PSM Level (0 - 255)", fontsize=12)
ax.set_ylabel("Illuminance (Lux)", fontsize=12)
ax.set_xlim(0, 260)
ax.grid(True)

# --- 3. 데이터 수신 및 시각화 루프 ---
while True:
    if ser.in_waiting > 0:
        raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
        
        # 종료 신호 확인
        if "Sweep Finished" in raw_line:
            print("\n[완료] 스캔이 끝났습니다. 데이터를 저장합니다.")
            break
            
        # 데이터 파싱 (CSV 형식: Level, Lux)
        try:
            parts = raw_line.split(',')
            if len(parts) == 2:
                lvl = int(parts[0])
                lux = float(parts[1])
                
                levels.append(lvl)
                lux_values.append(lux)
                
                # 실시간 그래프 업데이트
                line.set_data(levels, lux_values)
                ax.set_ylim(0, max(lux_values) * 1.1 if lux_values else 100)
                plt.pause(0.01)
                
                print(f"Level: {lvl:3} | Lux: {lux:8.2f}", end='\r')
        except ValueError:
            continue

# --- 4. 데이터 저장 및 최종 출력 ---
# Pandas를 이용한 저장
df = pd.DataFrame({'PSM_Level': levels, 'Lux': lux_values})
df.to_csv(FILENAME, index=False)
plt.savefig(f"characteristic_curve_{current_time}.png")

print(f"\n저장 완료: {FILENAME}")
print(f"최고 조도: {df['Lux'].max()} Lux")
plt.show() # 결과 그래프 창 유지

ser.close()