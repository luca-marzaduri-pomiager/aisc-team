# Installazione locale

La piattaforma permette di caricare modelli e dataset, configurare i plugin ed eseguire valutazioni. Questa distribuzione mantiene frontend, backend Django, worker Celery e download automatico dei plugin originali. Include anche Controls e Qualification con i relativi servizi PDF e LLM. Il Public Catalogue esterno non viene avviato né richiesto; il relativo pulsante è visibile ma disabilitato quando `CATALOG_URL` è vuoto; gestione, configurazione e utilizzo dei plugin interni restano disponibili.

## Requisiti

- Git, Docker Engine/Docker Desktop con container Linux e Docker Compose v2 recente (`docker compose version`).
- Connessione Internet per immagini, pacchetti Python/npm e repository GitHub pubblici.
- Consigliati almeno 16 GB di RAM assegnati a Docker e 25 GB liberi: alcuni plugin scaricano dipendenze ML consistenti. Il primo avvio può richiedere parecchi minuti.
- Porta locale 8092 libera. Tutti gli altri servizi comunicano tramite la rete Docker; non richiedono porte host dedicate.

## Clonazione e avvio

Clonare la repository GitHub consegnata dal proprietario:

```bash
git clone <URL_GITHUB_DI_QUESTA_REPOSITORY> aisc-team
cd aisc-team
docker compose up -d --build
```

Non servono submodule, copie dei repository dei plugin o un file `.env`: i valori dimostrativi sono già definiti nel Compose. Le applicazioni e le librerie condivise vengono compilate dai sorgenti inclusi. Il downloader originale scarica i sette repository predefiniti nei volumi Docker; le revisioni sono fissate in [deploy/plugins.json](deploy/plugins.json). Le dipendenze applicative usano i lockfile; quelle transitive dei plugin possono ancora variare secondo i vincoli upstream.

Attendere che il downloader termini e che i servizi risultino sani:

```bash
docker compose ps -a
docker compose logs -f plugin-downloader
```

Un errore di download/installazione viene segnalato nei log e impedisce l'avvio del backend: nessun plugin predefinito viene escluso silenziosamente. Corretto il problema di rete o di dipendenze, ripetere il comando di avvio. I plugin già installati vengono riutilizzati.

Aprire **http://localhost:8092** nel browser (usare `localhost`, coerente con gli URL SSO).

| Accesso | Utente | Password locale iniziale |
| --- | --- | --- |
| Webapp, utente originale | `user` | `user` |
| Webapp, amministratore originale | `admin` | `admin` |
| Console Keycloak, realm master | `admin` | `admin` |

Il realm e gli utenti sono quelli del template originale, senza progetti precompilati né creazione automatica di utenti Django. La registrazione è disabilitata nel template upstream originale (`registrationAllowed: false`). Le password degli utenti applicativi si gestiscono nella console Keycloak. Il login usa Keycloak e redirect sullo stesso indirizzo della webapp. Il backend verifica issuer pubblico e chiavi JWKS sulla rete interna. Credenziali solo dimostrative: il proxy ascolta esclusivamente su loopback. Non usare questa configurazione per pubblicare un servizio Internet.

| Percorso | Servizio |
| --- | --- |
| `/` | Webapp AISC |
| `/api/docs` | Documentazione API |
| `/admin/` | Django admin |
| `/auth/admin/` | Console Keycloak |
| `/flower/` | Monitor Celery |
| `/controls` | Controls |
| `/qualification` | Qualification |

I percorsi `/api/v1/internal/*` sono bloccati dal proxy; il worker li raggiunge direttamente sulla rete Docker.

## Configurazione facoltativa

Per personalizzare i valori, copiare `env.example` in `.env` oppure impostare variabili nell'ambiente prima del comando di avvio. Non versionare `.env`. Tutte le credenziali dimostrative sono sostituibili senza modificare il codice.

- `AISC_PORT`: unica porta host. Cambiandola si aggiornano automaticamente URL frontend, backend, issuer e redirect Keycloak. Se 8092 è occupata, scegliere una porta libera in `.env` e ripetere `docker compose up -d --build`.
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `S3_USER`, `S3_PASSWORD`, `RABBITMQ_USERNAME`, `RABBITMQ_PASSWORD`, `IMMUDB_ADMIN_PASSWORD`: credenziali infrastruttura. Per i valori inseriti in URL di connessione usare caratteri compatibili con gli URL.
- `DJANGO_SECRET_KEY` e `INTERNAL_API_KEY`: chiavi locali condivise automaticamente da backend e worker.
- `KEYCLOAK_ADMIN`, `KEYCLOAK_ADMIN_PASSWORD`: amministratore iniziale della console Keycloak. Gli utenti applicativi restano quelli del realm originale.
- `MISTRAL_API_KEY`, `ANTHROPIC_API_KEY`, `QUALIFICATION_LLM_MODEL`: servizio LLM di Qualification; senza chiave le richieste al provider non possono funzionare.

