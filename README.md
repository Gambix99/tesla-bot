# Tesla Model 3 RWD — Bot Telegram (versione GitHub, senza installazioni)

Questa versione gira interamente "nel cloud" tramite **GitHub Actions**:
non devi installare Python, non devi aprire terminali, non devi tenere
acceso il computer. Tutto si configura dal browser.

## Come funziona

GitHub Actions avvia lo script `main.py` ogni 15 minuti. Ad ogni
avvio: controlla se hai scritto un comando su Telegram e risponde;
inoltre, ogni 30 minuti, interroga davvero l'inventory Tesla e ti
avvisa se compare una nuova Model 3 a trazione posteriore. Lo stato
(quali auto ha già segnalato, a che punto era arrivato con i comandi)
viene salvato in `state.json`, che il workflow stesso aggiorna nel
repository ad ogni esecuzione.

⚠️ Differenza rispetto a un bot "sempre acceso": le risposte ai comandi
non sono istantanee, arrivano entro il giro successivo (di solito pochi
minuti). Le notifiche automatiche per le nuove auto restano comunque a
cadenza ~30 minuti come richiesto.

## 1. Crea un account GitHub

Vai su https://github.com e registrati (gratis, basta un'email).

## 2. Crea il bot Telegram e trova il tuo Chat ID

Sono gli stessi due passaggi della guida precedente:
1. Su Telegram cerca **BotFather**, scrivigli `/newbot`, segui le
   istruzioni e copia il **token** che ti dà alla fine.
2. Scrivi un messaggio al tuo nuovo bot (es. "ciao"), poi apri nel
   browser `https://api.telegram.org/bot<IL_TUO_TOKEN>/getUpdates`
   (sostituendo il token) e cerca `"chat":{"id":` seguito da un
   numero: quello è il tuo **Chat ID**.

## 3. Crea un nuovo repository

1. Su github.com clicca sul **+** in alto a destra → **New repository**.
2. Dai un nome (es. `tesla-bot`), lascialo **Public** (va benissimo,
   i tuoi dati sensibili non finiranno mai nel codice: li mettiamo nei
   "Secrets", vedi punto 5), spunta "Add a README file", poi **Create
   repository**.

## 4. Carica i file del progetto

1. Nella pagina del repository appena creato, clicca **Add file** →
   **Upload files**.
2. Trascina dentro **tutti i file e le cartelle** che trovi nello zip
   che ti ho preparato (compresa la cartella `.github` con dentro
   `workflows/tesla-bot.yml` — è importante che questa cartella
   arrivi intatta, con questo nome esatto).
3. Se il tuo browser non ti permette di trascinare la cartella
   `.github` (a volte succede), crea il file manualmente: clicca
   **Add file → Create new file**, e nel campo del nome scrivi
   `.github/workflows/tesla-bot.yml` (scrivendo lo slash GitHub crea le
   cartelle da solo), poi incolla dentro il contenuto del file
   `tesla-bot.yml` che trovi nello zip.
4. In fondo alla pagina clicca **Commit changes**.

## 5. Aggiungi i tuoi dati segreti (Secrets)

I dati sensibili (token, password) non vanno mai scritti nel codice:
li salviamo separatamente, cifrati da GitHub.

1. Nel repository vai su **Settings** (in alto) → nel menu a sinistra
   **Secrets and variables** → **Actions**.
2. Clicca **New repository secret** e crea questi due (obbligatori):
   - Nome `TELEGRAM_BOT_TOKEN`, valore: il token di BotFather
   - Nome `TELEGRAM_CHAT_ID`, valore: il tuo Chat ID
3. Se vuoi anche le email (opzionale), aggiungi allo stesso modo:
   `EMAIL_ENABLED` (valore `true`), `SMTP_HOST`, `SMTP_PORT`,
   `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `EMAIL_TO` — vedi la
   sezione email più sotto per i valori da usare con Gmail.

## 6. Dai al workflow il permesso di salvare lo stato

Serve un permesso esplicito perché il bot possa aggiornare
`state.json` nel repository ad ogni esecuzione:

1. Sempre in **Settings** → menu a sinistra **Actions** → **General**.
2. Scorri fino a **Workflow permissions**.
3. Seleziona **Read and write permissions**.
4. Clicca **Save**.

(Se salti questo passaggio, il bot funzionerà ma darà un errore ogni
volta che prova a salvare lo stato: niente di grave, ma è meglio
farlo subito.)

## 7. Prova il bot subito (senza aspettare)

1. Vai sul tab **Actions** in alto nel repository.
2. Se compare un banner "Workflows aren't being run on this
   repository", clicca per abilitarli.
3. Nella lista a sinistra clicca **Tesla Model 3 RWD Bot**.
4. Clicca il pulsante **Run workflow** (a destra) → **Run workflow**
   di conferma.
5. Aspetta 30-60 secondi, ricarica la pagina: dovresti vedere
   l'esecuzione con un segno di spunta verde ✅. Cliccaci sopra per
   vedere i log riga per riga se vuoi controllare cosa ha fatto.
6. Vai su Telegram e scrivi `/start` al tuo bot: se hai fatto tutto
   correttamente ti risponderà (al massimo entro il prossimo giro
   automatico, ma di solito quasi subito se hai appena lanciato il
   workflow a mano).

Da questo momento il bot gira da solo, per sempre, gratuitamente:
ogni 15 minuti si sveglia, controlla i tuoi comandi, e ogni 30 minuti
controlla anche l'inventory Tesla.

## Comandi Telegram

| Comando   | Cosa fa |
|-----------|---------|
| `/start`  | Messaggio di benvenuto |
| `/lista`  | Tutte le auto Tesla in pronta consegna in Italia |
| `/model3` | Solo le Model 3 a trazione posteriore |
| `/check`  | Forza un controllo al prossimo giro |

## Email (opzionale)

Con Gmail: attiva la verifica in due passaggi sul tuo account Google,
poi crea una "App Password" da
https://myaccount.google.com/apppasswords. Usa come secrets:
`EMAIL_ENABLED=true`, `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=465`,
`SMTP_USER`=il tuo indirizzo Gmail, `SMTP_PASSWORD`=l'app password
generata, `EMAIL_FROM`=il tuo indirizzo Gmail, `EMAIL_TO`=dove vuoi
ricevere le notifiche.

## Se qualcosa non funziona

- Vai sul tab **Actions**, apri l'ultima esecuzione (anche quelle con
  la ❌ rossa) e leggi i log: di solito l'errore è scritto chiaramente
  (es. "TELEGRAM_BOT_TOKEN" mancante = hai sbagliato il nome di un
  secret; errori 403 sul push = manca il permesso del punto 6).
- Se il bot smette di trovare auto pur non dando errori, il sito Tesla
  potrebbe aver cambiato qualcosa: scarica il repository sul computer
  (Code → Download ZIP) ed esegui `python debug_trims.py` in locale
  per ispezionare i dati grezzi restituiti da Tesla (richiede Python
  installato solo per questo controllo puntuale).
- GitHub disattiva automaticamente i workflow programmati se un
  repository resta del tutto inattivo per 60 giorni: dato che questo
  bot fa un commit ad ogni esecuzione, questo non dovrebbe mai
  succedere da solo. Se succedesse comunque, basta tornare sul tab
  Actions e riabilitarlo con un click.
