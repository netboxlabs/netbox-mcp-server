# Configuration du Client MCP

Ce document explique comment configurer votre client MCP pour se connecter au serveur NetBox MCP.

## Option 1: Transport STDIO (Recommandé pour Claude Desktop)

Le transport STDIO est le plus simple et le plus couramment utilisé avec Claude Desktop.

### Configuration `.env`

```env
NETBOX_URL=https://vnnw3287.cloud.netboxapp.com/
NETBOX_TOKEN=votre_token_ici
TRANSPORT=stdio
VERIFY_SSL=false
LOG_LEVEL=DEBUG
```

### Configuration Claude Desktop

Ajoutez ceci dans votre fichier de configuration Claude Desktop :

**Sur macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Sur Windows:** `%APPDATA%/Claude/claude_desktop_config.json`
**Sur Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "netbox": {
      "command": "/chemin/vers/netbox-mcp-server/golang/netbox-mcp-server",
      "env": {
        "NETBOX_URL": "https://vnnw3287.cloud.netboxapp.com/",
        "NETBOX_TOKEN": "votre_token_ici",
        "TRANSPORT": "stdio",
        "VERIFY_SSL": "false",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Remplacez `/chemin/vers/netbox-mcp-server/golang/netbox-mcp-server` par le chemin absolu vers votre binaire.

## Option 2: Transport HTTP (Streamable HTTP/MCP)

Le transport HTTP Streamable permet aux clients de se connecter via HTTP, utile pour les déploiements distants ou les clients web. Il utilise le protocole Streamable HTTP du MCP sur l'endpoint `/mcp`.

### Configuration `.env`

```env
NETBOX_URL=https://vnnw3287.cloud.netboxapp.com/
NETBOX_TOKEN=votre_token_ici
TRANSPORT=http
HOST=0.0.0.0
PORT=8000
VERIFY_SSL=false
LOG_LEVEL=DEBUG
```

### Lancement du serveur

```bash
./netbox-mcp-server
```

Le serveur démarre et affiche :

```
[DEBUG] Starting HTTP transport (Streamable HTTP) on 0.0.0.0:8000
[DEBUG] Streamable HTTP server listening on: http://0.0.0.0:8000
[DEBUG] MCP endpoint: http://0.0.0.0:8000/mcp
[DEBUG] Use this URL in your MCP client: http://0.0.0.0:8000/mcp
```

### Configuration du client MCP (HTTP)

Pour un client MCP qui supporte le protocole Streamable HTTP :

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

Ou depuis un autre ordinateur (remplacez `localhost` par l'adresse IP du serveur) :

```json
{
  "mcpServers": {
    "netbox": {
      "url": "http://192.168.1.100:8000/mcp",
      "transport": "http"
    }
  }
}
```

### Endpoint disponible

- **MCP Endpoint:** `http://HOST:PORT/mcp` - Endpoint unique pour toutes les communications MCP (requêtes, notifications, streaming)

## Quelle option choisir ?

### Utilisez STDIO si :
- ✅ Vous utilisez Claude Desktop
- ✅ Le serveur s'exécute sur la même machine que le client
- ✅ Vous voulez la configuration la plus simple
- ✅ Vous n'avez pas besoin d'accès réseau

### Utilisez HTTP (Streamable) si :
- ✅ Vous voulez accéder au serveur depuis un autre ordinateur
- ✅ Vous utilisez un client web
- ✅ Vous avez plusieurs clients qui doivent se connecter au même serveur
- ✅ Vous voulez exposer le serveur sur le réseau

## Sécurité

### ⚠️ VERIFY_SSL=false

Dans votre configuration, vous avez `VERIFY_SSL=false`. Ceci désactive la vérification des certificats SSL. **Ne faites ceci qu'en développement/test !**

Pour la production, utilisez toujours `VERIFY_SSL=true` avec un certificat SSL valide.

### 🔒 Protection du Token

- Ne commitez jamais votre `.env` dans git
- Utilisez des permissions de fichiers restrictives : `chmod 600 .env`
- Pour la production, utilisez des secrets managés (vault, secrets manager, etc.)

### 🌐 Exposition réseau (MODE HTTP)

Si vous utilisez `HOST=0.0.0.0`, le serveur écoute sur **toutes** les interfaces réseau. Cela signifie que n'importe qui sur votre réseau peut potentiellement accéder au serveur.

**Pour plus de sécurité en mode HTTP :**

1. Utilisez `HOST=127.0.0.1` si vous n'avez besoin que d'un accès local
2. Mettez en place un reverse proxy (nginx, Apache) avec HTTPS
3. Utilisez un firewall pour limiter l'accès
4. Ajoutez une authentification au niveau du reverse proxy

## Test de la connexion

### Test STDIO

1. Lancez le serveur : `./netbox-mcp-server`
2. Vérifiez les logs pour confirmer le chargement de la configuration
3. Ouvrez Claude Desktop - le serveur NetBox devrait apparaître dans la liste des MCP

### Test HTTP

1. Lancez le serveur : `./netbox-mcp-server`
2. Vérifiez que le serveur écoute :
   ```bash
   curl http://localhost:8000/mcp
   ```
3. Vous devriez recevoir une réponse du serveur MCP

## Dépannage

### Erreur "Configuration error: NETBOX_URL is required"

Le fichier `.env` n'est pas chargé ou les variables ne sont pas définies.

**Solution :**
- Vérifiez que `.env` est dans le même répertoire que le binaire
- Vérifiez le contenu du fichier `.env`
- Assurez-vous qu'il n'y a pas d'espaces autour du `=`

### Erreur de connexion au serveur NetBox

**Solution :**
- Vérifiez que `NETBOX_URL` est correct
- Vérifiez que `NETBOX_TOKEN` est valide
- Si certificat auto-signé, utilisez `VERIFY_SSL=false` (dev uniquement)

### Le serveur HTTP ne démarre pas

**Solution :**
- Vérifiez que le port n'est pas déjà utilisé : `lsof -i :8000`
- Changez le port dans `.env` : `PORT=8001`
- Sur Linux, les ports < 1024 nécessitent des privilèges root

## Exemple complet pour votre cas

D'après vos logs, vous utilisez actuellement :

```env
NETBOX_URL=https://vnnw3287.cloud.netboxapp.com/
NETBOX_TOKEN=votre_token
TRANSPORT=http
HOST=0.0.0.0
PORT=8000
VERIFY_SSL=false
LOG_LEVEL=DEBUG
```

### Si vous voulez utiliser Claude Desktop (recommandé)

Changez juste une ligne dans `.env` :

```env
TRANSPORT=stdio
```

Puis configurez Claude Desktop comme expliqué ci-dessus.

### Si vous voulez vraiment utiliser HTTP

Gardez votre `.env` actuel et connectez votre client MCP à :

```
http://localhost:8000/mcp
```

Ou depuis un autre PC sur votre réseau :

```
http://VOTRE_IP:8000/mcp
```
