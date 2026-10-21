# Verifica della consegna AISC

Verifica eseguita il **21 ottobre 2026** con Docker Desktop Linux/WSL2 e Docker Compose v5.0.0. Le modifiche sono limitate a `aisc-team`; non sono stati eseguiti commit o push e non sono stati eliminati volumi Docker.

## Configurazione

- Build locali di frontend, backend, worker e applicazioni collegate riuscite.
- `docker compose config --quiet` riuscito.
- Una sola porta pubblicata: `127.0.0.1:8092`, tramite Caddy. Nessun `container_name`, registry o Public Catalogue esterno richiesto.
- Verificate uguaglianza delle chiavi interne e delle credenziali broker tra backend e worker e propagazione di `AISC_PORT` agli URL frontend, issuer e redirect Keycloak.
- Entrypoint shell con fine riga LF; `.gitattributes` preserva il comportamento dopo checkout Windows.
- Dipendenze applicative installate dai lockfile; librerie AISC condivise compilate dai sorgenti locali.
- Nessun codice della dipendenza esterna `llm_eval` incluso nella repository; sorgenti e ambienti dei plugin sono scaricati nei volumi a runtime. Rimosse le copie superflue in `aisc-presentation/plugin_sources`.

## Installazione e accesso

Il progetto isolato `aisc-handoff-check` ha usato volumi nuovi per esercitare avvio, importazione del realm, migrazioni e creazione bucket. Terminati i test, è stato fermato con `docker compose -p aisc-handoff-check down`, senza `-v`: i volumi restano conservati.

La configurazione finale è stata avviata con successo anche con il comando esatto `docker compose up -d --build`, nel progetto predefinito `aisc-team-local`, inizialmente privo di container e volumi. Nessun `.env` o intervento manuale è stato necessario in questo avvio finale. Download, installazione dei sette plugin, migrazioni, bucket e importazione del realm sono terminati automaticamente. I servizi dotati di healthcheck risultano sani. Lo stack storico `aisc-team` resta separato.

Verifiche HTTP e browser effettuate:

- Webapp, Controls, Qualification e documento OpenAPI raggiungibili.
- Discovery OIDC con issuer pubblico corretto; token Keycloak ottenuto con le credenziali locali.
- Login interattivo in Chromium tramite tema Keycloak originale, ritorno alla webapp e sessione autenticata; nessun errore JavaScript non gestito.
- Il pulsante Public Catalogue è visibile ma disabilitato quando l'URL non è configurato; il pulsante per registrare i collegamenti plugin è visibile nei browser compatibili. La richiesta automatica di registrazione rimane disattivata senza catalogo configurato.
- API protette senza token rifiutate; API interne bloccate dal proxy pubblico.
- Tutti i sette pacchetti scoperti, abilitati in un progetto tramite API autenticata e relative definizioni di input lette correttamente.

## Plugin effettivamente verificati

| Pacchetto | Implementazioni importate e abilitate via API | Valutazione completa verificata |
| --- | --- | --- |
| `predictive-insights` | ClassificationPerformancePlugin, RegressionPerformancePlugin | **Sì, classificazione ONNX** |
| `data-monitor` | DataAnomalyPlugin, DataDriftPlugin | Non eseguita |
| `fairness-awareness` | ClassificationFairnessPlugin | Non eseguita |
| `aisc-plugin-langbite` | LangBiteEvaluationPlugin | Non eseguita; configurare modello/provider |
| `aisc-plugin-llm-eval` | LLMEvaluationPlugin, LLMEvaluationPluginForFinance, LLMEvaluationPluginForTranslation | Non eseguita; configurare modello/provider secondo le metriche |
| `aisc-plugin-strongreject` | StrongRejectPlugin | Non eseguita; configurare target e valutatore |
| `explitest-plugin` | ExpliTestPlugin | Non eseguita |

La valutazione Performance ha usato `testing_data.csv` e `rf_cls_model.onnx` del repository upstream alla revisione fissata nel manifest. I file dimostrativi gestiti con Git LFS sono stati letti dall'endpoint GitHub media, senza copiarli nella distribuzione. Gli input sono stati caricati su MinIO e la valutazione richiesta tramite API autenticata; RabbitMQ e Celery hanno eseguito il plugin nel suo ambiente preparato e registrato i risultati in PostgreSQL.

Esito: **Done**, 12 misure relative a 9 metriche, **Accuracy = 0,99**. Identificativo del primo test riuscito: `35290772-25c9-40f4-8b06-6a694c6b300a`. La valutazione è stata ripetuta con successo sull'installazione finale pulita: `f155633d-da1c-4b31-b256-cf9d73d15c07`, stesso esito e stessa accuracy. Anche login Chromium e abilitazione di tutti i sette pacchetti tramite API sono stati ripetuti con successo sull'istanza finale.

L'importazione e l'abilitazione non dimostrano il funzionamento di ogni configurazione upstream. Nessuna API key reale è stata usata. Chiamate LLM, valutatori fine-tuned, servizi di provider e funzionalità LLM di Qualification non sono stati provati con credenziali reali. La disponibilità tecnica di `llm_eval` non risolve la verifica dei relativi permessi di licenza.

## Ripetere i controlli

Attendere gli healthcheck del Compose, quindi:

```bash
python deploy/check_http.py
```

Questo controllo legge lo stato della piattaforma e dei plugin, senza creare progetti o valutazioni. Per verificare Chromium, installare le dipendenze di `e2e` e il browser Playwright nella cartella locale:

```bash
npm ci --prefix e2e
# Impostare PLAYWRIGHT_BROWSERS_PATH su una cartella dentro e2e, per esempio e2e/.browsers.
npx --prefix e2e playwright install chromium
node deploy/check_browser.cjs
```

I progetti e i file creati dalle prove riportate sopra sono stati rimossi dall'istanza locale. Lo script che generava la valutazione dimostrativa è stato rimosso dalla distribuzione. L'avvio non crea progetti, valutazioni o amministratori Django.

Il Compose usa direttamente `keycloak/aisc-realm.template.json`, senza una copia del realm o sostituzioni delle password applicative. Sono ripristinati gli accessi originali `user/user` e `admin/admin`; il valore originale di `registrationAllowed` è `false`. L'account master `local-admin` introdotto durante la preparazione è stato rimosso. Le modifiche mantenute riguardano avvio, dipendenze, rete e download/installazione dei plugin.

I controlli HTTP/browser leggono `AISC_PORT` e, facoltativamente, `AISC_TEST_PASSWORD`. Sono entrambi di sola lettura rispetto ai dati applicativi.

Dopo il ripristino sono riusciti il riavvio con il comando unico, il login browser con le credenziali originali, entrambi gli accessi `user/user` e `admin/admin`, e la scoperta dei sette pacchetti. Verificato dopo il riavvio e dopo i controlli: nessun progetto e nessun utente Django generato automaticamente.

## Interfaccia neutra

Rimossi nome del prodotto, loghi e favicon riconoscibili da barra superiore, home, login, titoli browser, intestazioni delle applicazioni collegate e footer PDF. La webapp usa l'etichetta generica `Workspace`; le etichette dei pacchetti non mostrano il prefisso del prodotto. Gli identificativi tecnici dei pacchetti e dell'autenticazione sono conservati per compatibilità, come le attribuzioni nei documenti di licenza.

Build riuscite e controllo Chromium superato su home, login, sessione autenticata, Controls e Qualification: nessun marchio originale nei testi e nelle immagini delle intestazioni controllate. Verificate anche la scoperta dei sette pacchetti, l'assenza di nuovi progetti e l'uguaglianza delle regole di autenticazione e degli account con il template originale.
