#!/bin/bash

# ----------------------------
# Configuration
# ----------------------------

# INTERFACE=${INTERFACE:-$(ip route | awk '/default/ {print $5}')}
do_get_SERVER_HOST() {
   possible_HOST_IP=$(hostname -I | awk '{print $1}')
   UDP_SERVER_HOST=$(whiptail --inputbox "Please configure the server host IP for the LoRaWAN UDP packet forwarder and TTS service. You can check the OLED screen on the enclosure to get the IP." 10 60 $possible_HOST_IP --title "Host IP" 3>&1 1>&2 2>&3)
   exitstatus=$?
   if [ $exitstatus = 0 ]; then
      echo "Server Host is configured to: " $UDP_SERVER_HOST
   else
      echo "User selected Cancel."
      exit 0
   fi
}
do_get_GATEWAY_EUI() {
   if [[ -f /app/config/station.conf ]]; then
      GATEWAY_EUI=$(cat /app/config/station.conf | jq '.station_conf.routerid' | sed 's/"//g')
   else
      GATEWAY_EUI_NIC=${GATEWAY_EUI_NIC:-"eth0"}
      if [[ $(grep "$GATEWAY_EUI_NIC" /proc/net/dev) == "" ]]; then
         GATEWAY_EUI_NIC="eth0"
      fi
      if [[ $(grep "$GATEWAY_EUI_NIC" /proc/net/dev) == "" ]]; then
         GATEWAY_EUI_NIC="wlan0"
      fi
      if [[ $(grep "$GATEWAY_EUI_NIC" /proc/net/dev) == "" ]]; then
         GATEWAY_EUI_NIC="usb0"
      fi
      if [[ $(grep "$GATEWAY_EUI_NIC" /proc/net/dev) == "" ]]; then
         # Last chance: get the most used NIC based on received bytes
         GATEWAY_EUI_NIC=$(cat /proc/net/dev | tail -n+3 | sort -k2 -nr | head -n1 | cut -d ":" -f1 | sed 's/ //g')
      fi
      if [[ $(grep "$GATEWAY_EUI_NIC" /proc/net/dev) == "" ]]; then
         echo -e "\033[91mERROR: No network interface found. Cannot set gateway EUI.\033[0m"
      fi
      GATEWAY_EUI=$(ip link show $GATEWAY_EUI_NIC | awk '/ether/ {print $2}' | awk -F\: '{print $1$2$3"FFFE"$4$5$6}')
   fi
}
do_get_SERVER_HOST
do_get_GATEWAY_EUI

COLOR_SUMMARY="\e[1;32m" # bold green on black
COLOR_ERROR="\e[31m"     # red
COLOR_END="\e[0m"

# ----------------------------
# Tasks
# ----------------------------

# Modify docker-compose.yml file
echo -e "${COLOR_SUMMARY}Configuring docker-compose.yml file${COLOR_END}"
sed "s/GATEWAY_EUI: \".*\"/GATEWAY_EUI: \"$GATEWAY_EUI\"/g" -i docker-compose.yml
sed "s/TTS_DOMAIN: .*/TTS_DOMAIN: $UDP_SERVER_HOST/g" -i docker-compose.yml
sed "s/SERVER_HOST: .*/SERVER_HOST: $UDP_SERVER_HOST/g" -i docker-compose.yml
sed "s#address: .*#address: ${UDP_SERVER_HOST}#g" -i BACpypes.ini

echo -e "${COLOR_SUMMARY}Getting container images and services ready...${COLOR_END}"
docker compose up -d

echo -e "${COLOR_SUMMARY}"
echo "---------------------------------------------------------------------"
echo "Gateway EUI  : $GATEWAY_EUI"
echo "Stack URL    : https://${UDP_SERVER_HOST}/       (admin/changeme)"
echo "The next step is to run ./BACnet-out.py"
echo "---------------------------------------------------------------------"
echo -e "${COLOR_END}"
