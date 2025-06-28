# NetBox REST API Endpoints Checklist

This checklist tracks the implementation of MCP tools for all NetBox 4.3 API endpoints. Each endpoint supports multiple HTTP methods as indicated.

**Legend:**
- 📋 Collection endpoints (`/resource/`): GET, POST, PUT, PATCH, DELETE
- 🔍 Individual endpoints (`/resource/{id}/`): GET, PUT, PATCH, DELETE  
- ⚡ Action endpoints (`/resource/{id}/action/`): GET (typically read-only)

**Current Status:**
- ✅ **Implemented**: Tool exists in MCP server
- ❌ **Not Implemented**: Tool needs to be created
- 📝 **Planned**: Tool planned for implementation

---

## Circuits Module

### Circuit Group Assignments
- [ ] 📋 `/api/circuits/circuit-group-assignments/` - List/Create circuit group assignments
- [ ] 🔍 `/api/circuits/circuit-group-assignments/{id}/` - Get/Update/Delete specific assignment

### Circuit Groups  
- [ ] 📋 `/api/circuits/circuit-groups/` - List/Create circuit groups
- [ ] 🔍 `/api/circuits/circuit-groups/{id}/` - Get/Update/Delete specific group

### Circuit Terminations
- [x] 📋 `/api/circuits/circuit-terminations/` - List/Create circuit terminations ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/circuits/circuit-terminations/{id}/` - Get/Update/Delete specific termination
- [ ] ⚡ `/api/circuits/circuit-terminations/{id}/paths/` - Get termination paths

### Circuit Types
- [x] 📋 `/api/circuits/circuit-types/` - List/Create circuit types ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/circuits/circuit-types/{id}/` - Get/Update/Delete specific type

### Circuits
- [x] 📋 `/api/circuits/circuits/` - List/Create circuits ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/circuits/circuits/{id}/` - Get/Update/Delete specific circuit

### Provider Accounts
- [ ] 📋 `/api/circuits/provider-accounts/` - List/Create provider accounts
- [ ] 🔍 `/api/circuits/provider-accounts/{id}/` - Get/Update/Delete specific account

### Provider Networks
- [x] 📋 `/api/circuits/provider-networks/` - List/Create provider networks ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/circuits/provider-networks/{id}/` - Get/Update/Delete specific network

### Providers
- [x] 📋 `/api/circuits/providers/` - List/Create providers ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/circuits/providers/{id}/` - Get/Update/Delete specific provider

### Virtual Circuit Terminations
- [ ] 📋 `/api/circuits/virtual-circuit-terminations/` - List/Create virtual circuit terminations
- [ ] 🔍 `/api/circuits/virtual-circuit-terminations/{id}/` - Get/Update/Delete specific virtual termination
- [ ] ⚡ `/api/circuits/virtual-circuit-terminations/{id}/paths/` - Get virtual termination paths

### Virtual Circuit Types
- [ ] 📋 `/api/circuits/virtual-circuit-types/` - List/Create virtual circuit types
- [ ] 🔍 `/api/circuits/virtual-circuit-types/{id}/` - Get/Update/Delete specific virtual type

### Virtual Circuits
- [ ] 📋 `/api/circuits/virtual-circuits/` - List/Create virtual circuits
- [ ] 🔍 `/api/circuits/virtual-circuits/{id}/` - Get/Update/Delete specific virtual circuit

---

## Core Module

### Background Queues
- [ ] 📋 `/api/core/background-queues/` - List background queues
- [ ] 🔍 `/api/core/background-queues/{name}/` - Get specific queue

### Background Tasks
- [ ] 📋 `/api/core/background-tasks/` - List background tasks
- [ ] 🔍 `/api/core/background-tasks/{id}/` - Get specific task
- [ ] ⚡ `/api/core/background-tasks/{id}/delete/` - Delete task
- [ ] ⚡ `/api/core/background-tasks/{id}/enqueue/` - Enqueue task
- [ ] ⚡ `/api/core/background-tasks/{id}/requeue/` - Requeue task
- [ ] ⚡ `/api/core/background-tasks/{id}/stop/` - Stop task

### Background Workers
- [ ] 📋 `/api/core/background-workers/` - List background workers
- [ ] 🔍 `/api/core/background-workers/{name}/` - Get specific worker

### Data Files
- [ ] 📋 `/api/core/data-files/` - List/Create data files
- [ ] 🔍 `/api/core/data-files/{id}/` - Get/Update/Delete specific file

### Data Sources
- [ ] 📋 `/api/core/data-sources/` - List/Create data sources
- [ ] 🔍 `/api/core/data-sources/{id}/` - Get/Update/Delete specific source
- [ ] ⚡ `/api/core/data-sources/{id}/sync/` - Sync data source

### Jobs
- [ ] 📋 `/api/core/jobs/` - List jobs
- [ ] 🔍 `/api/core/jobs/{id}/` - Get specific job

### Object Changes
- [x] 📋 `/api/core/object-changes/` - List object changes (changelogs) ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/core/object-changes/{id}/` - Get specific change

