# HA Trading Add-on

Dashboard/add-on sperimentale per seguire titoli finanziari, leggere notizie giornaliere e costruire segnali decisionali dentro Home Assistant.

> Nota: questo progetto non fornisce consulenza finanziaria. Gli score sono segnali informativi da verificare, non raccomandazioni automatiche di acquisto o vendita.

## Cosa contiene

- Add-on Home Assistant in `finance-trading-cockpit/`
- Backend Python FastAPI
- UI web leggera servita dall'add-on
- Watchlist persistente in SQLite nel volume privato `/data` dell'add-on
- Endpoint per aggiungere/rimuovere ticker
- Range grafico stile trading app: oggi, 1 settimana, 1 mese, 1 anno, totale
- Scala prezzi e fonte dati visibili su ogni grafico
- Filtro rapido della watchlist
- Autocomplete ticker con ricerca simboli reali
- Quote e storico prezzi live tramite provider Yahoo Finance non ufficiale
- Notizie generali e notizie collegate ai singoli titoli, con fonte e link apribile
- Score iniziale basato su prezzo, variazione giornaliera e notizie
- Icona add-on in `finance-trading-cockpit/icon.png`
- Dashboard Lovelace di esempio in `home-assistant/dashboard-example.yaml`

## Avvio come add-on Home Assistant

1. In Home Assistant vai su:

   `Impostazioni -> Componenti aggiuntivi -> Negozio componenti aggiuntivi -> menu -> Repository`

2. Aggiungi questa repository:

   `https://github.com/VanHelsing2048/ha-trading-addon`

3. Ricarica lo store se necessario.

4. Installa `Finance Trading Cockpit`.

5. Avvia l'add-on e apri l'interfaccia web dal pannello `Trading Cockpit`.

## Aggiornamenti

Home Assistant rileva gli aggiornamenti dell'add-on dal campo `version` in `finance-trading-cockpit/config.yaml`.
La build usa `BUILD_ARCH` direttamente nel `Dockerfile`, cosi' Raspberry Pi 4 su `aarch64` usa la base image Home Assistant corretta senza `build.yaml`.

## Sicurezza

- L'interfaccia web e' disponibile tramite Home Assistant Ingress.
- Non vengono esposte porte host nel `config.yaml`.
- Non vengono richiesti privilegi, host network, Docker API, Supervisor API o accesso completo.
- Il database resta nel volume privato `/data` dell'add-on.

Per pubblicare una nuova versione:

1. modifica il codice;
2. aggiorna `version` nel `config.yaml`;
3. aggiungi una nota in `CHANGELOG.md`;
4. aggiorna `README.md` se cambiano installazione, configurazione o funzionalita';
5. crea commit, tag Git e push.

Convenzione versioni:

- patch, esempio `0.2.1`: fix piccoli;
- minor, esempio `0.3.0`: nuove funzionalita';
- major, esempio `1.0.0`: cambi incompatibili o prima versione stabile.

## Configurazione provider

La prima versione funziona anche senza chiavi API, usando dati demo. Per dati reali configura una sorgente prezzi/news nel file dell'add-on o tramite variabili ambiente:

- `DATA_MODE=live` oppure `DATA_MODE=demo`
- `NEWS_RSS_URLS` con URL RSS separati da virgola

`live` e' la modalita' predefinita per le nuove installazioni. Se un'installazione esistente mantiene `data_mode: demo` nelle opzioni Home Assistant, cambiala manualmente in `live` dalla pagina di configurazione dell'add-on.

## Persistenza

- I titoli aggiunti alla watchlist sono salvati in SQLite nel volume persistente `/data` dell'add-on.
- La watchlist resta disponibile dopo riavvio dell'add-on o di Home Assistant.
- Le notizie vengono lette dalle fonti configurate e mostrate in dashboard; la cache persistente delle news e' prevista per una versione successiva.

Provider reali da aggiungere nelle prossime iterazioni:

- Yahoo Finance non ufficiale / yfinance
- Alpha Vantage
- Finnhub
- Financial Modeling Prep
- RSS finanziari

## Struttura

```text
finance-trading-cockpit/
  config.yaml
  Dockerfile
  run.sh
  app/
    main.py
    models.py
    services/
    static/
home-assistant/
  dashboard-example.yaml
```
