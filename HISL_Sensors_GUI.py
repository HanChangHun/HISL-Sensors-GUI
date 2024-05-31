import pymysql
import tkinter as tk
from tkinter import ttk, simpledialog, font
import threading
import time
import json


def load_config(file_path):
    with open(file_path) as f:
        return json.load(f)


def fetch_data(cursor, query):
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else None


def sensor_data_monitor(db_config, interval, stop_event, sensor_data):
    db = pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        db=db_config["db"],
        password=db_config["password"],
        charset="utf8",
    )
    cursor = db.cursor()

    while not stop_event.is_set():
        # Env Board 데이터 조회
        query = (
            "SELECT temperature FROM env_board WHERE device_id = 'env_board_1'"
        )
        sensor_data["Ambient Temperature"] = fetch_data(cursor, query)

        query = "SELECT ambient_light FROM env_board WHERE device_id = 'env_board_1'"
        sensor_data["Ambient Light"] = fetch_data(cursor, query)

        query = (
            "SELECT humidity FROM env_board WHERE device_id = 'env_board_1'"
        )
        sensor_data["Humidity"] = fetch_data(cursor, query)

        query = (
            "SELECT timestamp FROM env_board WHERE device_id = 'env_board_1'"
        )
        sensor_data["Env Board Timestamp"] = fetch_data(cursor, query)

        # Monsoon 데이터 조회
        query = "SELECT power FROM monsoon WHERE device_id = 'monsoon_1'"
        sensor_data["Power"] = fetch_data(cursor, query)

        query = "SELECT current FROM monsoon WHERE device_id = 'monsoon_1'"
        sensor_data["Current"] = fetch_data(cursor, query)

        query = "SELECT voltage FROM monsoon WHERE device_id = 'monsoon_1'"
        sensor_data["Voltage"] = fetch_data(cursor, query)

        query = "SELECT timestamp FROM monsoon WHERE device_id = 'monsoon_1'"
        sensor_data["Monsoon Timestamp"] = fetch_data(cursor, query)

        # center309 데이터 조회
        query = (
            "SELECT t1, t2, timestamp FROM center309 ORDER BY id DESC LIMIT 1"
        )
        result = fetch_data(cursor, query)
        if result:
            (
                sensor_data["t1"],
                sensor_data["t2"],
                sensor_data["center309 Timestamp"],
            ) = result
        else:
            sensor_data["t1"] = sensor_data["t2"] = sensor_data[
                "center309 Timestamp"
            ] = None

        db.commit()  # 데이터 변경 사항 커밋
        time.sleep(interval)

    db.close()


def update_gui(sensor_data, labels):
    while True:
        labels["Ambient Temperature"].config(
            text=f"Ambient Temperature: {sensor_data['Ambient Temperature']}°C",
            anchor="w",
        )
        labels["Ambient Light"].config(
            text=f"Ambient Light: {sensor_data['Ambient Light']} lux",
            anchor="w",
        )
        labels["Humidity"].config(
            text=f"Humidity: {sensor_data['Humidity']}%",
            anchor="w",
        )
        labels["Env Board Timestamp"].config(
            text=f"Env Board Timestamp: {sensor_data['Env Board Timestamp']}\n",
            anchor="w",
        )
        labels["Power"].config(
            text=f"Power: {sensor_data['Power']:.4f} W",
            anchor="w",
        )
        labels["Current"].config(
            text=f"Current: {sensor_data['Current']:.4f} mA",
            anchor="w",
        )
        labels["Voltage"].config(
            text=f"Voltage: {sensor_data['Voltage']:.4f} V",
            anchor="w",
        )
        labels["Monsoon Timestamp"].config(
            text=f"Monsoon Timestamp: {sensor_data['Monsoon Timestamp']}",
            anchor="w",
        )
        labels["t1"].config(
            text=(
                f"t1: {sensor_data['t1']}°C"
                if sensor_data["t1"]
                else "t1: N/A"
            ),
            anchor="w",
        )
        labels["t2"].config(
            text=(
                f"t2: {sensor_data['t2']}°C"
                if sensor_data["t2"]
                else "t2: N/A"
            ),
            anchor="w",
        )
        labels["center309 Timestamp"].config(
            text=(
                f"center309 Timestamp: {sensor_data['center309 Timestamp']}"
                if sensor_data["center309 Timestamp"]
                else "center309 Timestamp: N/A"
            ),
            anchor="w",
        )
        time.sleep(1)  # GUI 업데이트 간격 (1초)


def main():
    root = tk.Tk()  # 기본 루트 윈도우 생성
    root.withdraw()  # 루트 윈도우 숨기기

    # 글씨 크기 설정
    font_size = 18
    custom_font = font.Font(size=font_size)

    db_config = load_config("mysql_config.json")

    interval = 1.0  # 모니터링 간격 (초)

    sensor_data = {
        "Ambient Temperature": None,
        "Ambient Light": None,
        "Humidity": None,
        "Env Board Timestamp": None,
        "Power": None,
        "Current": None,
        "Voltage": None,
        "Monsoon Timestamp": None,
    }

    stop_event = threading.Event()

    # GUI 생성
    root.deiconify()  # 루트 윈도우 보이기
    root.title("Sensor Data Monitoring")

    labels = {}
    for key in sensor_data.keys():
        label = ttk.Label(root, text=f"{key}: ", font=custom_font)
        label.pack(anchor="w")
        labels[key] = label

    # 모니터링 스레드 시작
    monitor_thread = threading.Thread(
        target=sensor_data_monitor,
        args=(db_config, interval, stop_event, sensor_data),
    )
    monitor_thread.start()

    # GUI 업데이트 스레드 시작
    gui_thread = threading.Thread(
        target=update_gui,
        args=(sensor_data, labels),
    )
    gui_thread.daemon = True
    gui_thread.start()

    root.mainloop()

    # 모니터링 스레드 중지
    stop_event.set()
    monitor_thread.join()


if __name__ == "__main__":
    main()
