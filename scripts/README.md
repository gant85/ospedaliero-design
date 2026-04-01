# Confluence Documentation Manager

Strumento Python per gestire la documentazione tecnica su Confluence.

## Funzionalità

- ✅ **Upload completo**: Carica tutta la documentazione da `docs/`
- ✅ **Upload singolo file**: Carica o aggiorna un singolo file `.md` o `.puml`
- ✅ **Cancellazione pagina**: Elimina una pagina specifica
- ✅ **Cancellazione ricorsiva**: Elimina tutte le pagine figlie sotto una pagina parent
- ✅ **Configurazione flessibile**: CLI args > Env vars > Config file

## Configurazione

### Priorità Configurazione

1. **CLI arguments** (priorità massima)
2. **Environment variables** (`CONFLUENCE_*`)
3. **confluence_config.json** (priorità minima)

### File di Configurazione

`scripts/confluence_config.json`:

```json
{
  "default_base_url": "https://your-org.atlassian.net/wiki",
  "default_space_key": "YOUR_SPACE",
  "default_parent_id": "123456",
  "project_name": "Your Project",
  "docs_dir": "docs",
  "action": "upload",
  "single_file": null,
  "delete_dir": null
}
```

### Variabili d'Ambiente

```bash
# Obbligatorie
export CONFLUENCE_USERNAME="your-email@company.com"
export CONFLUENCE_API_TOKEN="your-api-token"

# Opzionali (usano default da config se non specificate)
export CONFLUENCE_BASE_URL="https://your-org.atlassian.net/wiki"
export CONFLUENCE_SPACE_KEY="YOUR_SPACE"
export CONFLUENCE_PARENT_ID="123456"
```

**Azure Pipeline**: Le variabili vengono lette automaticamente dalle secret variables della pipeline.

## Esempi d'Uso

### 1. Upload Completo (Default)

Carica tutta la documentazione da `docs/`:

```bash
python scripts/upload_confluence.py
```

Con configurazione custom:

```bash
python scripts/upload_confluence.py \
  --project-name "My Project" \
  --docs-dir "documentation" \
  --parent-id "514228239"
```

### 2. Upload Singolo File

Carica o aggiorna un singolo file:

```bash
# Upload markdown
python scripts/upload_confluence.py \
  --action upload-single \
  --file docs/ARCHITECTURE.md

# Upload diagramma PlantUML
python scripts/upload_confluence.py \
  --action upload-single \
  --file docs/diagrams/system-flow.puml
```

### 3. Cancellazione Pagina

Elimina una pagina specifica per ID:

```bash
python scripts/upload_confluence.py \
  --action delete \
  --page-id "514228239"
```

Elimina per titolo:

```bash
python scripts/upload_confluence.py \
  --action delete \
  --page-title "My Project - Architecture"
```

### 4. Cancellazione Ricorsiva

Elimina tutte le pagine figlie sotto una parent (con conferma interattiva):

```bash
python scripts/upload_confluence.py \
  --action delete-children \
  --page-id "514228239"
```

**⚠️ ATTENZIONE**: Questa azione elimina TUTTE le pagine figlie ricorsivamente!

In CI/CD (salta conferma):

```bash
CI=true python scripts/upload_confluence.py \
  --action delete-children \
  --page-id "514228239"
```

## Utilizzo in Azure DevOps Pipeline

### Pipeline YAML

