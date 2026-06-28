# HA Trading Add-on

Dashboard/add-on sperimentale per seguire titoli finanziari, leggere notizie giornaliere e costruire segnali decisionali dentro Home Assistant.

> Nota: questo progetto non fornisce consulenza finanziaria. Gli score sono segnali informativi da verificare, non raccomandazioni automatiche di acquisto o vendita.

## Cosa contiene

- Add-on Home Assistant in `finance-trading-cockpit/`
- Backend Python FastAPI
- UI web leggera servita dall'add-on
- Watchlist persistente in SQLite nel volume privato `/data` dell'add-on
- Endpoint per aggiungere/rimuovere ticker
- Nessun ticker precompilato: la watchlist contiene solo i titoli che aggiungi tu
- Range grafico stile trading app: oggi, 1 settimana, 1 mese, 1 anno, totale
- Scala prezzi, fonte dati, link sorgente e ora aggiornamento visibili su ogni grafico
- Link tecnico all'endpoint Yahoo usato per generare ogni grafico
- Lettura rapida per ogni titolo con trend, variazione, copertura dati, notizie RSS e score
- Prezzi gestiti con doppio valore EUR/USD e cambio EUR/USD visibile
- Grafico selezionabile in EUR o USD
- Filtro rapido della watchlist
- Autocomplete ticker con ricerca simboli reali
- Quote e storico prezzi live tramite provider Yahoo Finance non ufficiale
- Notizie generali e notizie collegate ai singoli titoli, con fonte e link apribile
- Nessuna notizia generata: se non configuri RSS reali, la dashboard mostra che non ci sono notizie
- Performance calcolata sul range selezionato, separata dalla variazione giornaliera
- Le percentuali mostrate nelle card sono relative solo al range selezionato
- Audit dati per titolo con fonte, range, punti, primo/ultimo close e formula percentuale
- Layout responsive ottimizzato per mobile senza scroll orizzontale
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
- Il processo applicativo gira come utente non-root nel container.
- Le architetture supportate sono limitate a Raspberry Pi: `aarch64` e `armv7`.
- Le opzioni sensibili sono dichiarate esplicitamente come disabilitate nel `config.yaml`.
- L'add-on usa immagini GHCR precompilate per architettura e firmate con Cosign tramite GitHub Actions.

Nota sul punteggio sicurezza: dopo il push di un tag, attendi che il workflow `Publish add-on image` finisca prima di installare o aggiornare da Home Assistant. Il tag dell'immagine deve corrispondere alla `version` del `config.yaml`.

Per pubblicare una nuova versione:

1. modifica il codice;
2. aggiorna `version` nel `config.yaml`;
3. aggiungi una nota in `CHANGELOG.md`;
4. aggiungi la stessa nota in `finance-trading-cockpit/CHANGELOG.md`;
5. aggiorna `README.md` se cambiano installazione, configurazione o funzionalita';
6. crea commit, tag Git e push.

Convenzione versioni:

- patch, esempio `0.2.1`: fix piccoli;
- minor, esempio `0.3.0`: nuove funzionalita';
- major, esempio `1.0.0`: cambi incompatibili o prima versione stabile.

## Configurazione dati

L'add-on non richiede API key o abbonamenti. In modalita' `live` usa Yahoo Finance tramite endpoint pubblici non ufficiali per prezzi, ricerca simboli e storico.

- `DATA_MODE=live` oppure `DATA_MODE=demo`
- `NEWS_RSS_URLS` con URL RSS separati da virgola

`live` e' la modalita' predefinita per le nuove installazioni. Se un'installazione esistente mantiene `data_mode: demo` nelle opzioni Home Assistant, cambiala manualmente in `live` dalla pagina di configurazione dell'add-on.

Note sui dati:

- Yahoo Finance e' usato tramite endpoint pubblici non ufficiali.
- Il range `1W` della dashboard usa il range Yahoo `5d` con intervallo `15m`; la UI mostra sempre range e intervallo effettivi.
- Le notizie arrivano solo dagli RSS configurati in `NEWS_RSS_URLS`.
- Se non ci sono RSS o risultati pertinenti, non vengono generate notizie demo.
- La dashboard mostra sempre sorgente, ora di lettura, range, numero punti e formula usata per la percentuale.

## Persistenza

- I titoli aggiunti alla watchlist sono salvati in SQLite nel volume persistente `/data` dell'add-on.
- La watchlist resta disponibile dopo riavvio dell'add-on o di Home Assistant.
- Le notizie vengono lette dalle fonti configurate e mostrate in dashboard; la cache persistente delle news e' prevista per una versione successiva.

Fonti gratuite da valutare nelle prossime iterazioni:

- RSS ufficiali o editoriali affidabili.
- Calendari societari pubblici senza chiave, solo se tecnicamente stabili.
- Eventuali provider con piano gratuito, ma solo come opzione avanzata e mai obbligatoria.

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
