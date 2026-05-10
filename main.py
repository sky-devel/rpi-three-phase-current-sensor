from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from gpiozero import CPUTemperature
from psycopg2.extras import Json
from config import settings
from database import execute_query
from datetime import datetime
import traceback
import threading
import serial
import time
import copy
import sys

cpu = CPUTemperature()

clients = {}

for number, port in settings.SERIAL_PORTS.items():
    clients[number] = ModbusClient(method='rtu', port=port, baudrate=settings.BAUD_RATE, timeout=1, bytesize=8, stopbits=1, parity='N')


data = {sensor_number: {
    "voltage": [],
    "current": [],
    "power": [],
    "frequency": [],
    "power_factor": []
    } for sensor_number in clients}
data['engine_revolutions'] = []
data_lock = threading.Lock()
sending_data_lock = threading.Lock()
reading_event = threading.Event()
reading_event.set()
current_minute = datetime.now().strftime("%H:%M")
current_date = datetime.date(datetime.now())


def read_sensor_data(sensor_number: int, client: ModbusClient, data_buffer: dict):
    print(f'The query cycle for sensor {sensor_number} has been created', file=sys.stdout)
    last_time = time.time()
    start_minute = datetime.now().strftime("%H:%M")

    with client:
        while True:
            try:
                if time.time() - last_time >= 0.7:
                    last_time = time.time()
                    response = client.read_input_registers(
                        address=0x00,
                        count=10,
                        unit=1,
                    )
                    if start_minute != current_minute:
                        start_minute = current_minute
                        reading_event.wait()
                        for key in list(data_buffer):
                            data_buffer[key] = []
                        continue
                    else:
                        voltage = response.registers[0] / 10.0
                        current = (response.registers[2] << 16 | response.registers[1]) / 1000.0
                        power = (response.registers[4] << 16 | response.registers[3]) / 10.0
                        # energy = (response.registers[6] << 16 | response.registers[5])
                        frequency = response.registers[7] / 10.0
                        power_factor = response.registers[8] / 100.0
                        reading_event.wait()
                        data_lock.acquire()
                        data_buffer["voltage"].append(voltage)
                        data_buffer["current"].append(current)
                        data_buffer["power"].append(power)
                        data_buffer["frequency"].append(frequency)
                        data_buffer["power_factor"].append(power_factor)
                        data_lock.release()
                    # print(f"V: {voltage}V | A: {current}A | W: {power}W | F: {frequency}Hz | PF: {power_factor}")
            except Exception as ex:
                print(f'Sensor {sensor_number}:', traceback.format_exc(), file=sys.stderr)


def read_engine_revolutions():
    port = None
    
    try:
        def open_port():
            port = serial.Serial('/dev/serial0', 9600, timeout=1)
            time.sleep(0.5)
            return port

        port = open_port()
        start_minute = datetime.now().strftime('%H:%M')

        while True:
            try:
                if port.is_open and port.in_waiting > 0:
                    if start_minute != current_minute:
                        start_minute = current_minute
                        reading_event.wait()
                        data['engine_revolutions'] = []
                        continue
                    
                    line = port.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        value = int(line)
                        print(value)
                        reading_event.wait()
                        data_lock.acquire()
                        data['engine_revolutions'].append(value)
                        data_lock.release()
            except OSError as e:
                # Ошибка порта
                try:
                    port.close()
                except Exception:
                    pass
                port = open_port()
                time.sleep(0.2)
    except Exception as ex:
        print(traceback.format_exc())
        try:
            if port and port.is_open:
                port.close()
        finally:
            read_engine_revolutions()

def mian_loop():
    global current_minute
    global current_date

    def send_data(sensors_data):
        query = f"INSERT INTO three_phase_data (datetime, machine, p1, p2, p3, engine, metadata) VALUES ('{current_date} {current_minute}', {settings.MACHINE_ID}, {Json(sensors_data[1])}, {Json(sensors_data[2])}, {Json(sensors_data[3])}, {Json({'revolutions': sensors_data['engine_revolutions']})}, {Json({'temperature': round(cpu.temperature, 1)})});"
        threading.Thread(target=execute_query, args=(query,)).start()

    while True:
        try:
            if current_minute != datetime.now().strftime("%H:%M"):
                reading_event.clear()
                with data_lock:
                    send_data(sensors_data=copy.deepcopy(data))
                reading_event.set()
                current_minute = datetime.now().strftime("%H:%M")
                current_date = datetime.date(datetime.now())
        except Exception as ex:
            print(traceback.format_exc())
            time.sleep(10)


if __name__ == "__main__":
    for sensor_number, client in clients.items():
        threading.Thread(target=read_sensor_data, args=(sensor_number, client, data[sensor_number])).start()
    threading.Thread(target=read_engine_revolutions).start()
    threading.Thread(target=mian_loop).start()
