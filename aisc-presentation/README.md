# AISC — demo per presentazione

AISC (AI Assessment Sandbox Configurator) permette di creare progetti, registrare modelli e dataset, configurare valutazioni tramite plugin, consultarne risultati e tracciare le operazioni nel registro di audit. Include anche Controls (checklist di conformità) e Qualification (qualificazione e schede dei sistemi AI).

Questa copia è autonoma rispetto alla cronologia Git originale. Tutte le sorgenti delle applicazioni e delle librerie condivise sono incluse come normali directory. Non servono submodule, credenziali GitHub, immagini private, Node.js o Python installati sul computer del collega.

## Requisiti

- Docker Desktop avviato, con container Linux e Docker Compose v2.
- Connessione Internet per il primo download di immagini e dipendenze pubbliche.
- Risorse sufficienti per diverse build contemporanee: consigliati almeno 8 GB di memoria assegnata a Docker e 20 GB liberi; la prima build può richiedere diversi minuti.
- Porta locale 8090 libera. Su Windows usa una cartella locale, evitando cartelle sincronizzate mentre Docker compila.

## Avvio con un comando

Clona il nuovo repository privato oppure estrai il suo archivio, apri un terminale nella directory contenente `docker-compose.yml` ed esegui:

```powershell
docker compose up --build -d --wait --wait-timeout 600
```

Non è necessario creare `.env`: Compose contiene valori dimostrativi coerenti, crea i database, applica le migrazioni e inizializza lo storage. I dati vengono salvati in nuovi volumi del progetto `aisc-presentation`. Il comando non riutilizza i volumi del progetto originale.

Apri **http://localhost:8090**. I servizi di database, storage e messaggistica non espongono porte sul computer host. L'interfaccia è esposta soltanto su localhost: questa è una demo locale, non una configurazione di produzione.

| Accesso | Utente | Password demo |
| --- | --- | --- |
| Interfaccia AISC | `demo` | `demo-presentation` |
| Interfaccia AISC con ruolo amministratore | `demo-admin` | `demo-presentation` |
| Django admin, `/admin/` | `demo-admin` | `demo-presentation` |
| Console Keycloak, `/auth/admin/` | `demo-admin` | `demo-presentation` |

Le password sono pubblici valori dimostrativi, non credenziali del progetto originale. Non esporre questa configurazione su Internet. Il backend crea l'account Django solo al primo avvio; Keycloak importa il realm solo quando non esiste.

Gli indirizzi utilizzano `localhost`: non sostituirlo con l'indirizzo IP del computer o con `127.0.0.1` durante il login.

| Funzione | URL |
| --- | --- |
| AISC | http://localhost:8090 |
| Controls | http://localhost:8090/controls |
| Qualification | http://localhost:8090/qualification |
| Documentazione API | http://localhost:8090/api/docs |
| Monitor valutazioni | http://localhost:8090/flower/ |
| Istruzioni plugin | http://localhost:8090/plugins-help |

## Plugin: installazione manuale

**Nessun plugin viene installato o scaricato automaticamente all'avvio.** La piattaforma parte con l'elenco dei plugin vuoto. Senza plugin puoi presentare l'interfaccia, creare progetti, gestire componenti, checklist e schede; per eseguire valutazioni occorre installare il plugin appropriato.

Le sorgenti dei sette plugin sono conservate in `plugin_sources/`, fuori dai contesti di build delle immagini di base e dalle directory caricate dalla piattaforma. I plugin non sono stati rimossi. Sono disponibili:

| Nome da passare al comando | Funzione | Dipendenze aggiuntive |
| --- | --- | --- |
| `performance` | Metriche di prestazione dei modelli predittivi | NumPy, pandas, scikit-learn, ONNX Runtime |
| `data-evaluation` | Data drift e anomalie nei dati | NumPy, SciPy, scikit-learn |
| `fairness` | Valutazione della fairness | NumPy, pandas, ONNX Runtime |
| `langbite` | Valutazione di sistemi linguistici | Backend LLM locali o servizi esterni, eventuali chiavi e modelli |
| `llm-eval` | Metriche euristiche e valutatori LLM | `llm_eval` upstream, dipendenze ML e possibili modelli/endpoint |
| `strongreject` | Valutazione di risposte e jailbreak | Servizi LLM/dataset; dipendenze pesanti per le opzioni avanzate |
| `explitest` | Spiegabilità dei modelli | ExpliTest upstream, SHAP, LIME, ONNX Runtime |

Per esempio, dopo avere avviato la piattaforma:

```powershell
docker compose run --rm plugin-installer performance
docker compose restart aisc-backend aisc-eval-worker
```

Il comando scarica esplicitamente le dipendenze su quel computer, in volumi Docker locali, e copia il plugin nella directory attiva. Poi aggiorna la lista dei plugin nell'interfaccia e aggiungilo al progetto. Non serve abilitare "Enable one-click installs". Il pulsante del catalogo apre una pagina locale di istruzioni.

L'installer manuale usa un ambiente di dipendenze condiviso per il caricamento dei plugin. Installa solo quelli necessari alla presentazione: combinazioni con vincoli incompatibili richiedono una verifica dedicata. Il worker prepara inoltre un ambiente isolato per ogni valutazione. Non tutti i plugin sono garantiti su ogni architettura o senza risorse GPU.

### Dipendenza esterna `llm_eval`

Il plugin AISC `aisc-plugin-llm-eval` è incluso con la sua licenza Apache-2.0. Il codice della dipendenza distinta **`llm_eval` non è incluso nel repository o nelle immagini di base**, e l'avvio normale non lo scarica.

Origine: https://github.com/serval-uni-lu/llm_eval

