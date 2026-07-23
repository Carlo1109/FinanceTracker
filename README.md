# 💰 FinanceTracker

FinanceTracker è un'app desktop sviluppata in Python per gestire le proprie finanze personali in modo semplice, moderno e completamente offline.

## ✨ Funzionalità

- 📊 Dashboard con KPI
- 🥧 Grafico a torta delle spese
- 💳 Import estratti conto (al momento: Fineco, Revolut, PostePay, PayPal)
- ✍️ Inserimento movimenti manuali
- 🏷️ Gestione categorie e parole chiave
- 💾 Backup del database
- 🔒 Tutti i dati rimangono sul proprio PC

## 🖥️ Tecnologie

- Python
- Streamlit
- SQLite
- Plotly
- PyWebView

## 📷 Screenshot

### Dashboard

![Dashboard](screenshots/dashboard.png)

### Movimenti

![Movimenti](screenshots/movements.png)

### Gestione categorie

![Categorie](screenshots/categories.png)

### Importa dati

![Impostazioni](screenshots/import.png)


## 🚀 Download

Scarica l'ultima versione dalla sezione **Releases**.

## 📂 Dove vengono salvati i dati

Tutti i dati restano in locale sul PC. Nella cartella dell'app trovi:

- `finance_tracker.db` — database
- `categories.json` — categorie e parole chiave
- `backups/` — backup
- `logs/` — log dell'applicazione

| Sistema | Percorso |
|---|---|
| **Windows** | `%LOCALAPPDATA%\FinanceTracker\` |
| **Linux** | `~/.local/share/FinanceTracker/` |
| **macOS** | `~/Library/Application Support/FinanceTracker/` |

Su Windows il percorso completo tipico è:
`C:\Users\<utente>\AppData\Local\FinanceTracker\`

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT.