```yaml
- stage: UpdateDocs
  displayName: 'Update Confluence Documentation'
  dependsOn: DeployProd
  condition: succeeded()
  jobs:
    - job: UploadConfluence
      displayName: 'Upload to Confluence'
      pool:
        vmImage: 'ubuntu-latest'
      steps:
        - task: UsePythonVersion@0
          inputs:
            versionSpec: '3.11'

        - script: |
            pip install requests
          displayName: 'Install Dependencies'

        # Upload all docs
        - script: |
            python scripts/upload_confluence.py
          displayName: 'Upload Documentation'
          env:
            CONFLUENCE_USERNAME: $(CONFLUENCE_USERNAME)
            CONFLUENCE_API_TOKEN: $(CONFLUENCE_API_TOKEN)
            CONFLUENCE_BASE_URL: $(CONFLUENCE_BASE_URL)
            CONFLUENCE_SPACE_KEY: $(CONFLUENCE_SPACE_KEY)
            CONFLUENCE_PARENT_ID: $(CONFLUENCE_PARENT_ID)

        # Or upload single file
        - script: |
            python scripts/upload_confluence.py \
              --action upload-single \
              --file docs/CHANGELOG.md
          displayName: 'Update Changelog Only'
          env:
            CONFLUENCE_USERNAME: $(CONFLUENCE_USERNAME)
            CONFLUENCE_API_TOKEN: $(CONFLUENCE_API_TOKEN)
```

### Pipeline Secret Variables

Configura in Azure DevOps → Pipelines → Variables:

| Nome                   | Valore                         | Tipo   |
| ---------------------- | ------------------------------ | ------ |
| `CONFLUENCE_USERNAME`  | your-email@company.com         | Secret |
| `CONFLUENCE_API_TOKEN` | your-atlassian-api-token       | Secret |
| `CONFLUENCE_BASE_URL`  | https://org.atlassian.net/wiki | Normal |
| `CONFLUENCE_SPACE_KEY` | YOUR_SPACE                     | Normal |
| `CONFLUENCE_PARENT_ID` | 514228239                      | Normal |

## Argomenti CLI Completi

```
--action {upload,upload-single,delete,delete-children}
    Azione da eseguire (default: upload)

--file FILE
    Path al file per upload-single (es: docs/ARCHITECTURE.md)

--page-id PAGE_ID
    ID pagina per delete/delete-children

--page-title PAGE_TITLE
    Titolo pagina per delete (alternativa a --page-id)

--docs-dir DOCS_DIR
    Directory documentazione (default: da config)

--parent-id PARENT_ID
    ID pagina parent Confluence

--space-key SPACE_KEY
    Chiave space Confluence

--project-name PROJECT_NAME
    Nome progetto per titoli pagine

--base-url BASE_URL
    URL base Confluence

--use-plantuml-macro
    Usa macro PlantUML nativa (richiede installazione)

--dry-run
    Test senza modifiche reali

--env-file ENV_FILE
    Path file .env custom
```

## Struttura Documentazione

Lo script supporta una struttura gerarchica:

```
docs/
├── README.md                    → "Project - Readme"
├── ARCHITECTURE.md              → "Project - Architecture"
├── DEVELOPMENT.md               → "Project - Development"
├── architecture/                → "Project - Architecture" (categoria)
│   ├── README.md               → Contenuto categoria
│   ├── 01-system-overview.md   → "Project - System Overview"
│   └── 02-data-flow.md         → "Project - Data Flow"
└── diagrams/
    ├── architecture.puml        → Embedded in pages
    └── system-flow.puml         → Embedded in pages
```

## Ottenere API Token

1. Vai su https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copia il token (verrà mostrato solo una volta)
4. Usalo come `CONFLUENCE_API_TOKEN`

## Troubleshooting

### "Space not found"

Verifica che `CONFLUENCE_SPACE_KEY` sia corretto:

- Vai su Confluence → Space Settings → Space details
- Copia la "Space Key"

### "Page not found"

Verifica che `CONFLUENCE_PARENT_ID` sia corretto:

- Apri la pagina parent su Confluence
- L'ID è nell'URL: `.../pages/514228239/...`

### "Authentication failed"

Verifica credenziali:

- Username deve essere l'email Atlassian
- API token deve essere valido (non scaduto)

### Encoding errors su Windows

Lo script usa UTF-8 automaticamente. Se vedi errori:

```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts/upload_confluence.py
```

## Log

I log vengono salvati in `confluence_upload.log` con encoding UTF-8.

```bash
# Visualizza ultimi 50 log
tail -n 50 confluence_upload.log

# Windows PowerShell
Get-Content confluence_upload.log -Tail 50
```
