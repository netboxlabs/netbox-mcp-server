package main

// NetBoxObjectType represents a NetBox object type configuration
type NetBoxObjectType struct {
	Name     string `json:"name"`
	Endpoint string `json:"endpoint"`
}

// NetBoxObjectTypes contains the mapping of object type names to their configuration
var NetBoxObjectTypes = map[string]NetBoxObjectType{
	"circuits.circuit": {
		Name:     "Circuit",
		Endpoint: "circuits/circuits",
	},
	"circuits.circuitgroup": {
		Name:     "CircuitGroup",
		Endpoint: "circuits/circuit-groups",
	},
	"circuits.circuitgroupassignment": {
		Name:     "CircuitGroupAssignment",
		Endpoint: "circuits/circuit-group-assignments",
	},
	"circuits.circuittermination": {
		Name:     "CircuitTermination",
		Endpoint: "circuits/circuit-terminations",
	},
	"circuits.circuittype": {
		Name:     "CircuitType",
		Endpoint: "circuits/circuit-types",
	},
	"circuits.provider": {
		Name:     "Provider",
		Endpoint: "circuits/providers",
	},
	"circuits.provideraccount": {
		Name:     "ProviderAccount",
		Endpoint: "circuits/provider-accounts",
	},
	"circuits.providernetwork": {
		Name:     "ProviderNetwork",
		Endpoint: "circuits/provider-networks",
	},
	"circuits.virtualcircuit": {
		Name:     "VirtualCircuit",
		Endpoint: "circuits/virtual-circuits",
	},
	"circuits.virtualcircuittermination": {
		Name:     "VirtualCircuitTermination",
		Endpoint: "circuits/virtual-circuit-terminations",
	},
	"circuits.virtualcircuittype": {
		Name:     "VirtualCircuitType",
		Endpoint: "circuits/virtual-circuit-types",
	},
	"core.datafile": {
		Name:     "DataFile",
		Endpoint: "core/data-files",
	},
	"core.datasource": {
		Name:     "DataSource",
		Endpoint: "core/data-sources",
	},
	"core.job": {
		Name:     "Job",
		Endpoint: "core/jobs",
	},
	"core.objectchange": {
		Name:     "ObjectChange",
		Endpoint: "core/object-changes",
	},
	"core.objecttype": {
		Name:     "ObjectType",
		Endpoint: "extras/object-types",
	},
	"dcim.cable": {
		Name:     "Cable",
		Endpoint: "dcim/cables",
	},
	"dcim.cabletermination": {
		Name:     "CableTermination",
		Endpoint: "dcim/cable-terminations",
	},
	"dcim.consoleport": {
		Name:     "ConsolePort",
		Endpoint: "dcim/console-ports",
	},
	"dcim.consoleporttemplate": {
		Name:     "ConsolePortTemplate",
		Endpoint: "dcim/console-port-templates",
	},
	"dcim.consoleserverport": {
		Name:     "ConsoleServerPort",
		Endpoint: "dcim/console-server-ports",
	},
	"dcim.consoleserverporttemplate": {
		Name:     "ConsoleServerPortTemplate",
		Endpoint: "dcim/console-server-port-templates",
	},
	"dcim.device": {
		Name:     "Device",
		Endpoint: "dcim/devices",
	},
	"dcim.devicebay": {
		Name:     "DeviceBay",
		Endpoint: "dcim/device-bays",
	},
	"dcim.devicebaytemplate": {
		Name:     "DeviceBayTemplate",
		Endpoint: "dcim/device-bay-templates",
	},
	"dcim.devicerole": {
		Name:     "DeviceRole",
		Endpoint: "dcim/device-roles",
	},
	"dcim.devicetype": {
		Name:     "DeviceType",
		Endpoint: "dcim/device-types",
	},
	"dcim.frontport": {
		Name:     "FrontPort",
		Endpoint: "dcim/front-ports",
	},
	"dcim.frontporttemplate": {
		Name:     "FrontPortTemplate",
		Endpoint: "dcim/front-port-templates",
	},
	"dcim.interface": {
		Name:     "Interface",
		Endpoint: "dcim/interfaces",
	},
	"dcim.interfacetemplate": {
		Name:     "InterfaceTemplate",
		Endpoint: "dcim/interface-templates",
	},
	"dcim.inventoryitem": {
		Name:     "InventoryItem",
		Endpoint: "dcim/inventory-items",
	},
	"dcim.inventoryitemrole": {
		Name:     "InventoryItemRole",
		Endpoint: "dcim/inventory-item-roles",
	},
	"dcim.inventoryitemtemplate": {
		Name:     "InventoryItemTemplate",
		Endpoint: "dcim/inventory-item-templates",
	},
	"dcim.location": {
		Name:     "Location",
		Endpoint: "dcim/locations",
	},
	"dcim.macaddress": {
		Name:     "MACAddress",
		Endpoint: "dcim/mac-addresses",
	},
	"dcim.manufacturer": {
		Name:     "Manufacturer",
		Endpoint: "dcim/manufacturers",
	},
	"dcim.module": {
		Name:     "Module",
		Endpoint: "dcim/modules",
	},
	"dcim.modulebay": {
		Name:     "ModuleBay",
		Endpoint: "dcim/module-bays",
	},
	"dcim.modulebaytemplate": {
		Name:     "ModuleBayTemplate",
		Endpoint: "dcim/module-bay-templates",
	},
	"dcim.moduletype": {
		Name:     "ModuleType",
		Endpoint: "dcim/module-types",
	},
	"dcim.moduletypeprofile": {
		Name:     "ModuleTypeProfile",
		Endpoint: "dcim/module-type-profiles",
	},
	"dcim.platform": {
		Name:     "Platform",
		Endpoint: "dcim/platforms",
	},
	"dcim.powerfeed": {
		Name:     "PowerFeed",
		Endpoint: "dcim/power-feeds",
	},
	"dcim.poweroutlet": {
		Name:     "PowerOutlet",
		Endpoint: "dcim/power-outlets",
	},
	"dcim.poweroutlettemplate": {
		Name:     "PowerOutletTemplate",
		Endpoint: "dcim/power-outlet-templates",
	},
	"dcim.powerpanel": {
		Name:     "PowerPanel",
		Endpoint: "dcim/power-panels",
	},
	"dcim.powerport": {
		Name:     "PowerPort",
		Endpoint: "dcim/power-ports",
	},
	"dcim.powerporttemplate": {
		Name:     "PowerPortTemplate",
		Endpoint: "dcim/power-port-templates",
	},
	"dcim.rack": {
		Name:     "Rack",
		Endpoint: "dcim/racks",
	},
	"dcim.rackreservation": {
		Name:     "RackReservation",
		Endpoint: "dcim/rack-reservations",
	},
	"dcim.rackrole": {
		Name:     "RackRole",
		Endpoint: "dcim/rack-roles",
	},
	"dcim.racktype": {
		Name:     "RackType",
		Endpoint: "dcim/rack-types",
	},
	"dcim.rearport": {
		Name:     "RearPort",
		Endpoint: "dcim/rear-ports",
	},
	"dcim.rearporttemplate": {
		Name:     "RearPortTemplate",
		Endpoint: "dcim/rear-port-templates",
	},
	"dcim.region": {
		Name:     "Region",
		Endpoint: "dcim/regions",
	},
	"dcim.site": {
		Name:     "Site",
		Endpoint: "dcim/sites",
	},
	"dcim.sitegroup": {
		Name:     "SiteGroup",
		Endpoint: "dcim/site-groups",
	},
	"dcim.virtualchassis": {
		Name:     "VirtualChassis",
		Endpoint: "dcim/virtual-chassis",
	},
	"dcim.virtualdevicecontext": {
		Name:     "VirtualDeviceContext",
		Endpoint: "dcim/virtual-device-contexts",
	},
	"extras.bookmark": {
		Name:     "Bookmark",
		Endpoint: "extras/bookmarks",
	},
	"extras.configcontext": {
		Name:     "ConfigContext",
		Endpoint: "extras/config-contexts",
	},
	"extras.configtemplate": {
		Name:     "ConfigTemplate",
		Endpoint: "extras/config-templates",
	},
	"extras.customfield": {
		Name:     "CustomField",
		Endpoint: "extras/custom-fields",
	},
	"extras.customfieldchoiceset": {
		Name:     "CustomFieldChoiceSet",
		Endpoint: "extras/custom-field-choice-sets",
	},
	"extras.customlink": {
		Name:     "CustomLink",
		Endpoint: "extras/custom-links",
	},
	"extras.eventrule": {
		Name:     "EventRule",
		Endpoint: "extras/event-rules",
	},
	"extras.exporttemplate": {
		Name:     "ExportTemplate",
		Endpoint: "extras/export-templates",
	},
	"extras.imageattachment": {
		Name:     "ImageAttachment",
		Endpoint: "extras/image-attachments",
	},
	"extras.journalentry": {
		Name:     "JournalEntry",
		Endpoint: "extras/journal-entries",
	},
	"extras.notification": {
		Name:     "Notification",
		Endpoint: "extras/notifications",
	},
	"extras.notificationgroup": {
		Name:     "NotificationGroup",
		Endpoint: "extras/notification-groups",
	},
	"extras.savedfilter": {
		Name:     "SavedFilter",
		Endpoint: "extras/saved-filters",
	},
	"extras.script": {
		Name:     "Script",
		Endpoint: "extras/scripts",
	},
	"extras.subscription": {
		Name:     "Subscription",
		Endpoint: "extras/subscriptions",
	},
	"extras.tableconfig": {
		Name:     "TableConfig",
		Endpoint: "extras/table-configs",
	},
	"extras.tag": {
		Name:     "Tag",
		Endpoint: "extras/tags",
	},
	"extras.taggeditem": {
		Name:     "TaggedItem",
		Endpoint: "extras/tagged-objects",
	},
	"extras.webhook": {
		Name:     "Webhook",
		Endpoint: "extras/webhooks",
	},
	"ipam.aggregate": {
		Name:     "Aggregate",
		Endpoint: "ipam/aggregates",
	},
	"ipam.asn": {
		Name:     "ASN",
		Endpoint: "ipam/asns",
	},
	"ipam.asnrange": {
		Name:     "ASNRange",
		Endpoint: "ipam/asn-ranges",
	},
	"ipam.fhrpgroup": {
		Name:     "FHRPGroup",
		Endpoint: "ipam/fhrp-groups",
	},
	"ipam.fhrpgroupassignment": {
		Name:     "FHRPGroupAssignment",
		Endpoint: "ipam/fhrp-group-assignments",
	},
	"ipam.ipaddress": {
		Name:     "IPAddress",
		Endpoint: "ipam/ip-addresses",
	},
	"ipam.iprange": {
		Name:     "IPRange",
		Endpoint: "ipam/ip-ranges",
	},
	"ipam.prefix": {
		Name:     "Prefix",
		Endpoint: "ipam/prefixes",
	},
	"ipam.rir": {
		Name:     "RIR",
		Endpoint: "ipam/rirs",
	},
	"ipam.role": {
		Name:     "Role",
		Endpoint: "ipam/roles",
	},
	"ipam.routetarget": {
		Name:     "RouteTarget",
		Endpoint: "ipam/route-targets",
	},
	"ipam.service": {
		Name:     "Service",
		Endpoint: "ipam/services",
	},
	"ipam.servicetemplate": {
		Name:     "ServiceTemplate",
		Endpoint: "ipam/service-templates",
	},
	"ipam.vlan": {
		Name:     "VLAN",
		Endpoint: "ipam/vlans",
	},
	"ipam.vlangroup": {
		Name:     "VLANGroup",
		Endpoint: "ipam/vlan-groups",
	},
	"ipam.vlantranslationpolicy": {
		Name:     "VLANTranslationPolicy",
		Endpoint: "ipam/vlan-translation-policies",
	},
	"ipam.vlantranslationrule": {
		Name:     "VLANTranslationRule",
		Endpoint: "ipam/vlan-translation-rules",
	},
	"ipam.vrf": {
		Name:     "VRF",
		Endpoint: "ipam/vrfs",
	},
	"tenancy.contact": {
		Name:     "Contact",
		Endpoint: "tenancy/contacts",
	},
	"tenancy.contactassignment": {
		Name:     "ContactAssignment",
		Endpoint: "tenancy/contact-assignments",
	},
	"tenancy.contactgroup": {
		Name:     "ContactGroup",
		Endpoint: "tenancy/contact-groups",
	},
	"tenancy.contactrole": {
		Name:     "ContactRole",
		Endpoint: "tenancy/contact-roles",
	},
	"tenancy.tenant": {
		Name:     "Tenant",
		Endpoint: "tenancy/tenants",
	},
	"tenancy.tenantgroup": {
		Name:     "TenantGroup",
		Endpoint: "tenancy/tenant-groups",
	},
	"users.group": {
		Name:     "Group",
		Endpoint: "users/groups",
	},
	"users.objectpermission": {
		Name:     "ObjectPermission",
		Endpoint: "users/permissions",
	},
	"users.token": {
		Name:     "Token",
		Endpoint: "users/tokens",
	},
	"users.user": {
		Name:     "User",
		Endpoint: "users/users",
	},
	"virtualization.cluster": {
		Name:     "Cluster",
		Endpoint: "virtualization/clusters",
	},
	"virtualization.clustergroup": {
		Name:     "ClusterGroup",
		Endpoint: "virtualization/cluster-groups",
	},
	"virtualization.clustertype": {
		Name:     "ClusterType",
		Endpoint: "virtualization/cluster-types",
	},
	"virtualization.virtualdisk": {
		Name:     "VirtualDisk",
		Endpoint: "virtualization/virtual-disks",
	},
	"virtualization.virtualmachine": {
		Name:     "VirtualMachine",
		Endpoint: "virtualization/virtual-machines",
	},
	"virtualization.vminterface": {
		Name:     "VMInterface",
		Endpoint: "virtualization/interfaces",
	},
	"vpn.ikepolicy": {
		Name:     "IKEPolicy",
		Endpoint: "vpn/ike-policies",
	},
	"vpn.ikeproposal": {
		Name:     "IKEProposal",
		Endpoint: "vpn/ike-proposals",
	},
	"vpn.ipsecpolicy": {
		Name:     "IPSecPolicy",
		Endpoint: "vpn/ipsec-policies",
	},
	"vpn.ipsecprofile": {
		Name:     "IPSecProfile",
		Endpoint: "vpn/ipsec-profiles",
	},
	"vpn.ipsecproposal": {
		Name:     "IPSecProposal",
		Endpoint: "vpn/ipsec-proposals",
	},
	"vpn.l2vpn": {
		Name:     "L2VPN",
		Endpoint: "vpn/l2vpns",
	},
	"vpn.l2vpntermination": {
		Name:     "L2VPNTermination",
		Endpoint: "vpn/l2vpn-terminations",
	},
	"vpn.tunnel": {
		Name:     "Tunnel",
		Endpoint: "vpn/tunnels",
	},
	"vpn.tunnelgroup": {
		Name:     "TunnelGroup",
		Endpoint: "vpn/tunnel-groups",
	},
	"vpn.tunneltermination": {
		Name:     "TunnelTermination",
		Endpoint: "vpn/tunnel-terminations",
	},
	"wireless.wirelesslan": {
		Name:     "WirelessLAN",
		Endpoint: "wireless/wireless-lans",
	},
	"wireless.wirelesslangroup": {
		Name:     "WirelessLANGroup",
		Endpoint: "wireless/wireless-lan-groups",
	},
	"wireless.wirelesslink": {
		Name:     "WirelessLink",
		Endpoint: "wireless/wireless-links",
	},
}
