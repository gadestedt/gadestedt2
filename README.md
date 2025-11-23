# gadestedt2

Ett enkelt Tkinter-baserat GUI som visar simulerade sensorvärden.

## Körning

1. Se till att Python 3 finns installerat på systemet.
2. Installera beroenden:

   ```bash
   pip install minimalmodbus pyserial
   ```

3. Starta programmet med simulering (standard):

   ```bash
   python sensor_gui.py
   ```

   Värdena uppdateras automatiskt varje sekund.

4. Anslut till en Senseair tSENSE via seriell port (Modbus RTU):

   ```bash
   python sensor_gui.py --serial-port COM3 --slave-address 1 --baudrate 9600
   ```

   Ange `--serial-port` till rätt portnamn (t.ex. `/dev/ttyUSB0` på Linux). Vid behov kan registeradresser justeras via `--co2-register`, `--temperature-register` och `--humidity-register` (hex eller decimal). Lägg till `--simulate` om du vill tvinga simulering även med angiven port.
