from pymodbus.client.serial import ModbusSerialClient as ModbusClient
from config import settings
from database import execute_query
from datetime import datetime


clients = [ModbusClient(port=serial_port, baudrate=settings.BAUD_RATE, timeout=1) for serial_port in settings]

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
            print(response)

    except Exception as ex:
        print(ex)
    finally:
        client.close()