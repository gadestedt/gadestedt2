# tSense-dashboard

En enkel dashboard för att läsa tSense-data via seriell port och visa den i webbläsaren.

## Kom igång

1. Installera beroenden:
   ```bash
   npm install
   ```
2. Starta servern:
   ```bash
   npm start
   ```
3. Öppna http://localhost:3000 i webbläsaren.
4. Välj COM-port/seriell port och baud rate, klicka på **Anslut** och följ live-flödet.

> Ingen hårdvara? Välj porten **Demo-ström (mock)** som skapas automatiskt. Då skickas simulerade mätvärden var sekund så att dashboarden kan testas utan seriell enhet. Stäng av mock-porten via `ENABLE_MOCK=false` om du inte vill exponera den.

## Funktioner
- Upptäcker tillgängliga seriella portar.
- Kan starta/stoppa anslutningar till valfri port.
- WebSocket-ström med rå data och ev. tolkad JSON.
- Logg över de senaste 100 meddelandena.

## Tips
- Standardhastighet är 115200 baud, men kan ändras.
- Om hårdvaran skickar JSON per rad visas strukturerad vy automatiskt.
