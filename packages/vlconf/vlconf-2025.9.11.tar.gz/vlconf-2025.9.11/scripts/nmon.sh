#/usr/bin/env bash
# Bash script to monitor the wifi accesspoint connectivity
# and trigger reconnect if unresponsive, every 5 seconds.
# Outputs the BSSID when changed, and the time stamp.

bssid=$(nmcli dev wifi list | grep "*" | awk '{print $2}')
echo $bssid
while true; do
	newbssid=$(nmcli dev wifi list | grep "*" | awk '{print $2}');
	# echo $newbssid
	if [ "$newbssid" != "$bssid" ]; then
		echo -e "\a"
		## echo -e "\007"
		echo "BSSID changed"
		echo $newbssid
	fi
	bssid=$newbssid

	ping -c 1 google.com &> /dev/null
	if [ $? -eq 0 ]; then
		:
  		# echo "Host is reachable (0)"
	else
  		echo "Host is unreachable or error occurred (1)"
		date
		rebssid=$(nmcli dev wifi list | grep "eduroam" | awk 'NR==1{print $1}')
		nmcli dev wifi connect eduroam bssid $rebssid
	fi

	sleep 5
done


	