---

## DCIM (Data Center Infrastructure Management) Module

### Cable Terminations
- [ ] 📋 `/api/dcim/cable-terminations/` - List/Create cable terminations
- [ ] 🔍 `/api/dcim/cable-terminations/{id}/` - Get/Update/Delete specific termination

### Cables
- [x] 📋 `/api/dcim/cables/` - List/Create cables ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/cables/{id}/` - Get/Update/Delete specific cable

### Connected Device
- [ ] ⚡ `/api/dcim/connected-device/` - Get connected device info

### Console Port Templates
- [ ] 📋 `/api/dcim/console-port-templates/` - List/Create console port templates
- [ ] 🔍 `/api/dcim/console-port-templates/{id}/` - Get/Update/Delete specific template

### Console Ports
- [x] 📋 `/api/dcim/console-ports/` - List/Create console ports ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/console-ports/{id}/` - Get/Update/Delete specific port
- [ ] ⚡ `/api/dcim/console-ports/{id}/trace/` - Trace console port

### Console Server Port Templates
- [ ] 📋 `/api/dcim/console-server-port-templates/` - List/Create console server port templates
- [ ] 🔍 `/api/dcim/console-server-port-templates/{id}/` - Get/Update/Delete specific template

### Console Server Ports
- [x] 📋 `/api/dcim/console-server-ports/` - List/Create console server ports ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/console-server-ports/{id}/` - Get/Update/Delete specific port
- [ ] ⚡ `/api/dcim/console-server-ports/{id}/trace/` - Trace console server port

### Device Bay Templates
- [ ] 📋 `/api/dcim/device-bay-templates/` - List/Create device bay templates
- [ ] 🔍 `/api/dcim/device-bay-templates/{id}/` - Get/Update/Delete specific template

### Device Bays
- [x] 📋 `/api/dcim/device-bays/` - List/Create device bays ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/device-bays/{id}/` - Get/Update/Delete specific bay

### Device Roles
- [x] 📋 `/api/dcim/device-roles/` - List/Create device roles ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/device-roles/{id}/` - Get/Update/Delete specific role

### Device Types
- [x] 📋 `/api/dcim/device-types/` - List/Create device types ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/device-types/{id}/` - Get/Update/Delete specific type

### Devices
- [x] 📋 `/api/dcim/devices/` - List/Create devices ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/devices/{id}/` - Get/Update/Delete specific device
- [ ] ⚡ `/api/dcim/devices/{id}/render-config/` - Render device configuration

### Front Port Templates
- [ ] 📋 `/api/dcim/front-port-templates/` - List/Create front port templates
- [ ] 🔍 `/api/dcim/front-port-templates/{id}/` - Get/Update/Delete specific template

### Front Ports
- [x] 📋 `/api/dcim/front-ports/` - List/Create front ports ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/front-ports/{id}/` - Get/Update/Delete specific port
- [ ] ⚡ `/api/dcim/front-ports/{id}/paths/` - Get front port paths

### Interface Templates
- [ ] 📋 `/api/dcim/interface-templates/` - List/Create interface templates
- [ ] 🔍 `/api/dcim/interface-templates/{id}/` - Get/Update/Delete specific template