Revisione dichiarata: `46b3e4081b83e673f2c488e742ae34af8471df69`.

Il README upstream documenta installazione ed esempi d'uso, ma alla verifica del 21 ottobre 2026 non è stata trovata una licenza esplicita. Questa distribuzione non assegna a quella dipendenza una licenza Apache o MIT. Prima di installarla e usarla per la presentazione verifica con i titolari i permessi applicabili. Il riferimento esterno non risolve automaticamente la questione dei permessi d'uso.

Se disponi dei permessi necessari, il comando manuale è:

```powershell
docker compose run --rm plugin-installer llm-eval
docker compose restart aisc-backend aisc-eval-worker
```

Il download avviene direttamente dal repository originale. Codice e pacchetti installati restano nei volumi locali: non aggiungerli a Git e non redistribuirli in archivi, cache, ambienti Python o immagini. Non modificare i Dockerfile per installare questa dipendenza in fase di build senza chiarirne i diritti di distribuzione. Un'immagine contenente la dipendenza sarebbe una distribuzione distinta dal solo riferimento Git.

L'installazione e l'esecuzione di questo plugin non sono prerequisiti per avviare AISC. Possono richiedere download ML di grandi dimensioni, modelli con proprie condizioni di accesso, GPU oppure endpoint e chiavi provider personali. Il plugin e l'API upstream possono evolvere separatamente: l'esecuzione LLM deve essere verificata con il modello scelto.

## Qualification e servizi LLM

La gestione delle schede e il renderer PDF sono inclusi. Le funzioni che chiamano un provider LLM richiedono una chiave personale; senza chiave quelle richieste non possono produrre risposte. Non è inclusa una risposta AI simulata.

Per configurarle, copia `.env.example` in `.env`, inserisci solo la chiave necessaria e ripeti il comando di avvio. `.env` è escluso da Git. Non inserire segreti nelle variabili frontend `VITE_*`, visibili nel browser. Non includere `.env` negli archivi da condividere.

## Arresto e riavvio

```powershell
docker compose stop
docker compose start --wait
```

Per rimuovere soltanto container e rete di questa demo, mantenendo i dati:

```powershell
docker compose down
```

Per ricrearli, ripeti il comando iniziale. Non usare comandi globali `docker system prune` o cancellazioni di volumi: possono coinvolgere altri progetti.

## Problemi comuni

- **Docker non risponde:** avvia Docker Desktop e verifica che siano selezionati i container Linux.
- **Build lenta o interrotta:** verifica spazio, memoria e accesso a Docker Hub, GHCR, PyPI e npm. Puoi ridurre il parallelismo con `$env:COMPOSE_PARALLEL_LIMIT=1` in PowerShell prima di ripetere il comando.
- **Porta occupata:** prima del primo avvio imposta `$env:AISC_PORT=8091` e usa `http://localhost:8091`. Mantieni lo stesso valore per i comandi successivi. Se cambi porta dopo il primo login, devi aggiornare redirect URI e web origin del client `aisc-webapp` nella console Keycloak: il realm esistente non viene sovrascritto.
- **Servizio non pronto:** esegui `docker compose ps` e `docker compose logs --tail 100 NOME-SERVIZIO`. Alcuni servizi di inizializzazione terminano correttamente con codice 0.
- **Elenco plugin vuoto:** è previsto al primo avvio; segui l'installazione manuale. Dipendenze mancanti possono impedire il rilevamento del plugin.
- **Errore di un provider AI:** configura una chiave valida, controlla modello e disponibilità dell'endpoint. La demo non include account o crediti di servizi esterni.
- **Windows / errori negli script Linux:** `.gitattributes` forza LF per gli script; non salvarli con terminazioni CRLF. Non servono script Bash sull'host.
- **Archivio anziché clone:** scarica soltanto i file della distribuzione, senza `.env`, log, volumi o cache locali.

## Architettura e dipendenze

Caddy è l'unico ingresso HTTP. La webapp React/Vite usa il backend Django e Keycloak per il login. PostgreSQL conserva i dati delle tre applicazioni e di Keycloak in database separati. MinIO conserva file e artefatti; RabbitMQ e Redis supportano i job Celery; immudb conserva il registro di audit; Flower mostra i job. Controls e Qualification sono applicazioni Next.js con renderer PDF dedicati; Qualification ha un sidecar LiteLLM.

Le immagini applicative vengono costruite da queste sorgenti, usando le librerie locali in `shared/`. Il primo avvio richiede registri e package index pubblici; non è un'installazione offline. I plugin opzionali ExpliTest e LLM Eval hanno dipendenze Git upstream esplicite; altri plugin possono richiedere modelli o API esterne. Nessun accesso SSH a repository privati è necessario per l'avvio di base.

## Provenienza, anonimizzazione e licenze

Sono stati esclusi cronologia Git, metadati dei sottomoduli, configurazioni IDE personali, file ambiente originali, dataset/modelli dimostrativi non necessari e log. Sono stati sostituiti configurazione di rete, identità demo, logo e riferimenti all'infrastruttura privata. Non vengono importati database, utenti o volumi del computer originale.

Licenze, copyright e attribuzioni originali sono conservati: l'anonimizzazione non elimina gli obblighi di attribuzione. Applicazioni e librerie condivise usano Apache-2.0; i plugin inclusi usano Apache-2.0 o MIT secondo i rispettivi file LICENSE/NOTICE. La licenza dei componenti inclusi non si estende automaticamente alle loro dipendenze. Conserva questi documenti anche nel repository privato.

Le modifiche per la presentazione sono descritte in `CHANGES.md`. I risultati effettivi delle verifiche sono in `VERIFICATION.md`. Questa configurazione è destinata a una presentazione locale, senza dati riservati.