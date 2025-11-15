# Configuration Rapide - Client HTTP

## Pour votre configuration actuelle

Votre serveur tourne avec :
- `TRANSPORT=http`
- `HOST=0.0.0.0`
- `PORT=8000`

## URL à utiliser dans votre client MCP

```
http://localhost:8000/mcp
```

Ou depuis un autre ordinateur :

```
http://VOTRE_IP:8000/mcp
```

## Configuration Claude Desktop (exemple)

**Fichier:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "netbox": {
      "url": "http://localhost:8000/mcp",
      "transport": "http"
    }
  }
}
```

## Configuration pour un client MCP générique

```json
{
  "url": "http://localhost:8000/mcp",
  "transport": "http"
}
```

## Vérification de la connexion

```bash
curl http://localhost:8000/mcp
```

Vous devriez recevoir une réponse du serveur MCP.

## Protocole utilisé

Le serveur utilise **Streamable HTTP** selon la spécification MCP :
- https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http

Cela signifie :
- ✅ Un seul endpoint `/mcp` pour toutes les communications
- ✅ Support du streaming pour les réponses longues
- ✅ Compatible avec les clients HTTP standard
- ✅ Peut gérer plusieurs sessions simultanées

## Différence avec SSE

Le protocole **Streamable HTTP** est différent de **SSE (Server-Sent Events)** :

| Caractéristique | Streamable HTTP | SSE |
|----------------|-----------------|-----|
| Endpoint | `/mcp` | `/sse` + `/message` |
| Protocole | HTTP POST/GET avec streaming optionnel | Server-Sent Events |
| Bidirectionnel | Oui | Non (SSE = unidirectionnel) |
| Standard MCP | ✅ Oui (officiel) | Ancien standard |

Le Streamable HTTP est le standard recommandé par le protocole MCP moderne.