### Interfaces
- [x] 📋 `/api/dcim/interfaces/` - List/Create interfaces ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/interfaces/{id}/` - Get/Update/Delete specific interface
- [ ] ⚡ `/api/dcim/interfaces/{id}/trace/` - Trace interface

### Inventory Item Roles
- [ ] 📋 `/api/dcim/inventory-item-roles/` - List/Create inventory item roles
- [ ] 🔍 `/api/dcim/inventory-item-roles/{id}/` - Get/Update/Delete specific role

### Inventory Item Templates
- [ ] 📋 `/api/dcim/inventory-item-templates/` - List/Create inventory item templates
- [ ] 🔍 `/api/dcim/inventory-item-templates/{id}/` - Get/Update/Delete specific template

### Inventory Items
- [x] 📋 `/api/dcim/inventory-items/` - List/Create inventory items ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/inventory-items/{id}/` - Get/Update/Delete specific item

### Locations
- [x] 📋 `/api/dcim/locations/` - List/Create locations ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/locations/{id}/` - Get/Update/Delete specific location

### MAC Addresses
- [ ] 📋 `/api/dcim/mac-addresses/` - List/Create MAC addresses
- [ ] 🔍 `/api/dcim/mac-addresses/{id}/` - Get/Update/Delete specific MAC address

### Manufacturers
- [x] 📋 `/api/dcim/manufacturers/` - List/Create manufacturers ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/manufacturers/{id}/` - Get/Update/Delete specific manufacturer

### Module Bay Templates
- [ ] 📋 `/api/dcim/module-bay-templates/` - List/Create module bay templates
- [ ] 🔍 `/api/dcim/module-bay-templates/{id}/` - Get/Update/Delete specific template

### Module Bays
- [x] 📋 `/api/dcim/module-bays/` - List/Create module bays ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/module-bays/{id}/` - Get/Update/Delete specific bay

### Module Type Profiles
- [ ] 📋 `/api/dcim/module-type-profiles/` - List/Create module type profiles
- [ ] 🔍 `/api/dcim/module-type-profiles/{id}/` - Get/Update/Delete specific profile

### Module Types
- [x] 📋 `/api/dcim/module-types/` - List/Create module types ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/module-types/{id}/` - Get/Update/Delete specific type

### Modules
- [x] 📋 `/api/dcim/modules/` - List/Create modules ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/modules/{id}/` - Get/Update/Delete specific module

### Platforms
- [x] 📋 `/api/dcim/platforms/` - List/Create platforms ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/platforms/{id}/` - Get/Update/Delete specific platform

### Power Feeds
- [x] 📋 `/api/dcim/power-feeds/` - List/Create power feeds ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/power-feeds/{id}/` - Get/Update/Delete specific feed
- [ ] ⚡ `/api/dcim/power-feeds/{id}/trace/` - Trace power feed

### Power Outlet Templates
- [ ] 📋 `/api/dcim/power-outlet-templates/` - List/Create power outlet templates
- [ ] 🔍 `/api/dcim/power-outlet-templates/{id}/` - Get/Update/Delete specific template

### Power Outlets
- [x] 📋 `/api/dcim/power-outlets/` - List/Create power outlets ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/power-outlets/{id}/` - Get/Update/Delete specific outlet
- [ ] ⚡ `/api/dcim/power-outlets/{id}/trace/` - Trace power outlet

### Power Panels
- [x] 📋 `/api/dcim/power-panels/` - List/Create power panels ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/power-panels/{id}/` - Get/Update/Delete specific panel

### Power Port Templates
- [ ] 📋 `/api/dcim/power-port-templates/` - List/Create power port templates
- [ ] 🔍 `/api/dcim/power-port-templates/{id}/` - Get/Update/Delete specific template

### Power Ports
- [x] 📋 `/api/dcim/power-ports/` - List/Create power ports ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/power-ports/{id}/` - Get/Update/Delete specific port
- [ ] ⚡ `/api/dcim/power-ports/{id}/trace/` - Trace power port

### Rack Reservations
- [x] 📋 `/api/dcim/rack-reservations/` - List/Create rack reservations ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/rack-reservations/{id}/` - Get/Update/Delete specific reservation

### Rack Roles
- [x] 📋 `/api/dcim/rack-roles/` - List/Create rack roles ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/rack-roles/{id}/` - Get/Update/Delete specific role

### Rack Types
- [ ] 📋 `/api/dcim/rack-types/` - List/Create rack types
- [ ] 🔍 `/api/dcim/rack-types/{id}/` - Get/Update/Delete specific type