Le credenziali e gli URL del realm vengono inizializzati al primo avvio. Con dati già esistenti, modificare utenti e redirect nella console Keycloak; cambiare `.env` non sovrascrive utenti/database già inizializzati. Non eliminare volumi per aggiornare le password. Cambiare `DJANGO_SECRET_KEY` impedisce la lettura dei segreti dei plugin precedentemente cifrati.

## Plugin predefiniti

| Repository scaricato | Pacchetto | Requisiti per una valutazione |
| --- | --- | --- |
| `aisc-plugin-performance` | `predictive-insights` | Modello ONNX e dataset tabellare compatibile; nessuna API key |
| `aisc-plugin-data-evaluation` | `data-monitor` | Dataset di riferimento/test e configurazione delle colonne; nessuna API key |
| `aisc-plugin-fairness` | `fairness-awareness` | Modello/dataset e attributi sensibili da configurare; nessuna API key |
| `aisc-plugin-langbite` | `aisc-plugin-langbite` | Dataset/prompt, modello e provider scelto: API key o servizio/modello locale secondo configurazione |
| `aisc-plugin-llm-eval` | `aisc-plugin-llm-eval` | Dipendenza esterna `llm_eval`; metriche LLM judge richiedono un endpoint/modello e, se previsto, una API key |
| `aisc-plugin-strongreject` | `aisc-plugin-strongreject` | Dataset e configurazione target/judge; normalmente endpoint e API key. Gli extra del valutatore fine-tuned non sono installati dal percorso standard upstream |
| `aisc-plugin-explitest` | `explitest-plugin` | Modello e dataset compatibili, configurazione delle feature; eventuali requisiti del metodo scelto |

I pacchetti sono disponibili nella gestione interna dei plugin: creare un progetto, abilitare le implementazioni desiderate e configurarne input e parametri. API key e endpoint dei plugin vanno configurati negli input/impostazioni di progetto previsti dal plugin. Installazione/importazione riuscita non equivale a una valutazione verificata per ogni modello e provider.

### Dipendenza esterna di llm-eval

Il wrapper `aisc-plugin-llm-eval` è mantenuto tra i sette download. Il codice della dipendenza [serval-uni-lu/llm_eval](https://github.com/serval-uni-lu/llm_eval) **non è incluso nella repository**: viene scaricato durante l'installazione nel volume Docker, alla revisione indicata nel manifest. Il download tecnico non risolve eventuali limiti di licenza e non attribuisce diritti di redistribuzione. Verificare separatamente le condizioni della dipendenza e dei modelli/provider prima di ridistribuire immagini o usarli oltre la prova locale. Non considerare la licenza del wrapper come autorizzazione per tutte le dipendenze.

## Arresto, riavvio e diagnostica

```bash
# Arrestare conservando container e dati
docker compose stop
# Riavviare
docker compose start
# Applicare modifiche e ricostruire
docker compose up -d --build
# Rimuovere solo container/rete del progetto conservando tutti i volumi
docker compose down
# Log dei servizi applicativi
docker compose logs --tail=100 aisc-backend aisc-eval-worker keycloak
```

Non usare `down -v` se si vogliono conservare i dati. Il progetto predefinito si chiama `aisc-team-local`, separato dal precedente stack locale `aisc-team`. Non sono necessari nomi fissi dei container né reti o volumi esterni. Per eseguire copie indipendenti usare `docker compose -p <nome> ...` e porte `AISC_PORT` diverse. Lo stack principale non usa i vecchi file Compose di sviluppo/staging.

I sorgenti dei plugin vengono scaricati solo a runtime. `def_plugins/` è una cartella locale ignorata da Git e dal contesto di build; non serve consegnarla. Le vecchie copie in `aisc-presentation/plugin_sources/` sono state rimosse dalla distribuzione.

## Verifiche

Gli esiti della verifica di questa consegna sono riportati in [docs/HANDOFF_VALIDATION.md](docs/HANDOFF_VALIDATION.md). I test usano un progetto Compose separato e volumi nuovi, senza eliminare quelli esistenti.

Per sviluppo e architettura vedere [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md). Licenze e avvisi originali restano nei rispettivi file `LICENSE.md` e `NOTICE.md`.
