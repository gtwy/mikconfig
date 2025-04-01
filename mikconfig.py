#!/usr/bin/env python3
"""
Script: mikconfig.py
Description: Unified MikroTik configuration generator.
             This script offers a menu with six options:

wAP AX system:
1. CAPsMAN 2.0 config
2. WAP config

wAP AC system upgrade:
3. CAPsMAN 2.0 upgrade config
4. WAP upgrade config

Additional scripts:
5. New switch (no CAPsMAN)
6. Set identity and IP address only

Usage: Run this script and choose an option from the menu.
       Follow the prompts (if applicable) and copy the output commands into the MikroTik console.
"""

import ipaddress
import sys

def get_ip_config():
    # Helper function to prompt for IP configuration with defaults and extrapolation.
    default_ip = "10.1.27.2/24"
    default_network = "10.1.27.0"
    default_gateway = "10.1.27.1"
    default_dns = "8.8.8.8,8.8.4.4"
    subnet_choice = input("Enter Subnet Information? (Y/N): ").strip().lower()
    if subnet_choice == 'y':
        ip_input = input(f"IP Address [default: {default_ip}]: ").strip()
        if not ip_input:
            ip_input = default_ip
        try:
            ip_intf = ipaddress.ip_interface(ip_input)
        except Exception as e:
            print("Invalid IP address format, using default.")
            ip_input = default_ip
            ip_intf = ipaddress.ip_interface(ip_input)
        # Compute network and gateway based on the provided IP address
        computed_network = str(ip_intf.network.network_address)
        computed_gateway = str(ipaddress.IPv4Address(int(ip_intf.network.network_address) + 1))
        network_input = input(f"Network [default: {computed_network}]: ").strip()
        if not network_input:
            network_input = computed_network
        gateway_input = input(f"Gateway [default: {computed_gateway}]: ").strip()
        if not gateway_input:
            gateway_input = computed_gateway
        dns_input = input(f"DNS [default: {default_dns}]: ").strip()
        if not dns_input:
            dns_input = default_dns
    else:
        ip_input = default_ip
        network_input = default_network
        gateway_input = default_gateway
        dns_input = default_dns
    return ip_input, network_input, gateway_input, dns_input

def config_capsman2():
    # Option 1: CAPsMAN 2.0 config (switch config)
    print("Please enter the following information:\n")
    identity = input("System Identity (e.g. testnet-switch0): ").strip()
    ssid = input("SSID (e.g. testnet-wifi0): ").strip()
    passphrase = input("Passphrase (e.g. Qaqa1234@): ").strip()
    ip_input, network_input, gateway_input, dns_input = get_ip_config()

    config = f"""## make sure winbox is up to date
## connect with winbox via MAC address, no pw
## do not set password, skip
## in gui > files
## drag corresponding firmware update to files (usually "arm", "arm64", or "mipsbe")
## in gui > system > reboot (nearly 3 minutes)

## if firmware update doesn't take, use system > packages to check for update. requires working internet first

## open up console and change password for first time

/system identity
set name={identity}

/ip address remove [find comment="defconf"]

/ip dhcp-client
add interface=bridge

/system clock
set time-zone-name=America/New_York

/system note
set show-at-login=no

/system ntp client
set enabled=yes

/system ntp client servers
add address=0.opnsense.pool.ntp.org
add address=1.opnsense.pool.ntp.org
add address=2.opnsense.pool.ntp.org
add address=3.opnsense.pool.ntp.org

/interface wifi datapath
add bridge=bridge client-isolation=no disabled=no name=flat_datapath

/interface wifi configuration
add channel.reselect-interval=45m..1h30m .skip-dfs-channels=10min-cac \\
    country="United States" datapath=flat_datapath disabled=no mode=ap \\
    multicast-enhance=enabled name={ssid} \\
    security.authentication-types=wpa2-psk,wpa3-psk .encryption=ccmp \\
    .passphrase="{passphrase}" .ft=yes \\
    .ft-mobility-domain=0xB33F .ft-over-ds=yes .group-key-update=2h \\
    steering.rrm=yes .wnm=yes ssid={ssid} station-roaming=yes

/interface wifi provisioning
add action=create-dynamic-enabled comment=5ghz disabled=no identity-regexp="" \\
    master-configuration={ssid} name-format=5ghz-%I supported-bands=\\
    5ghz-ax,5ghz-ac,5ghz-n
add action=create-dynamic-enabled comment=2ghz disabled=no \\
    master-configuration={ssid} name-format=2ghz-%I supported-bands=\\
    2ghz-ax,2ghz-n

/interface bridge
set bridge protocol-mode=rstp priority=0x3000 port-cost-mode=long
/interface ethernet
set [ find ] loop-protect=on

## DOCUMENT SERIAL NUMBER
/system routerboard print

## SET STATIC IP ADDRESS
/ip dhcp-client remove [find interface="bridge"]
/ip address
add address={ip_input} comment=defconf interface=bridge network={network_input}
/ip dns
set servers={dns_input}
/ip route
add disabled=no dst-address=0.0.0.0/0 gateway={gateway_input}

## ENABLE CAPsMAN
/interface wifi capsman
set ca-certificate=auto certificate=auto enabled=yes interfaces=all \\
    package-path="" require-peer-certificate=no upgrade-policy=none

## SELECT NEIGHBOR GROUP
# gui > WiFi > Configuration > double click on wifi config
# Steering > Neighbor Group > select dynamic-whatever from drop down menu
"""
    print("\n" + "="*60)
    print("MikroTik switch config w/ CAPsMAN 2.0")
    print("="*60 + "\n")
    print(config)