### Racks
- [x] 📋 `/api/dcim/racks/` - List/Create racks ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/racks/{id}/` - Get/Update/Delete specific rack
- [ ] ⚡ `/api/dcim/racks/{id}/elevation/` - Get rack elevation

### Rear Port Templates
- [ ] 📋 `/api/dcim/rear-port-templates/` - List/Create rear port templates
- [ ] 🔍 `/api/dcim/rear-port-templates/{id}/` - Get/Update/Delete specific template

### Rear Ports
- [ ] 📋 `/api/dcim/rear-ports/` - List/Create rear ports
- [ ] 🔍 `/api/dcim/rear-ports/{id}/` - Get/Update/Delete specific port
- [ ] ⚡ `/api/dcim/rear-ports/{id}/paths/` - Get rear port paths

### Regions
- [x] 📋 `/api/dcim/regions/` - List/Create regions ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/regions/{id}/` - Get/Update/Delete specific region

### Site Groups
- [x] 📋 `/api/dcim/site-groups/` - List/Create site groups ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/site-groups/{id}/` - Get/Update/Delete specific group

### Sites
- [x] 📋 `/api/dcim/sites/` - List/Create sites ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/sites/{id}/` - Get/Update/Delete specific site

### Virtual Chassis
- [x] 📋 `/api/dcim/virtual-chassis/` - List/Create virtual chassis ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/dcim/virtual-chassis/{id}/` - Get/Update/Delete specific chassis

### Virtual Device Contexts
- [ ] 📋 `/api/dcim/virtual-device-contexts/` - List/Create virtual device contexts
- [ ] 🔍 `/api/dcim/virtual-device-contexts/{id}/` - Get/Update/Delete specific context

---

## Extras Module

### Bookmarks
- [ ] 📋 `/api/extras/bookmarks/` - List/Create bookmarks
- [ ] 🔍 `/api/extras/bookmarks/{id}/` - Get/Update/Delete specific bookmark

### Config Contexts
- [x] 📋 `/api/extras/config-contexts/` - List/Create config contexts ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/extras/config-contexts/{id}/` - Get/Update/Delete specific context
- [ ] ⚡ `/api/extras/config-contexts/{id}/sync/` - Sync config context

### Config Templates
- [ ] 📋 `/api/extras/config-templates/` - List/Create config templates
- [ ] 🔍 `/api/extras/config-templates/{id}/` - Get/Update/Delete specific template
- [ ] ⚡ `/api/extras/config-templates/{id}/render/` - Render config template
- [ ] ⚡ `/api/extras/config-templates/{id}/sync/` - Sync config template

### Custom Field Choice Sets
- [ ] 📋 `/api/extras/custom-field-choice-sets/` - List/Create custom field choice sets
- [ ] 🔍 `/api/extras/custom-field-choice-sets/{id}/` - Get/Update/Delete specific choice set
- [ ] ⚡ `/api/extras/custom-field-choice-sets/{id}/choices/` - Get choice set choices

### Custom Fields
- [x] 📋 `/api/extras/custom-fields/` - List/Create custom fields ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/extras/custom-fields/{id}/` - Get/Update/Delete specific field

### Custom Links
- [ ] 📋 `/api/extras/custom-links/` - List/Create custom links
- [ ] 🔍 `/api/extras/custom-links/{id}/` - Get/Update/Delete specific link

### Dashboard
- [ ] ⚡ `/api/extras/dashboard/` - Get dashboard data

### Event Rules
- [ ] 📋 `/api/extras/event-rules/` - List/Create event rules
- [ ] 🔍 `/api/extras/event-rules/{id}/` - Get/Update/Delete specific rule

### Export Templates
- [x] 📋 `/api/extras/export-templates/` - List/Create export templates ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/extras/export-templates/{id}/` - Get/Update/Delete specific template
- [ ] ⚡ `/api/extras/export-templates/{id}/sync/` - Sync export template

