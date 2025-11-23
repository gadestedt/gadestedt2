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

   Om dina tSENSE-register rapporterar olika noggrannhet kan du även ange decimaler per värde. Standardvärdena matchar Senseairs dokumentation: hel tal för CO₂ och en decimal för temperatur/luftfuktighet:

   ```bash
   python sensor_gui.py \
     --serial-port COM3 \
     --co2-decimals 0 \
     --temperature-decimals 1 \
     --humidity-decimals 1
   ```

5. För mjukare värden kan du justera glättningen (standard 0.0, intervallet 0-1). Högre tal ger mer utjämning och långsammare förändringar, medan `0` visar råvärden utan glättning:

   ```bash
   python sensor_gui.py --serial-port COM3 --smoothing-factor 0.15
   ```
