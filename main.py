import sys
import time
import Adafruit_ADS1x15

adc = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1)


print("ADC values:")
while True:
    val_arr = list()
    for i in range(4):
        val_arr.append(adc.read_adc(i))
    sys.stdout.write(f"\r%i %i %i %i" % tuple(val_arr))
    sys.stdout.flush()
    time.sleep(1)

