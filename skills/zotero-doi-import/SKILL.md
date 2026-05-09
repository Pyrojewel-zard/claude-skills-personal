---
name: zotero-doi-import
description: "Import papers by DOI into Zotero and organize them into collections. Uses Zotero Web API from the zotero-llm-classify project. Trigger: user provides DOI(s) and wants to add them to Zotero collections."
version: 0.1.0
---

# Zotero DOI Import Skill

Import papers by DOI into Zotero, create collections as needed, and organize papers.

## Prerequisites

Set environment variables:
```bash
export ZOTERO_USER_ID='your_user_id'
export ZOTERO_API_KEY='your_api_key'
```

## Workflow

### 1. Import single DOI to collection
```bash
python import_doi.py --doi "10.1109/TMTT.2023.1234567" --collection "RF Amplifiers"
```

### 2. Import multiple DOIs to collection
```bash
python import_doi.py --doi "10.1109/TMTT.2023.111" --doi "10.1109/TMTT.2023.222" --collection "RF Filters"
```

### 3. Import from text file (one DOI per line)
```bash
python import_doi.py --file dois.txt --collection "LNA Design"
```

### 4. Create collection first, then import
```bash
python import_doi.py --doi "10.xxxx/xxx" --collection "New Category/Subcategory" --create-collection
```

## How it works

1. **DOI import**: Uses Zotero Web API `POST /users/{userId}/items` with `{"itemType":"journalArticle","DOI":"..."}` to create items via magic URL resolution
2. **Collection lookup**: Searches existing collections by name, gets the collection key
3. **Collection creation**: If collection doesn't exist and `--create-collection` is set, creates it (supports nested: `Parent/Child`)
4. **Add to collection**: Patches the item to add the collection key

## API Details (from zotero-llm-classify/cli.py)

```python
from cli import ZoteroManager

zotero = ZoteroManager()

# Import by DOI - Zotero auto-resolves metadata
url = f"{zotero.base_url}/users/{zotero.user_id}/items"
payload = [{
    "itemType": "journalArticle",
    "DOI": "10.xxxx/xxx"
}]
response = zotero.session.post(url, headers=zotero.headers, json=payload)

# Get all collections
collections = zotero.get_collections()

# Create collection
zotero.create_collection({"name": "New Collection", "parentCollection": ""})

# Add item to collection
zotero.add_item_to_collection(item_key, collection_key)
```

## Rate Limiting

- Zotero API: 200 requests/5 minutes for anonymous, higher for authenticated
- Default retry: 5 times with exponential backoff (configured in ZoteroManager)
- Batch imports should add 0.5s delay between items

## Notes

- DOI import relies on Zotero's magic URL resolution - not all DOIs resolve perfectly
- Verify imported item metadata after import
- Collection names are case-sensitive matches
- Sub-collections require parent collection to exist first (use `Parent/Child` syntax with `--create-collection`)
