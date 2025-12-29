import serial
import csv
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --- 1. 설정 및 파일 생성 ---
PORT = 'COM6'  # 본인의 포트로 수정
BAUD = 115200

# 파일명에 실행 시각 포함 (예: log_20251229_103000.csv)
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
CSV_FILE = f"light_log_{current_time}.csv"

try:
    ser = serial.Serial(PORT, BAUD, timeout=0.01)
    time.sleep(2)
    ser.reset_input_buffer()
except Exception as e:
    print(f"연결 오류: {e}")
    exit()

# 데이터 리스트 초기화
times, targets, raw_luxs, filtered_luxs, psm_levels = [], [], [], [], []

# CSV 헤더 작성 (아두이노의 6개 출력 데이터와 매칭)
with open(CSV_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Time_ms", "Target", "Raw_Lux", "Filtered_Lux", "PSM_Level", "Gain_Kp"])

# --- 2. 그래프 설정 ---
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
plt.subplots_adjust(hspace=0.4)

def update(frame):
    global times, targets, raw_luxs, filtered_luxs, psm_levels
    
    if ser.in_waiting > 0:
        # 버퍼의 모든 데이터를 읽어 가장 최신 데이터만 선택 (지연 방지)
        raw_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        lines = raw_data.strip().split('\n')
        
        if len(lines) >= 1:
            latest_line = lines[-1] 
            data = latest_line.split(',')
            
            # 아두이노에서 보낸 6개의 데이터가 맞는지 확인
            if len(data) == 6:
                try:
                    t_sec = float(data[0]) / 1000.0
                    tgt, raw, filt, psm, gain = map(float, data[1:])

                    times.append(t_sec)
                    targets.append(tgt)
                    raw_luxs.append(raw)
                    filtered_luxs.append(filt)
                    psm_levels.append(psm)

                    # CSV 실시간 기록
                    with open(CSV_FILE, 'a', newline='') as f:
                        csv.writer(f).writerow(data)

                    # 최근 100개 데이터 표시 (성능 유지)
                    limit = 100
                    t_p = times[-limit:]
                    
                    # 그래프 1: 조도 안정성 검증 (Raw vs Filtered)
                    ax1.clear()
                    ax1.plot(t_p, targets[-limit:], 'r--', label='Target')
                    ax1.plot(t_p, raw_luxs[-limit:], 'b-', alpha=0.3, label='Raw Lux')
                    ax1.plot(t_p, filtered_luxs[-limit:], 'b-', linewidth=2, label='Filtered Lux')
                    ax1.set_title(f"Lux Stability (Target: {tgt} | Filtered: {filt:.1f} lx)")
                    ax1.legend(loc='upper right')

                    # 그래프 2: 제어 출력 (PSM Level)
                    ax2.clear()
                    ax2.plot(t_p, psm_levels[-limit:], 'g-', label='PSM Level')
                    ax2.set_ylabel("PSM Level")
                    ax2.set_title(f"Control Output (Current Level: {int(psm)})")

                    # 그래프 3: 상관관계 분석 (Filtered Lux vs PSM)
                    ax3.clear()
                    ax3.scatter(psm_levels[-300:], filtered_luxs[-300:], c='purple', s=5, alpha=0.5)
                    ax3.set_xlabel("PSM Level")
                    ax3.set_ylabel("Filtered Lux")
                    ax3.set_title("Correlation Analysis")

                except ValueError:
                    pass

# 애니메이션 간격 설정 (50ms)
ani = FuncAnimation(fig, update, interval=50, cache_frame_data=False)
plt.show()
ser.close()