### Image Attachments
- [x] 📋 `/api/extras/image-attachments/` - List/Create image attachments ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/extras/image-attachments/{id}/` - Get/Update/Delete specific attachment

### Journal Entries
- [ ] 📋 `/api/extras/journal-entries/` - List/Create journal entries
- [ ] 🔍 `/api/extras/journal-entries/{id}/` - Get/Update/Delete specific entry

### Notification Groups
- [ ] 📋 `/api/extras/notification-groups/` - List/Create notification groups
- [ ] 🔍 `/api/extras/notification-groups/{id}/` - Get/Update/Delete specific group

### Notifications
- [ ] 📋 `/api/extras/notifications/` - List/Create notifications
- [ ] 🔍 `/api/extras/notifications/{id}/` - Get/Update/Delete specific notification

### Object Types
- [ ] 📋 `/api/extras/object-types/` - List object types
- [ ] 🔍 `/api/extras/object-types/{id}/` - Get specific object type

### Saved Filters
- [x] 📋 `/api/extras/saved-filters/` - List/Create saved filters ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/extras/saved-filters/{id}/` - Get/Update/Delete specific filter

### Scripts
- [x] 📋 `/api/extras/scripts/` - List scripts ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/extras/scripts/{id}/` - Get specific script

### Subscriptions
- [ ] 📋 `/api/extras/subscriptions/` - List/Create subscriptions
- [ ] 🔍 `/api/extras/subscriptions/{id}/` - Get/Update/Delete specific subscription

### Table Configs
- [ ] 📋 `/api/extras/table-configs/` - List/Create table configs
- [ ] 🔍 `/api/extras/table-configs/{id}/` - Get/Update/Delete specific config

### Tagged Objects
- [ ] 📋 `/api/extras/tagged-objects/` - List tagged objects
- [ ] 🔍 `/api/extras/tagged-objects/{id}/` - Get specific tagged object

### Tags
- [x] 📋 `/api/extras/tags/` - List/Create tags ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/extras/tags/{id}/` - Get/Update/Delete specific tag

### Webhooks
- [x] 📋 `/api/extras/webhooks/` - List/Create webhooks ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/extras/webhooks/{id}/` - Get/Update/Delete specific webhook

---

## IPAM (IP Address Management) Module

### Aggregates
- [x] 📋 `/api/ipam/aggregates/` - List/Create aggregates ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/aggregates/{id}/` - Get/Update/Delete specific aggregate

### ASN Ranges
- [x] 📋 `/api/ipam/asn-ranges/` - List/Create ASN ranges ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/asn-ranges/{id}/` - Get/Update/Delete specific range
- [ ] ⚡ `/api/ipam/asn-ranges/{id}/available-asns/` - Get available ASNs in range

### ASNs
- [x] 📋 `/api/ipam/asns/` - List/Create ASNs ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/asns/{id}/` - Get/Update/Delete specific ASN

### FHRP Group Assignments
- [ ] 📋 `/api/ipam/fhrp-group-assignments/` - List/Create FHRP group assignments
- [ ] 🔍 `/api/ipam/fhrp-group-assignments/{id}/` - Get/Update/Delete specific assignment

### FHRP Groups
- [x] 📋 `/api/ipam/fhrp-groups/` - List/Create FHRP groups ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/fhrp-groups/{id}/` - Get/Update/Delete specific group

### IP Addresses
- [x] 📋 `/api/ipam/ip-addresses/` - List/Create IP addresses ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/ip-addresses/{id}/` - Get/Update/Delete specific address

### IP Ranges
- [x] 📋 `/api/ipam/ip-ranges/` - List/Create IP ranges ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/ip-ranges/{id}/` - Get/Update/Delete specific range
- [ ] ⚡ `/api/ipam/ip-ranges/{id}/available-ips/` - Get available IPs in range

### Prefixes
- [x] 📋 `/api/ipam/prefixes/` - List/Create prefixes ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/prefixes/{id}/` - Get/Update/Delete specific prefix
- [ ] ⚡ `/api/ipam/prefixes/{id}/available-ips/` - Get available IPs in prefix
- [ ] ⚡ `/api/ipam/prefixes/{id}/available-prefixes/` - Get available prefixes

### RIRs
- [x] 📋 `/api/ipam/rirs/` - List/Create RIRs ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/rirs/{id}/` - Get/Update/Delete specific RIR

### Roles
- [x] 📋 `/api/ipam/roles/` - List/Create IPAM roles ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/roles/{id}/` - Get/Update/Delete specific role

