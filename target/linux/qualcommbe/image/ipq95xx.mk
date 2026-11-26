DTS_DIR := $(DTS_DIR)/qcom

define Device/xiaomi_be7000
	$(call Device/FitImage)
	$(call Device/UbiFit)
	DEVICE_VENDOR := Xiaomi
	DEVICE_MODEL := BE7000
	DEVICE_DTS_CONFIG := config@al02-c6
	SOC := ipq9554
	BLOCKSIZE := 128k
	PAGESIZE := 2048
	DEVICE_PACKAGES := kmod-ath11k-ahb ath11k-firmware-ipq9574-ddwrt \
		kmod-ath12k ath12k-firmware-qcn9274-ddwrt \
		ipq-wifi-xiaomi_be7000
	SUPPORTED_DEVICES += xiaomi,be7000
endef
TARGET_DEVICES += xiaomi_be7000
