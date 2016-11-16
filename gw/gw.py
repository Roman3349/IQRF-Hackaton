import argparse
import time
from ubidots import ApiClient
from iqrf.transport import cdc


ARGS = argparse.ArgumentParser(description="IQRF MQTT gateway.")
ARGS.add_argument("-p", "--port", action="store", dest="port", required=True, type=str, help="The port name to connect to.")

class Protronix:
    
    co2  = None
    hum  = None
    temp = None
    CO2_HIGH_BYTE_POS         = 18;
    CO2_LOW_BYTE_POS          = 19;
    TEMPERATURE_HIGH_BYTE_POS = 14;
    TEMPERATURE_LOW_BYTE_POS  = 15;
    HUMIDITY_HIGH_BYTE_POS    = 22;
    HUMIDITY_LOW_BYTE_POS     = 23;

    def decode(self, response):
        self.co2  = (response[self.CO2_HIGH_BYTE_POS] << 8) | response[self.CO2_LOW_BYTE_POS]
        self.temp = ((response[self.TEMPERATURE_HIGH_BYTE_POS] << 8) | response[self.TEMPERATURE_LOW_BYTE_POS]) / 10
        self.hum = ((response[self.HUMIDITY_HIGH_BYTE_POS] << 8) | response[self.HUMIDITY_LOW_BYTE_POS]) / 10

def main():
    device = None
    protronix = Protronix()
    sensorPacket = bytes([0x01, 0x00, 0x0C, 0x02, 0xFF, 0xFF, 0xFE, 0x01, 0x42, 0x00, 0x03, 0x75, 0x33, 0x75, 0x31, 0x75, 0x32, 0xD9, 0x86])
    relay0OutputPacket = bytes([0x02, 0x00, 0x09, 0x01, 0xFF, 0xFF, 0x02, 0x04, 0x00])
    relay0OnPacket = bytes([0x02, 0x00, 0x09, 0x01, 0xFF, 0xFF, 0x02, 0x04, 0x04])
    relay0OffPacket = bytes([0x02, 0x00, 0x09, 0x01, 0xFF, 0xFF, 0x02, 0x04, 0x00])
    relay0Status = 0
    relay1OutputPacket = bytes([0x02, 0x00, 0x09, 0x01, 0xFF, 0xFF, 0x02, 0xA0, 0x00])
    relay1OnPacket = bytes([0x02, 0x00, 0x09, 0x01, 0xFF, 0xFF, 0x02, 0xA0, 0xA0])
    relay1OffPacket = bytes([0x02, 0x00, 0x09, 0x01, 0xFF, 0xFF, 0x02, 0xA0, 0x00])
    relay1Status = 0
    api = ApiClient(token='5b8VxXADFKoWmU3hW1vCbaRUjk6Jm2')
    apiCo2P = api.get_variable('582ba4fd76254229cbbaaf2b')
    apiHumP = api.get_variable('582baea2762542639adaa8e0')
    apiTempP = api.get_variable('582bacfb76254259b46cef24')
    apiRelay0 = api.get_variable('582bb0297625426d34553eac')
    apiRelay1 = api.get_variable('582bce78762542240da80aaf')
    while (True):
        time.sleep(1)
        try:
            device = cdc.open(ARGS.parse_args().port)
            test = device.send(cdc.TestRequest(), timeout=5)
            if test.status == cdc.CdcStatus.OK:
                device.send(cdc.DataSendRequest(sensorPacket))
                device.receive(timeout=5)
                protronix.decode(device.receive(timeout=5).data)
                print("CO2  (P) >", protronix.co2)
                apiCo2P.save_value({'value': protronix.co2})
                print("Hum  (P) >", protronix.hum)
                apiHumP.save_value({'value': protronix.hum})
                print("Temp (P) >", protronix.temp)
                apiTempP.save_value({'value': protronix.temp})
                if (relay0Status != apiRelay0.get_values(1)[0]['value']):
                    device.send(cdc.DataSendRequest(relay0OutputPacket))
                    relay0Status = apiRelay0.get_values(1)[0]['value']
                    if (relay0Status == 1):
                        device.send(cdc.DataSendRequest(relay0OnPacket))
                        print("Relay0   > On")
                    else:
                        device.send(cdc.DataSendRequest(relay0OffPacket))
                        print("Relay0   > Off")
                if (relay1Status != apiRelay1.get_values(1)[0]['value']):
                    device.send(cdc.DataSendRequest(relay1OutputPacket))
                    relay1Status = apiRelay1.get_values(1)[0]['value']
                    if (relay1Status == 1):
                        device.send(cdc.DataSendRequest(relay1OnPacket))
                        print("Relay1   > On")
                    else:
                        device.send(cdc.DataSendRequest(relay1OffPacket))
                        print("Relay1   > Off")
                print("----------")
            else:
                print("Test request failed!")

        except Exception as error:
            print("An error occured:", type(error), error)
        finally:
            if device is not None:
                device.close()

if __name__ == "__main__":
    main()
