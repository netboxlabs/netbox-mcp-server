# Opérations CRUD avec NetBox MCP Server

Ce guide explique comment utiliser les opérations de création, lecture, mise à jour et suppression (CRUD) avec le serveur MCP NetBox.

## 📖 Vue d'ensemble

Le serveur MCP NetBox supporte maintenant les opérations suivantes :

- **CREATE** : Créer de nouveaux objets (`netbox_create_object`)
- **READ** : Lire des objets existants (`netbox_get_objects`, `netbox_get_object_by_id`, `netbox_search_objects`)
- **UPDATE** : Mettre à jour des objets existants (`netbox_update_object`)
- **DELETE** : Supprimer des objets (`netbox_delete_object`)

## 🔐 Permissions requises

Pour utiliser les opérations d'écriture (CREATE, UPDATE, DELETE), votre token NetBox doit avoir les permissions appropriées :

- **Lecture seule** : Permission `view` sur les objets
- **Création** : Permission `add` sur les objets
- **Modification** : Permission `change` sur les objets
- **Suppression** : Permission `delete` sur les objets

## 📝 Exemples d'utilisation

### CREATE - Créer un objet

#### Créer un site

```json
{
  "tool": "netbox_create_object",
  "arguments": {
    "object_type": "dcim.site",
    "data": {
      "name": "Paris Datacenter",
      "slug": "paris-dc",
      "status": "active",
      "region": 1,
      "description": "Notre datacenter principal à Paris"
    }
  }
}
```

#### Créer un appareil

```json
{
  "tool": "netbox_create_object",
  "arguments": {
    "object_type": "dcim.device",
    "data": {
      "name": "switch-paris-01",
      "device_type": 5,
      "device_role": 2,
      "site": 3,
      "status": "active"
    }
  }
}
```

#### Créer une adresse IP

```json
{
  "tool": "netbox_create_object",
  "arguments": {
    "object_type": "ipam.ipaddress",
    "data": {
      "address": "192.168.1.100/24",
      "status": "active",
      "dns_name": "server01.example.com",
      "description": "Serveur web principal"
    }
  }
}
```

#### Créer un VLAN

```json
{
  "tool": "netbox_create_object",
  "arguments": {
    "object_type": "ipam.vlan",
    "data": {
      "vid": 100,
      "name": "Production",
      "status": "active",
      "site": 3
    }
  }
}
```

### UPDATE - Mettre à jour un objet

#### Mettre à jour le statut d'un appareil

```json
{
  "tool": "netbox_update_object",
  "arguments": {
    "object_type": "dcim.device",
    "object_id": 123,
    "data": {
      "status": "offline",
      "comments": "Maintenance programmée"
    }
  }
}
```

#### Modifier une adresse IP

```json
{
  "tool": "netbox_update_object",
  "arguments": {
    "object_type": "ipam.ipaddress",
    "object_id": 456,
    "data": {
      "dns_name": "new-hostname.example.com",
      "description": "Mise à jour du hostname"
    }
  }
}
```

#### Mettre à jour un site

```json
{
  "tool": "netbox_update_object",
  "arguments": {
    "object_type": "dcim.site",
    "object_id": 3,
    "data": {
      "description": "Datacenter principal - Mis à jour",
      "physical_address": "123 Rue de la Paix, 75001 Paris"
    }
  }
}
```

### DELETE - Supprimer un objet

#### Supprimer une adresse IP

```json
{
  "tool": "netbox_delete_object",
  "arguments": {
    "object_type": "ipam.ipaddress",
    "object_id": 789
  }
}
```

**Réponse :**
```json
{
  "success": true,
  "message": "Object ipam.ipaddress with ID 789 deleted successfully"
}
```

#### Supprimer un appareil

```json
{
  "tool": "netbox_delete_object",
  "arguments": {
    "object_type": "dcim.device",
    "object_id": 123
  }
}
```

⚠️ **Attention** : La suppression est irréversible !

## 🔄 Workflow complet : Créer et configurer un appareil

### Étape 1 : Rechercher le site

```json
{
  "tool": "netbox_get_objects",
  "arguments": {
    "object_type": "dcim.site",
    "filters": {"name__ic": "paris"},
    "fields": ["id", "name"]
  }
}
```

### Étape 2 : Créer l'appareil

```json
{
  "tool": "netbox_create_object",
  "arguments": {
    "object_type": "dcim.device",
    "data": {
      "name": "router-paris-02",
      "device_type": 10,
      "device_role": 1,
      "site": 3,
      "status": "planned"
    }
  }
}
```

### Étape 3 : Activer l'appareil

```json
{
  "tool": "netbox_update_object",
  "arguments": {
    "object_type": "dcim.device",
    "object_id": 124,
    "data": {
      "status": "active",
      "comments": "Mis en production"
    }
  }
}
```

## 🎯 Bonnes pratiques

### 1. Vérifier avant de supprimer

Toujours récupérer l'objet avant de le supprimer pour confirmer que c'est le bon :

```json
// 1. Récupérer l'objet
{
  "tool": "netbox_get_object_by_id",
  "arguments": {
    "object_type": "dcim.device",
    "object_id": 123,
    "fields": ["id", "name", "site"]
  }
}

// 2. Vérifier les informations, puis supprimer
{
  "tool": "netbox_delete_object",
  "arguments": {
    "object_type": "dcim.device",
    "object_id": 123
  }
}
```