def config_wap2():
    # Option 2: WAP config (wAP AX system)
    identity = input("System Identity (e.g. testnet-wap0): ").strip()
    config = f"""## ethernet cable goes into left port
## hold the reset button before connecting power (or ethernet if PoE)
## reset light will go solid for 5 seconds, flash for 5 seconds
## when it stops flashing, immediately release

## (45 second wait)

## connect via winbox

## password is in booklet. e.g. OMPRN69OYT
## save password in notepad, you'll need it again
## don't bother changing

## manual firmware update seems to fail, have to do it through gui
## gui > system > packages > update (check for updates, go to latest stable)

## (2-3 minute wait)

## connect again with winbox
## use the default password again, do not reset

## open up console and change password for first time

/system identity
set name={identity}

/ip address remove [find comment="defconf"]
/ip dhcp-client
add interface=bridgeLocal

/system clock
set time-zone-name=America/New_York
/system note
set show-at-login=no
/system ntp client
set enabled=yes
/system ntp client servers
add address=0.opnsense.pool.ntp.org
add address=1.opnsense.pool.ntp.org
add address=2.opnsense.pool.ntp.org
add address=3.opnsense.pool.ntp.org

/interface bridge
set bridgeLocal protocol-mode=rstp priority=0x8000 port-cost-mode=long
/interface ethernet
set [ find ] loop-protect=on

## DOCUMENT SERIAL NUMBER
/system routerboard print
"""
    print("\n" + "="*60)
    print("MikroTik wAP AX (CAPsMAN 2.0) config")
    print("="*60 + "\n")
    print(config)

def upgrade_cap():
    # Option 3: CAPsMAN 2.0 upgrade config (wAP AC system upgrade)
    ssid = input("SSID (e.g. testnet-wifi0): ").strip()
    passphrase = input("Passphrase (e.g. Qaqa1234@): ").strip()
    config = rf"""## REMOVE ALL CAPSMAN 1.0 CONFIGURATION
/caps-man security remove [find]
/caps-man configuration remove [find]
/caps-man provisioning remove [find]
/caps-man channels remove [find]
/caps-man interface remove [find]
/caps-man manager remove [find]

## DO THROUGH GUI
# full firmware update (automatic reboot)
# mark wireless package for uninstall

## REBOOT
/system reboot

## PASTE THESE COMMANDS TO COMPLETE PROVISIONING
/interface wifi datapath
add bridge=bridge client-isolation=no disabled=no name=flat_datapath
/interface wifi configuration
add channel.reselect-interval=45m..1h30m .skip-dfs-channels=10min-cac country=\
    "United States" datapath=flat_datapath disabled=no mode=ap \
    multicast-enhance=enabled name={ssid} security.authentication-types=\
    wpa2-psk .encryption=ccmp .passphrase="{passphrase}" .ft=no \
    .ft-mobility-domain=0xB33F .ft-over-ds=yes .group-key-update=2h ssid=\
    {ssid} station-roaming=yes steering.rrm=yes .wnm=yes
/interface wifi capsman
set ca-certificate=auto certificate=auto enabled=yes interfaces=all \
    package-path="" require-peer-certificate=no upgrade-policy=none
/interface wifi provisioning
add action=create-dynamic-enabled comment=5ghz disabled=no \
    master-configuration={ssid} name-format=5ghz-%I supported-bands=\
    5ghz-ac,5ghz-n
add action=create-dynamic-enabled comment=2ghz disabled=no \
    master-configuration={ssid} name-format=2ghz-%I supported-bands=2ghz-n

/interface bridge
set bridge protocol-mode=rstp priority=0x3000 port-cost-mode=long
/interface ethernet
set [ find ] loop-protect=on

## SELECT NEIGHBOR GROUP
# gui > WiFi > Configuration > double click on wifi config
# Steering > Neighbor Group > select dynamic-whatever from drop down menu
# then go to Remote CAP and reprovision all radios (or power cycle everything)
"""
    print("\n" + "="*60)
    print("MikroTik switch config to upgrade CAPsMAN 1.0 to CAPsMAN 2.0")
    print("="*60 + "\n")
    print(config)

