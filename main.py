import json
import sys
import Adafruit_ADS1x15
from statistics import mean
from database import execute_query
from datetime import datetime

adc = Adafruit_ADS1x15.ADS1x15.ADS1115(address=0x48, busnum=1)

print("ADC values:")
val_sequence = {"analog_input_0": [], "analog_input_1": [], "analog_input_2": []}
while True:
    start_time = datetime.now()
    while start_time.minute == datetime.now().minute:
        val_sequence["analog_input_0"].append(adc.read_adc(0, gain=1, data_rate=475))
        val_sequence["analog_input_1"].append(adc.read_adc(1, gain=1, data_rate=475))
        val_sequence["analog_input_2"].append(adc.read_adc(2, gain=1, data_rate=475))
        sys.stdout.write(f"\r%i %i %i" % tuple([mean(values) for values in val_sequence.values()]))
        sys.stdout.flush()
    else:
        execute_query("INSERT INTO sensor_data(datetime, data) VALUES ('%s', '%s');" % (start_time.strftime('%Y-%m-%d %H:%M:00'), json.dumps(val_sequence)))
        val_sequence = {key: [] for key in val_sequence.keys()}
