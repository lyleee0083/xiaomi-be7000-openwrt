include $(TOPDIR)/rules.mk
include $(INCLUDE_DIR)/version.mk

PKG_NAME:=ipq-wifi
PKG_RELEASE:=1

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL=$(PROJECT_GIT)/project/firmware/qca-wireless.git
PKG_SOURCE_DATE:=2026-10-25
PKG_SOURCE_VERSION:=49ce14c099b16044b7062df54bdabeb495b804ad
PKG_SOURCE_SUBDIR:=$(PKG_NAME)-$(subst -,.,$(PKG_SOURCE_DATE))~$(call version_abbrev,$(PKG_SOURCE_VERSION))
PKG_SOURCE:=$(PKG_SOURCE_SUBDIR).tar.zst
PKG_MIRROR_HASH:=b9c6723021af9267035b7e25762b80c06887a5ea9c524b2649b0b27ea58b121c
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)
PKG_FLAGS:=nonshared

include $(INCLUDE_DIR)/package.mk

define Build/Prepare
	$(call Build/Prepare/Default)
	[ ! -d ./files/ ] || $(CP) ./files/. $(PKG_BUILD_DIR)/
endef

define Build/Compile
endef

ALLWIFIBOARDS := xiaomi_be7000
ALLWIFIPACKAGES := $(foreach BOARD,$(ALLWIFIBOARDS),ipq-wifi-$(BOARD))

define Package/ipq-wifi-default
  SUBMENU:=ath10k Board-Specific Overrides
  SECTION:=firmware
  CATEGORY:=Firmware
  DEPENDS:=@TARGET_qualcommbe
  TITLE:=Custom Board
endef

define ipq-wifi-install-ath11-one-to
  $(INSTALL_DIR)  $(2)/lib/firmware/ath11k/$(3)/
  $(INSTALL_DATA) $(1) $(2)/lib/firmware/ath11k/$(3)/board-2.bin
endef

define ipq-wifi-install-ath12-one-to
  $(INSTALL_DIR)  $(2)/lib/firmware/ath12k/$(3)/
  $(INSTALL_DATA) $(1) $(2)/lib/firmware/ath12k/$(3)/board-2.bin
endef

define ipq-wifi-install-one
  $(if $(filter $(suffix $(1)),.IPQ9574 .ipq9574),\
    $(call ipq-wifi-install-ath11-one-to,$(1),$(2),IPQ9574/hw1.0),\
  $(if $(filter $(suffix $(1)),.QCN9274 .qcn9274),\
    $(call ipq-wifi-install-ath12-one-to,$(1),$(2),QCN9274/hw2.0),\
    $(error Unrecognized board-file suffix '$(suffix $(1))' for '$(1)')\
  ))

endef
# Blank line required at end of above define due to foreach context

define generate-ipq-wifi-package
  define Package/ipq-wifi-$(1)
    $(call Package/ipq-wifi-default)
    TITLE:=board-2.bin Overrides for $(2)
  endef

  define Package/ipq-wifi-$(1)/description
The $(2) requires board-specific reference board-2.bin data
for IPQ9574 (ath11k) and QCN9274 (ath12k).
  endef

  define Package/ipq-wifi-$(1)/install-overlay
    $$$$(foreach IPQ_WIFI_BOARD_FILE,$$$$(wildcard $(PKG_BUILD_DIR)/board-$(1).*),\
      $$$$(call ipq-wifi-install-one,$$$$(IPQ_WIFI_BOARD_FILE),$$(1)))
  endef
endef

$(eval $(call generate-ipq-wifi-package,xiaomi_be7000,Xiaomi BE7000))

$(foreach PACKAGE,$(ALLWIFIPACKAGES),$(eval $(call BuildPackage,$(PACKAGE))))
