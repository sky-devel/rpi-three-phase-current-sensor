from pymodbus.client.serial import ModbusSerialClient as ModbusClient
from config import settings
from database import execute_query
from datetime import datetime
from loguru import logger
import time


logger.add("app.log", rotation="10 MB", format="\n{time}\n{level}\n{message}")
clients = [ModbusClient(port=serial_port, baudrate=settings.BAUD_RATE, timeout=1) for serial_port in settings.SERIAL_PORT_LIST]


def read_sensor_data(client: ModbusClient):
    try:
        client.connect()
        response = client.read_input_registers(
            address=0x0000,
            count=6,
            slave=settings.SLAVE_ID,
        )

        if response.isError():
            raise Exception(f"Error in the response of the device({client})")
        else:
            voltage = response.registers[0] / 10.0
            current = response.registers[1] / 100.0
            power = response.registers[2]
            print(f"Voltage: {voltage:.2f} V, Current: {current:.2f} A, Power: {power} W", end='\n')
    except Exception as ex:
        logger.error(f"ModbusClient: {client}\n{ex}")    
    finally:
        client.close()

if __name__ == "__main__":
    while True:
        for client in clients:
            read_sensor_data(client)
        time.sleep(1)
        print("\n")
