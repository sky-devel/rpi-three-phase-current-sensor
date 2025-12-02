from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from gpiozero import CPUTemperature
from psycopg2.extras import Json
from config import settings
from database import execute_query
from datetime import datetime
from loguru import logger
import traceback
import threading
import time
import json
import copy

cpu = CPUTemperature()
# logger.add("app.log", rotation="10 MB", format="\n{time}\n{level}\n{message}")

clients = [ModbusClient(method='rtu', port=serial_port, baudrate=settings.BAUD_RATE, timeout=1, bytesize=8, stopbits=1,
                        parity='N') for serial_port in settings.SERIAL_PORT_LIST]

data = {str(client.port): {"voltage": [], "current": []} for client in clients}
data_lock = threading.Lock()
sending_data_lock = threading.Lock()
reading_event = threading.Event()
reading_event.set()
current_minute = datetime.now().strftime("%H:%M")
current_date = datetime.date(datetime.now())


def read_sensor_data(client: ModbusClient, data_buffer: dict):
    last_time = time.time()
    start_minute = datetime.now().strftime("%H:%M")

    while True:
        try:
            with client:
                if time.time() - last_time >= 0.7:
                    print(round(cpu.temperature, 1))
                    last_time = time.time()
                    response = client.read_input_registers(
                        address=0x00,
                        count=6,
                        unit=1,
                    )

                    if start_minute != current_minute:
                        start_minute = current_minute
                        reading_event.wait()
                        data_buffer["voltage"] = []
                        data_buffer["current"] = []
                        # data_buffer["power"] = []
                        continue
                    else:
                        voltage = response.registers[0] / 10.0
                        current = response.registers[1] / 100.0
                        # power = response.registers[2]
                        # logger.info(f"{str(client)}, {voltage}, {current}")
                        reading_event.wait()
                        data_lock.acquire()
                        data_buffer["voltage"].append(voltage)
                        data_buffer["current"].append(current)
                        data_lock.release()
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            # logger.error(f"ModbusClient: {client}\n{ex}")


def mian_loop():
    global current_minute
    global current_date

    def send_data(data):
        query = 'INSERT INTO three_phase_data (datetime, machine, sensor, data) VALUES '
        for client in clients:
            print(client, str(client.port)[-11], client.port, sep='---')
            sensor_id = str(client.port)[-11]
            client = client.port
            data[client]['temperature'] = round(cpu.temperature, 1)
            query += f"('{current_date} {current_minute}', 0, {sensor_id}, {Json(data[client])}), "
        query = query[:-2] + ';'
        threading.Thread(target=execute_query, args=(query,)).start()

    while True:
        try:
            if current_minute != datetime.now().strftime("%H:%M"):
                reading_event.clear()
                with data_lock:
                    send_data(data=copy.deepcopy(data))
                reading_event.set()
                current_minute = datetime.now().strftime("%H:%M")
                current_date = datetime.date(datetime.now())
        except Exception as ex:
            print(ex)
            # logger.error(f"Main Loop Exaption:\n{ex}")
            time.sleep(10)


if __name__ == "__main__":
    for client in clients:
        threading.Thread(target=read_sensor_data, args=(client, data[str(client.port)])).start()
    threading.Thread(target=mian_loop).start()
