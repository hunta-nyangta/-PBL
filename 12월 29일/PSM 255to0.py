import serial
import matplotlib.pyplot as plt
import pandas as pd
import time
from datetime import datetime

# --- 설정 ---
PORT = 'COM6'  # 본인의 포트로 수정
BAUD = 115200
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
FILENAME = f"down_sweep_{current_time}.csv"

levels, lux_values = [], []

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()
    print(f"연결 성공: {PORT}. 하향 스캔 데이터를 기다리는 중...")
except Exception as e:
    print(f"연결 오류: {e}")
    exit()

# 그래프 설정
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(10, 6))
line, = ax.plot([], [], 'r-o', markersize=3, label='Down-Sweep Lux')
ax.set_title("Lux vs PSM Level (255 -> 0)", fontsize=14)
ax.set_xlabel("PSM Level", fontsize=12)
ax.set_ylabel("Lux", fontsize=12)
ax.set_xlim(255, 0) # X축을 역순으로 설정하여 내려오는 느낌 강조
ax.grid(True)

while True:
    if ser.in_waiting > 0:
        raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
        
        if "Sweep Finished" in raw_line:
            print("\n[완료] 데이터 수집 종료.")
            break
            
        try:
            parts = raw_line.split(',')
            if len(parts) == 2:
                lvl = int(parts[0])
                lux = float(parts[1])
                
                levels.append(lvl)
                lux_values.append(lux)
                
                # 실시간 업데이트
                line.set_data(levels, lux_values)
                ax.set_ylim(0, max(lux_values) * 1.1 if lux_values else 100)
                plt.pause(0.01)
                print(f"Level: {lvl:3} | Lux: {lux:8.2f}", end='\r')
        except ValueError:
            continue

# 데이터 저장
df = pd.DataFrame({'PSM_Level': levels, 'Lux': lux_values})
df.to_csv(FILENAME, index=False)
plt.savefig(f"down_sweep_graph_{current_time}.png")
print(f"\n파일 저장 완료: {FILENAME}")
plt.show()
ser.close()