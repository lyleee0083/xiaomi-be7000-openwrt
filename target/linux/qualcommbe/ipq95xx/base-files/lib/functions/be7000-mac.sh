#!/bin/sh

be7000_valid_mac() {
	local mac first
	mac=$(macaddr_canonicalize "$1") || return 1
	[ -n "$mac" ] && [ "$mac" != 00:00:00:00:00:00 ] && [ "$mac" != ff:ff:ff:ff:ff:ff ] || return 1
	first=${mac%%:*}
	[ $((0x$first & 1)) -eq 0 ] || return 1
	printf '%s\n' "$mac"
}

be7000_read_art_mac() {
	local offset="$1" part=""
	if [ -n "${BE7000_ART_FILE:-}" ] && [ -r "$BE7000_ART_FILE" ]; then
		hexdump -v -n 6 -s "$offset" -e '5/1 "%02x:" "%02x"' "$BE7000_ART_FILE" 2>/dev/null
		return $?
	fi
	if [ -n "$(find_mtd_index 0:art 2>/dev/null)" ]; then
		part="0:art"
	elif [ -n "$(find_mtd_index 0:ART 2>/dev/null)" ]; then
		part="0:ART"
	else
		return 1
	fi
	mtd_get_mac_binary "$part" "$offset" 2>/dev/null
}

be7000_load_port_macs() {
	local reserved="$1" raw0 raw1 raw2 raw3 wifi2g wifi5g base="" all used=""
	local index raw candidate local_base first step
	BE7000_MAC_READY=0
	BE7000_MAC0= BE7000_MAC1= BE7000_MAC2= BE7000_MAC3=
	raw0=$(be7000_valid_mac "$(be7000_read_art_mac 0)") || raw0=""
	raw1=$(be7000_valid_mac "$(be7000_read_art_mac 6)") || raw1=""
	raw2=$(be7000_valid_mac "$(be7000_read_art_mac 12)") || raw2=""
	raw3=$(be7000_valid_mac "$(be7000_read_art_mac 18)") || raw3=""
	wifi2g=$(be7000_valid_mac "$(be7000_read_art_mac 4110)") || wifi2g=""
	wifi5g=$(be7000_valid_mac "$(be7000_read_art_mac 413712)") || wifi5g=""
	for raw in "$raw0" "$raw1" "$raw2" "$raw3"; do
		[ -z "$raw" ] || { base="$raw"; break; }
	done
	if [ -z "$base" ]; then
		logger -p daemon.warn -t be7000-mac "No valid ART wired MAC; preserving native network defaults"
		return 2
	fi
	first=${base%%:*}
	local_base=$(printf '%02x:%s' "$((0x$first | 2))" "${base#*:}")
	all=" $raw0 $raw1 $raw2 $raw3 $wifi2g $wifi5g $reserved "
	for index in 0 1 2 3; do
		eval 'raw=$raw'"$index"
		case " $used $wifi2g $wifi5g $reserved " in *" $raw "*) raw="" ;; esac
		if [ -n "$raw" ]; then
			candidate="$raw"
		else
			step=$((256 + index))
			while :; do
				candidate=$(be7000_valid_mac "$(macaddr_add "$local_base" "$step")") || return 1
				case "$all $used " in
					*" $candidate "*) step=$((step + 1)) ;;
					*) break ;;
				esac
				[ "$step" -lt 65536 ] || return 1
			done
		fi
		eval 'BE7000_MAC'"$index"'=$candidate'
		used="$used $candidate"
	done
	BE7000_MAC_READY=1
}

be7000_port_mac() {
	[ "${BE7000_MAC_READY:-0}" = 1 ] || return 1
	case "$1" in
		wan) printf '%s\n' "$BE7000_MAC0" ;;
		lan1) printf '%s\n' "$BE7000_MAC1" ;;
		lan2) printf '%s\n' "$BE7000_MAC2" ;;
		lan3) printf '%s\n' "$BE7000_MAC3" ;;
		*) return 1 ;;
	esac
}

be7000_mac_uci() {
	uci -t "$BE7000_MAC_STAGE" "$@"
}

be7000_collect_state() {
	local section="$1" name mac
	config_get name "$section" name
	config_get mac "$section" macaddr
	case "$name" in
		wan|lan1|lan2|lan3)
			eval "BE7000_DEV_SEC_${name}=\$section"
			if mac=$(be7000_valid_mac "$mac"); then
				eval "BE7000_DEV_MAC_${name}=\$mac"
			fi
			;;
		br-lan)
			BE7000_DEV_SEC_BRLAN="$section"
			if mac=$(be7000_valid_mac "$mac"); then
				BE7000_EXISTING_BR_LAN="$mac"
			fi
			;;
		*)
			if mac=$(be7000_valid_mac "$mac"); then
				BE7000_RESERVED_MACS="$BE7000_RESERVED_MACS $mac"
			fi
			;;
	esac
}