### Route Targets
- [x] 📋 `/api/ipam/route-targets/` - List/Create route targets ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/route-targets/{id}/` - Get/Update/Delete specific target

### Service Templates
- [ ] 📋 `/api/ipam/service-templates/` - List/Create service templates
- [ ] 🔍 `/api/ipam/service-templates/{id}/` - Get/Update/Delete specific template

### Services
- [x] 📋 `/api/ipam/services/` - List/Create services ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/services/{id}/` - Get/Update/Delete specific service

### VLAN Groups
- [x] 📋 `/api/ipam/vlan-groups/` - List/Create VLAN groups ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/vlan-groups/{id}/` - Get/Update/Delete specific group
- [ ] ⚡ `/api/ipam/vlan-groups/{id}/available-vlans/` - Get available VLANs in group

### VLAN Translation Policies
- [ ] 📋 `/api/ipam/vlan-translation-policies/` - List/Create VLAN translation policies
- [ ] 🔍 `/api/ipam/vlan-translation-policies/{id}/` - Get/Update/Delete specific policy

### VLAN Translation Rules
- [ ] 📋 `/api/ipam/vlan-translation-rules/` - List/Create VLAN translation rules
- [ ] 🔍 `/api/ipam/vlan-translation-rules/{id}/` - Get/Update/Delete specific rule

### VLANs
- [x] 📋 `/api/ipam/vlans/` - List/Create VLANs ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/vlans/{id}/` - Get/Update/Delete specific VLAN

### VRFs
- [x] 📋 `/api/ipam/vrfs/` - List/Create VRFs ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/ipam/vrfs/{id}/` - Get/Update/Delete specific VRF

---

## System Endpoints

### Schema
- [ ] ⚡ `/api/schema/` - Get API schema

### Status
- [ ] ⚡ `/api/status/` - Get system status

---

## Tenancy Module

### Contact Assignments
- [ ] 📋 `/api/tenancy/contact-assignments/` - List/Create contact assignments
- [ ] 🔍 `/api/tenancy/contact-assignments/{id}/` - Get/Update/Delete specific assignment

### Contact Groups
- [x] 📋 `/api/tenancy/contact-groups/` - List/Create contact groups ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/tenancy/contact-groups/{id}/` - Get/Update/Delete specific group

### Contact Roles
- [x] 📋 `/api/tenancy/contact-roles/` - List/Create contact roles ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/tenancy/contact-roles/{id}/` - Get/Update/Delete specific role

### Contacts
- [x] 📋 `/api/tenancy/contacts/` - List/Create contacts ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/tenancy/contacts/{id}/` - Get/Update/Delete specific contact

### Tenant Groups
- [x] 📋 `/api/tenancy/tenant-groups/` - List/Create tenant groups ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/tenancy/tenant-groups/{id}/` - Get/Update/Delete specific group

### Tenants
- [x] 📋 `/api/tenancy/tenants/` - List/Create tenants ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/tenancy/tenants/{id}/` - Get/Update/Delete specific tenant

---

## Users Module

### Config
- [ ] ⚡ `/api/users/config/` - Get user configuration

### Groups
- [ ] 📋 `/api/users/groups/` - List/Create user groups
- [ ] 🔍 `/api/users/groups/{id}/` - Get/Update/Delete specific group

### Permissions
- [ ] 📋 `/api/users/permissions/` - List permissions
- [ ] 🔍 `/api/users/permissions/{id}/` - Get specific permission

### Tokens
- [ ] 📋 `/api/users/tokens/` - List/Create API tokens
- [ ] 🔍 `/api/users/tokens/{id}/` - Get/Update/Delete specific token
- [ ] ⚡ `/api/users/tokens/provision/` - Provision token

### Users
- [ ] 📋 `/api/users/users/` - List/Create users
- [ ] 🔍 `/api/users/users/{id}/` - Get/Update/Delete specific user

---

## Virtualization Module

### Cluster Groups
- [x] 📋 `/api/virtualization/cluster-groups/` - List/Create cluster groups ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/virtualization/cluster-groups/{id}/` - Get/Update/Delete specific group

### Cluster Types
- [x] 📋 `/api/virtualization/cluster-types/` - List/Create cluster types ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/virtualization/cluster-types/{id}/` - Get/Update/Delete specific type

### Clusters
- [x] 📋 `/api/virtualization/clusters/` - List/Create clusters ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/virtualization/clusters/{id}/` - Get/Update/Delete specific cluster

### Interfaces
- [x] 📋 `/api/virtualization/interfaces/` - List/Create VM interfaces ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/virtualization/interfaces/{id}/` - Get/Update/Delete specific interface