### 2. Mise à jour partielle

Vous n'avez pas besoin de fournir tous les champs lors d'une mise à jour, seulement ceux qui changent :

```json
{
  "tool": "netbox_update_object",
  "arguments": {
    "object_type": "dcim.device",
    "object_id": 123,
    "data": {
      "status": "offline"
      // Autres champs restent inchangés
    }
  }
}
```

### 3. Utiliser les ID pour les relations

Pour les champs relationnels (foreign keys), utilisez l'ID de l'objet lié :

```json
{
  "tool": "netbox_create_object",
  "arguments": {
    "object_type": "dcim.interface",
    "data": {
      "device": 123,        // ID de l'appareil
      "name": "GigabitEthernet0/1",
      "type": "1000base-t"
    }
  }
}
```

### 4. Vérifier les champs requis

Consultez la documentation NetBox API pour connaître les champs requis pour chaque type d'objet :

- **dcim.device** : `name`, `device_type`, `device_role`, `site`
- **dcim.site** : `name`, `slug`
- **ipam.ipaddress** : `address`
- **ipam.vlan** : `vid`, `name`

## ❌ Gestion des erreurs

### Erreur de validation

```json
{
  "error": "API error: 400 Bad Request - {'name': ['This field is required.']}"
}
```

**Solution** : Vérifier que tous les champs requis sont fournis.

### Erreur de permissions

```json
{
  "error": "API error: 403 Forbidden - Permission denied"
}
```

**Solution** : Vérifier que votre token a les permissions nécessaires.

### Objet non trouvé

```json
{
  "error": "API error: 404 Not Found - Object not found"
}
```

**Solution** : Vérifier que l'ID de l'objet existe.

### Conflit de données

```json
{
  "error": "API error: 400 Bad Request - {'slug': ['This value must be unique.']}"
}
```

**Solution** : Utiliser une valeur unique pour le champ en question.

## 🔍 Types d'objets les plus courants

### DCIM (Data Center Infrastructure Management)

- `dcim.site` - Sites/Datacenters
- `dcim.device` - Appareils (switches, routers, serveurs)
- `dcim.interface` - Interfaces réseau
- `dcim.rack` - Racks
- `dcim.cable` - Câbles

### IPAM (IP Address Management)

- `ipam.ipaddress` - Adresses IP
- `ipam.prefix` - Préfixes réseau
- `ipam.vlan` - VLANs
- `ipam.vrf` - VRFs
- `ipam.aggregate` - Agrégats IP

### Circuits

- `circuits.circuit` - Circuits
- `circuits.provider` - Fournisseurs
- `circuits.circuittype` - Types de circuits

### Virtualization

- `virtualization.virtualmachine` - Machines virtuelles
- `virtualization.cluster` - Clusters
- `virtualization.vminterface` - Interfaces VM

## 🚀 Exemples avancés

### Créer un appareil avec toutes ses interfaces

```json
// 1. Créer l'appareil
{
  "tool": "netbox_create_object",
  "arguments": {
    "object_type": "dcim.device",
    "data": {
      "name": "switch-01",
      "device_type": 5,
      "device_role": 2,
      "site": 3,
      "status": "active"
    }
  }
}

// 2. Créer les interfaces (répéter pour chaque interface)
{
  "tool": "netbox_create_object",
  "arguments": {
    "object_type": "dcim.interface",
    "data": {
      "device": 124,  // ID de l'appareil créé
      "name": "GigabitEthernet1/0/1",
      "type": "1000base-t",
      "enabled": true
    }
  }
}
```

### Migration d'appareil entre sites

```json
// 1. Récupérer l'appareil
{
  "tool": "netbox_get_object_by_id",
  "arguments": {
    "object_type": "dcim.device",
    "object_id": 123
  }
}

// 2. Mettre à jour le site
{
  "tool": "netbox_update_object",
  "arguments": {
    "object_type": "dcim.device",
    "object_id": 123,
    "data": {
      "site": 5,  // Nouveau site
      "comments": "Migré vers le datacenter de Lyon"
    }
  }
}
```

## 📚 Ressources

- [Documentation API NetBox](https://docs.netbox.dev/en/stable/rest-api/)
- [Liste complète des objets NetBox](https://docs.netbox.dev/en/stable/models/)
- [Guide des permissions NetBox](https://docs.netbox.dev/en/stable/administration/permissions/)

## ⚠️ Avertissements importants

1. **Suppression irréversible** : Les objets supprimés ne peuvent pas être récupérés
2. **Vérification des dépendances** : Certains objets ne peuvent pas être supprimés s'ils sont référencés par d'autres
3. **Permissions** : Assurez-vous que votre token a les bonnes permissions
4. **Validation** : NetBox valide toutes les données avant de les sauvegarder
5. **Changements en cascade** : Certaines modifications peuvent affecter d'autres objets

## 🆘 Support

Pour toute question ou problème :
- Consultez les logs du serveur MCP (niveau DEBUG pour plus de détails)
- Vérifiez la documentation de l'API NetBox
- Assurez-vous que votre instance NetBox est à jour