be7000_collect_iface_reserved() {
	local section="$1" mac
	config_get mac "$section" macaddr
	mac=$(be7000_valid_mac "$mac") || return 0
	case "$section" in
		lan) [ -n "$BE7000_EXISTING_BR_LAN" ] || BE7000_EXISTING_BR_LAN="$mac" ;;
		wan) ;;
		*) BE7000_RESERVED_MACS="$BE7000_RESERVED_MACS $mac" ;;
	esac
}

be7000_ensure_device_mac() {
	local devname="$1" target="$2" sec="$3" cur="$4" peer_macs="$5" new_sec
	if [ -n "$cur" ]; then
		case " $peer_macs " in
			*" $cur "*) cur="" ;;
		esac
	fi
	if [ -n "$sec" ] && [ -n "$cur" ]; then
		printf '%s\n' "$cur"
		return 0
	fi
	if [ -z "$sec" ]; then
		new_sec=$(be7000_mac_uci add network device) || return 1
		be7000_mac_uci set "network.$new_sec.name=$devname" || return 1
		sec="$new_sec"
	fi
	be7000_mac_uci set "network.$sec.macaddr=$target" || return 1
	BE7000_MAC_CHANGED=1
	printf '%s\n' "$target"
}

be7000_apply_network_macs() {
	local mac_status p cur sec target assigned="" lan1_final
	BE7000_RESERVED_MACS= BE7000_EXISTING_BR_LAN=
	BE7000_DEV_SEC_wan= BE7000_DEV_SEC_lan1= BE7000_DEV_SEC_lan2= BE7000_DEV_SEC_lan3= BE7000_DEV_SEC_BRLAN=
	BE7000_DEV_MAC_wan= BE7000_DEV_MAC_lan1= BE7000_DEV_MAC_lan2= BE7000_DEV_MAC_lan3=
	BE7000_MAC_CHANGED=0
	config_load network || return 1
	config_foreach be7000_collect_state device
	config_foreach be7000_collect_iface_reserved interface
	for p in wan lan1 lan2 lan3; do
		eval "cur=\$BE7000_DEV_MAC_${p}"
		[ -z "$cur" ] || BE7000_RESERVED_MACS="$BE7000_RESERVED_MACS $cur"
	done
	[ -z "$BE7000_EXISTING_BR_LAN" ] || BE7000_RESERVED_MACS="$BE7000_RESERVED_MACS $BE7000_EXISTING_BR_LAN"
	be7000_load_port_macs "$BE7000_RESERVED_MACS"
	mac_status=$?
	if [ "$mac_status" -eq 2 ]; then
		return 0
	fi
	[ "$mac_status" -eq 0 ] || return 1

	lan1_final=""
	for p in wan lan1 lan2 lan3; do
		eval "sec=\$BE7000_DEV_SEC_${p}"
		eval "cur=\$BE7000_DEV_MAC_${p}"
		target=$(be7000_port_mac "$p") || return 1
		cur=$(be7000_ensure_device_mac "$p" "$target" "$sec" "$cur" "$assigned") || return 1
		assigned="$assigned $cur"
		[ "$p" != lan1 ] || lan1_final="$cur"
	done

	if [ -n "$BE7000_DEV_SEC_BRLAN" ] && [ -z "$BE7000_EXISTING_BR_LAN" ]; then
		be7000_mac_uci set "network.$BE7000_DEV_SEC_BRLAN.macaddr=${lan1_final:-$BE7000_MAC1}" || return 1
		BE7000_MAC_CHANGED=1
	fi

	if [ "$BE7000_MAC_CHANGED" = 1 ]; then
		[ -z "$(uci -q changes network)" ] || return 1
		be7000_mac_uci commit network || return 1
	fi
	return 0
}

be7000_fix_network_macs() {
	(
		[ "$(cat /tmp/sysinfo/board_name 2>/dev/null)" = xiaomi,be7000 ] || return 0
		[ -z "$(uci -q changes network)" ] || {
			logger -p daemon.warn -t be7000-mac "Pending network edits; deferring MAC repair"
			return 1
		}
		umask 077
		BE7000_MAC_STAGE=$(mktemp -d /tmp/be7000-mac.XXXXXX) || return 1
		trap 'rm -f "$BE7000_MAC_STAGE/network"; rmdir "$BE7000_MAC_STAGE" 2>/dev/null' EXIT
		trap 'exit 1' HUP INT TERM
		be7000_apply_network_macs
	)
}