def upgrade_wap():
    # Option 4: WAP upgrade config (wAP AC system upgrade)
    config = """## DO THROUGH GUI
# full firmware update (automatic reboot)
# mark wireless package for uninstall
# drag qcom-wifi-ac package into files

## REBOOT
/system reboot

## PASTE THESE COMMANDS TO COMPLETE PROVISIONING
/interface wifi cap set enabled=yes discovery-interfaces=bridgeLocal
/interface wifi
set [ find default-name=wifi1 ] configuration.manager=capsman .mode=ap disabled=no
set [ find default-name=wifi2 ] configuration.manager=capsman .mode=ap disabled=no
/interface bridge port
add bridge=bridgeLocal interface=wifi1
add bridge=bridgeLocal interface=wifi2
/interface bridge
set bridgeLocal protocol-mode=rstp priority=0x8000 port-cost-mode=long
/interface ethernet
set [ find ] loop-protect=on
"""
    print("\n" + "="*60)
    print("MikroTik wAP AC (CAPsMAN 2.0) upgrade config")
    print("="*60 + "\n")
    print(config)

def config_new_switch():
    # Option 5: New switch (no CAPsMAN)
    print("Please enter the following information:\n")
    identity = input("System Identity (e.g. testnet-switch0): ").strip()
    ip_input, network_input, gateway_input, dns_input = get_ip_config()
    config = f"""## make sure winbox is up to date
## connect with winbox via MAC address, no pw
## do not set password, skip
## in gui > files
## drag corresponding firmware update to files (usually "arm", "arm64", or "mipsbe")
## in gui > system > reboot (nearly 3 minutes)

## if firmware update doesn't take, use system > packages to check for update. requires working internet first

## open up console and change password for first time

/system identity
set name={identity}

/ip address remove [find comment="defconf"]

/ip dhcp-client
add interface=bridge

/system clock
set time-zone-name=America/New_York

/system note
set show-at-login=no

/system ntp client
set enabled=yes

/system ntp client servers
add address=0.opnsense.pool.ntp.org
add address=1.opnsense.pool.ntp.org
add address=2.opnsense.pool.ntp.org
add address=3.opnsense.pool.ntp.org

/interface bridge
set bridge protocol-mode=rstp priority=0x3000 port-cost-mode=long
/interface ethernet
set [ find ] loop-protect=on

## DOCUMENT SERIAL NUMBER
/system routerboard print

## SET STATIC IP ADDRESS
/ip dhcp-client remove [find interface="bridge"]
/ip address
add address={ip_input} comment=defconf interface=bridge network={network_input}
/ip dns
set servers={dns_input}
/ip route
add disabled=no dst-address=0.0.0.0/0 gateway={gateway_input}
"""
    print("\n" + "="*60)
    print("MikroTik New Switch (no CAPsMAN) config")
    print("="*60 + "\n")
    print(config)

def config_identity_ip_only():
    # Option 6: Set identity and IP address only
    print("Please enter the following information:\n")
    identity = input("System Identity (e.g. testnet-switch0): ").strip()
    ip_input, network_input, gateway_input, dns_input = get_ip_config()
    config = f"""## SET IDENTITY
/system identity
set name={identity}

## SET STATIC IP ADDRESS
/ip dhcp-client remove [find interface="bridge"]
/ip address remove [find comment="defconf"]
/ip address
add address={ip_input} comment=defconf interface=bridge network={network_input}
/ip dns
set servers={dns_input}
/ip route
add disabled=no dst-address=0.0.0.0/0 gateway={gateway_input}
"""
    print("\n" + "="*60)
    print("MikroTik Identity and IP Address Only config")
    print("="*60 + "\n")
    print(config)

def main_menu():
    menu = """
==============================
MikroTik Configuration Generator
==============================

wAP AX system:
1. CAPsMAN 2.0 config
2. WAP config

wAP AC system upgrade:
3. CAPsMAN 2.0 upgrade config
4. WAP upgrade config

Additional scripts:
5. New switch (no CAPsMAN)
6. Set identity and IP address only

Enter your choice (1-6): """
    choice = input(menu).strip()

    if choice == '1':
        config_capsman2()
    elif choice == '2':
        config_wap2()
    elif choice == '3':
        upgrade_cap()
    elif choice == '4':
        upgrade_wap()
    elif choice == '5':
        config_new_switch()
    elif choice == '6':
        config_identity_ip_only()
    else:
        print("Invalid option. Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    main_menu()