### Virtual Disks
- [ ] 📋 `/api/virtualization/virtual-disks/` - List/Create virtual disks
- [ ] 🔍 `/api/virtualization/virtual-disks/{id}/` - Get/Update/Delete specific disk

### Virtual Machines
- [x] 📋 `/api/virtualization/virtual-machines/` - List/Create virtual machines ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/virtualization/virtual-machines/{id}/` - Get/Update/Delete specific VM
- [ ] ⚡ `/api/virtualization/virtual-machines/{id}/render-config/` - Render VM configuration

---

## VPN Module

### IKE Policies
- [x] 📋 `/api/vpn/ike-policies/` - List/Create IKE policies ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/vpn/ike-policies/{id}/` - Get/Update/Delete specific policy

### IKE Proposals
- [x] 📋 `/api/vpn/ike-proposals/` - List/Create IKE proposals ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/vpn/ike-proposals/{id}/` - Get/Update/Delete specific proposal

### IPSec Policies
- [x] 📋 `/api/vpn/ipsec-policies/` - List/Create IPSec policies ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/vpn/ipsec-policies/{id}/` - Get/Update/Delete specific policy

### IPSec Profiles
- [x] 📋 `/api/vpn/ipsec-profiles/` - List/Create IPSec profiles ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/vpn/ipsec-profiles/{id}/` - Get/Update/Delete specific profile

### IPSec Proposals
- [x] 📋 `/api/vpn/ipsec-proposals/` - List/Create IPSec proposals ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/vpn/ipsec-proposals/{id}/` - Get/Update/Delete specific proposal

### L2VPN Terminations
- [ ] 📋 `/api/vpn/l2vpn-terminations/` - List/Create L2VPN terminations
- [ ] 🔍 `/api/vpn/l2vpn-terminations/{id}/` - Get/Update/Delete specific termination

### L2VPNs
- [x] 📋 `/api/vpn/l2vpns/` - List/Create L2VPNs ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/vpn/l2vpns/{id}/` - Get/Update/Delete specific L2VPN

### Tunnel Groups
- [x] 📋 `/api/vpn/tunnel-groups/` - List/Create tunnel groups ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/vpn/tunnel-groups/{id}/` - Get/Update/Delete specific group

### Tunnel Terminations
- [ ] 📋 `/api/vpn/tunnel-terminations/` - List/Create tunnel terminations
- [ ] 🔍 `/api/vpn/tunnel-terminations/{id}/` - Get/Update/Delete specific termination

### Tunnels
- [x] 📋 `/api/vpn/tunnels/` - List/Create tunnels ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/vpn/tunnels/{id}/` - Get/Update/Delete specific tunnel

---

## Wireless Module

### Wireless LAN Groups
- [x] 📋 `/api/wireless/wireless-lan-groups/` - List/Create wireless LAN groups ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/wireless/wireless-lan-groups/{id}/` - Get/Update/Delete specific group

### Wireless LANs
- [x] 📋 `/api/wireless/wireless-lans/` - List/Create wireless LANs ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/wireless/wireless-lans/{id}/` - Get/Update/Delete specific LAN

### Wireless Links
- [x] 📋 `/api/wireless/wireless-links/` - List/Create wireless links ✅ **IMPLEMENTED**
- [ ] 🔍 `/api/wireless/wireless-links/{id}/` - Get/Update/Delete specific link

---

## Summary Statistics

**Total Endpoints:** 275+
- **Collection Endpoints:** 142 (List/Create operations)
- **Individual Endpoints:** 115 (Get/Update/Delete operations)  
- **Action Endpoints:** 18 (Special operations like trace, render, sync)

**Implementation Status:**
- ✅ **Implemented:** 76 collection endpoints (54%)
- ❌ **Not Implemented:** 199 endpoints (72%)
- 📝 **Remaining Work:** 199 endpoints need MCP tools

**Next Priority Modules:**
1. **Individual Endpoints:** Complete {id} operations for implemented collections
2. **Action Endpoints:** Implement trace, render, sync, and availability operations
3. **Core Module:** Background tasks, data sources, jobs
4. **Users Module:** Authentication and authorization management
5. **Template Endpoints:** All template-based operations