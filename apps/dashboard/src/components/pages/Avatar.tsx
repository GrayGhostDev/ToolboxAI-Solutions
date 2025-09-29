IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../../IconutilsIcon/IconmuiIcon-Iconimports';
IconimportIcon * IconasIcon IconReactIcon IconfromIcon "Iconreact";

IconimportIcon { IconuseStateIcon } IconfromIcon "Iconreact";
IconimportIcon {
  IconIconMoodSmileIcon,
  IconIconColorLensIcon,
  IconIconCheckroomIcon,
  IconIconEmojiEventsIcon,
  IconIconLockIcon,
  IconIconLockOpenIcon,
  IconIconDeviceFloppyIcon,
  IconIconRefreshIcon,
  IconIconCameraIcon,
  IconIconEditIcon,
  IconIconShoppingCartIcon,
  IconIconStarIcon,
} IconfromIcon "@IconmuiIcon/IconiconsIcon-Iconmaterial";
IconimportIcon { IconuseAppSelectorIcon, IconuseAppDispatchIcon } IconfromIcon "../../Iconstore";
IconimportIcon { IconaddNotificationIcon } IconfromIcon "../../IconstoreIcon/IconslicesIcon/IconuiSlice";
IconimportIcon { IconIconIcon, IconIconCameraIcon, IconIconCheckroomIcon, IconIconColorLensIcon, IconIconDeviceFloppyIcon, IconIconEditIcon, IconIconEmojiEventsIcon, IconIconLockIcon, IconIconLockOpenIcon, IconIconMoodSmileIcon, IconIconRefreshIcon, IconIconShoppingCartIcon, IconIconStarIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';

IconinterfaceIcon IconAvatarCategoryIcon {
  IconidIcon: IconstringIcon;
  IconnameIcon: IconstringIcon;
  IconiconIcon: IconReactIcon.IconReactNodeIcon;
  IconitemsIcon: IconAvatarItemIcon[];
}

IconinterfaceIcon IconAvatarItemIcon {
  IconidIcon: IconstringIcon;
  IconnameIcon: IconstringIcon;
  IconpreviewIcon: IconstringIcon;
  IconcategoryIcon: IconstringIcon;
  IconrarityIcon: "Iconcommon" | "Iconrare" | "Iconepic" | "Iconlegendary";
  IconxpCostIcon: IconnumberIcon;
  IconlevelRequiredIcon: IconnumberIcon;
  IconownedIcon: IconbooleanIcon;
  IconequippedIcon: IconbooleanIcon;
}

IconconstIcon IconAVATAR_CATEGORIESIcon: IconAvatarCategoryIcon[] = [
  {
    IconidIcon: "Iconhairstyles",
    IconnameIcon: "IconHairstyles",
    IconiconIcon: <IconIconMoodSmileIcon />,
    IconitemsIcon: [
      { IconidIcon: "Iconhair_1", IconnameIcon: "IconShortIcon & IconNeat", IconpreviewIcon: "👱", IconcategoryIcon: "Iconhairstyles", IconrarityIcon: "Iconcommon", IconxpCostIcon: Icon0Icon, IconlevelRequiredIcon: Icon1Icon, IconownedIcon: IcontrueIcon, IconequippedIcon: IcontrueIcon },
      { IconidIcon: "Iconhair_2", IconnameIcon: "IconLongIcon & IconWavy", IconpreviewIcon: "👩", IconcategoryIcon: "Iconhairstyles", IconrarityIcon: "Iconcommon", IconxpCostIcon: Icon50Icon, IconlevelRequiredIcon: Icon2Icon, IconownedIcon: IcontrueIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconhair_3", IconnameIcon: "IconMohawk", IconpreviewIcon: "🎸", IconcategoryIcon: "Iconhairstyles", IconrarityIcon: "Iconrare", IconxpCostIcon: Icon150Icon, IconlevelRequiredIcon: Icon5Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconhair_4", IconnameIcon: "IconRainbowIcon IconSpikes", IconpreviewIcon: "🌈", IconcategoryIcon: "Iconhairstyles", IconrarityIcon: "Iconepic", IconxpCostIcon: Icon300Icon, IconlevelRequiredIcon: Icon10Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconhair_5", IconnameIcon: "IconGalaxyIcon IconHair", IconpreviewIcon: "🌌", IconcategoryIcon: "Iconhairstyles", IconrarityIcon: "Iconlegendary", IconxpCostIcon: Icon500Icon, IconlevelRequiredIcon: Icon15Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
    ],
  },
  {
    IconidIcon: "Iconoutfits",
    IconnameIcon: "IconOutfits",
    IconiconIcon: <IconIconCheckroomIcon />,
    IconitemsIcon: [
      { IconidIcon: "Iconoutfit_1", IconnameIcon: "IconSchoolIcon IconUniform", IconpreviewIcon: "👔", IconcategoryIcon: "Iconoutfits", IconrarityIcon: "Iconcommon", IconxpCostIcon: Icon0Icon, IconlevelRequiredIcon: Icon1Icon, IconownedIcon: IcontrueIcon, IconequippedIcon: IcontrueIcon },
      { IconidIcon: "Iconoutfit_2", IconnameIcon: "IconCasualIcon IconWear", IconpreviewIcon: "👕", IconcategoryIcon: "Iconoutfits", IconrarityIcon: "Iconcommon", IconxpCostIcon: Icon75Icon, IconlevelRequiredIcon: Icon2Icon, IconownedIcon: IcontrueIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconoutfit_3", IconnameIcon: "IconSportsIcon IconJersey", IconpreviewIcon: "🏈", IconcategoryIcon: "Iconoutfits", IconrarityIcon: "Iconrare", IconxpCostIcon: Icon200Icon, IconlevelRequiredIcon: Icon6Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconoutfit_4", IconnameIcon: "IconSpaceIcon IconSuit", IconpreviewIcon: "🚀", IconcategoryIcon: "Iconoutfits", IconrarityIcon: "Iconepic", IconxpCostIcon: Icon400Icon, IconlevelRequiredIcon: Icon12Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconoutfit_5", IconnameIcon: "IconDragonIcon IconArmor", IconpreviewIcon: "🐉", IconcategoryIcon: "Iconoutfits", IconrarityIcon: "Iconlegendary", IconxpCostIcon: Icon750Icon, IconlevelRequiredIcon: Icon20Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
    ],
  },
  {
    IconidIcon: "Iconaccessories",
    IconnameIcon: "IconAccessories",
    IconiconIcon: <IconIconStarIcon />,
    IconitemsIcon: [
      { IconidIcon: "Iconacc_1", IconnameIcon: "IconReadingIcon IconGlasses", IconpreviewIcon: "👓", IconcategoryIcon: "Iconaccessories", IconrarityIcon: "Iconcommon", IconxpCostIcon: Icon25Icon, IconlevelRequiredIcon: Icon1Icon, IconownedIcon: IcontrueIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconacc_2", IconnameIcon: "IconCoolIcon IconSunglasses", IconpreviewIcon: "🕶️", IconcategoryIcon: "Iconaccessories", IconrarityIcon: "Iconcommon", IconxpCostIcon: Icon50Icon, IconlevelRequiredIcon: Icon3Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconacc_3", IconnameIcon: "IconMagicIcon IconHat", IconpreviewIcon: "🎩", IconcategoryIcon: "Iconaccessories", IconrarityIcon: "Iconrare", IconxpCostIcon: Icon175Icon, IconlevelRequiredIcon: Icon7Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconacc_4", IconnameIcon: "IconCrownIcon IconofIcon IconWisdom", IconpreviewIcon: "👑", IconcategoryIcon: "Iconaccessories", IconrarityIcon: "Iconepic", IconxpCostIcon: Icon350Icon, IconlevelRequiredIcon: Icon14Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconacc_5", IconnameIcon: "IconPhoenixIcon IconWings", IconpreviewIcon: "🔥", IconcategoryIcon: "Iconaccessories", IconrarityIcon: "Iconlegendary", IconxpCostIcon: Icon600Icon, IconlevelRequiredIcon: Icon18Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
    ],
  },
  {
    IconidIcon: "Iconbackgrounds",
    IconnameIcon: "IconBackgrounds",
    IconiconIcon: <IconIconColorLensIcon />,
    IconitemsIcon: [
      { IconidIcon: "Iconbg_1", IconnameIcon: "IconClassroom", IconpreviewIcon: "🏫", IconcategoryIcon: "Iconbackgrounds", IconrarityIcon: "Iconcommon", IconxpCostIcon: Icon0Icon, IconlevelRequiredIcon: Icon1Icon, IconownedIcon: IcontrueIcon, IconequippedIcon: IcontrueIcon },
      { IconidIcon: "Iconbg_2", IconnameIcon: "IconLibrary", IconpreviewIcon: "📚", IconcategoryIcon: "Iconbackgrounds", IconrarityIcon: "Iconcommon", IconxpCostIcon: Icon40Icon, IconlevelRequiredIcon: Icon2Icon, IconownedIcon: IcontrueIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconbg_3", IconnameIcon: "IconLaboratory", IconpreviewIcon: "🔬", IconcategoryIcon: "Iconbackgrounds", IconrarityIcon: "Iconrare", IconxpCostIcon: Icon125Icon, IconlevelRequiredIcon: Icon5Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconbg_4", IconnameIcon: "IconSpaceIcon IconStation", IconpreviewIcon: "🛸", IconcategoryIcon: "Iconbackgrounds", IconrarityIcon: "Iconepic", IconxpCostIcon: Icon275Icon, IconlevelRequiredIcon: Icon11Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
      { IconidIcon: "Iconbg_5", IconnameIcon: "IconMysticIcon IconPortal", IconpreviewIcon: "🌀", IconcategoryIcon: "Iconbackgrounds", IconrarityIcon: "Iconlegendary", IconxpCostIcon: Icon450Icon, IconlevelRequiredIcon: Icon16Icon, IconownedIcon: IconfalseIcon, IconequippedIcon: IconfalseIcon },
    ],
  },
];

IconexportIcon IcondefaultIcon IconfunctionIcon IconAvatarIcon() {
  IconconstIcon IcondispatchIcon = IconuseAppDispatchIcon();
  IconconstIcon IconuserXPIcon = IconuseAppSelectorIcon((IconsIcon) => IconsIcon.IcongamificationIcon?.IconxpIcon ?? Icon0Icon);
  IconconstIcon IconuserLevelIcon = IconuseAppSelectorIcon((IconsIcon) => IconsIcon.IcongamificationIcon?.IconlevelIcon ?? Icon1Icon);
  
  IconconstIcon [IconselectedCategoryIcon, IconsetSelectedCategoryIcon] = IconuseStateIcon("Iconhairstyles");
  IconconstIcon [IconavatarItemsIcon, IconsetAvatarItemsIcon] = IconuseStateIcon<IconAvatarItemIcon[]>(
    IconAVATAR_CATEGORIESIcon.IconflatMapIcon((IconcatIcon) => IconcatIcon.IconitemsIcon)
  );
  IconconstIcon [IconavatarNameIcon, IconsetAvatarNameIcon] = IconuseStateIcon("IconCoolIcon IconStudent");
  IconconstIcon [IconshowShopIcon, IconsetShowShopIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconavatarSettingsIcon, IconsetAvatarSettingsIcon] = IconuseStateIcon({
    IconshowBadgesIcon: IcontrueIcon,
    IconshowLevelIcon: IcontrueIcon,
    IconanimatedEffectsIcon: IcontrueIcon,
    IconpublicProfileIcon: IcontrueIcon,
  });

  IconconstIcon IconcurrentCategoryIcon = IconAVATAR_CATEGORIESIcon.IconfindIcon((IconcatIcon) => IconcatIcon.IconidIcon === IconselectedCategoryIcon);

  IconconstIcon IconhandleEquipItemIcon = (IconitemIdIcon: IconstringIcon) => {
    IconsetAvatarItemsIcon((IconprevIcon) =>
      IconprevIcon.IconmapIcon((IconitemIcon) => {
        IconifIcon (IconitemIcon.IconidIcon === IconitemIdIcon && IconitemIcon.IconownedIcon) {
          // IconUnequipIcon IconallIcon IconitemsIcon IconinIcon IcontheIcon IconsameIcon IconcategoryIcon, IconthenIcon IconequipIcon IconthisIcon IcononeIcon
          IconconstIcon IconnewEquippedIcon = IconitemIcon.IconcategoryIcon === IconcurrentCategoryIcon?.IconidIcon ? !IconitemIcon.IconequippedIcon : IconitemIcon.IconequippedIcon;
          IconreturnIcon { ...IconitemIcon, IconequippedIcon: IconnewEquippedIcon };
        } IconelseIcon IconifIcon (IconitemIcon.IconcategoryIcon === IconcurrentCategoryIcon?.IconidIcon) {
          IconreturnIcon { ...IconitemIcon, IconequippedIcon: IconfalseIcon };
        }
        IconreturnIcon IconitemIcon;
      })
    );
    
    IcondispatchIcon(IconaddNotificationIcon({
      IconmessageIcon: "IconAvatarIcon IconitemIcon IconequippedIcon!",
      IcontypeIcon: "Iconsuccess",
    }));
  };

  IconconstIcon IconhandlePurchaseItemIcon = (IconitemIcon: IconAvatarItemIcon) => {
    IconifIcon (IconuserXPIcon >= IconitemIcon.IconxpCostIcon && IconuserLevelIcon >= IconitemIcon.IconlevelRequiredIcon) {
      IconsetAvatarItemsIcon((IconprevIcon) =>
        IconprevIcon.IconmapIcon((IconiIcon) => (IconiIcon.IconidIcon === IconitemIcon.IconidIcon ? { ...IconiIcon, IconownedIcon: IcontrueIcon } : IconiIcon))
      );
      
      IcondispatchIcon(IconaddNotificationIcon({
        IconmessageIcon: `IconPurchasedIcon ${IconitemIcon.IconnameIcon} IconforIcon ${IconitemIcon.IconxpCostIcon} IconXPIcon!`,
        IcontypeIcon: "Iconsuccess",
      }));
    } IconelseIcon {
      IcondispatchIcon(IconaddNotificationIcon({
        IconmessageIcon: "IconInsufficientIcon IconXPIcon IconorIcon IconlevelIcon IconrequirementIcon IconnotIcon Iconmet",
        IcontypeIcon: "Iconerror",
      }));
    }
  };

  IconconstIcon IconhandleSaveAvatarIcon = () => {
    // IconInIcon IconproductionIcon, IconthisIcon IconwouldIcon IconsaveIcon IcontoIcon IcontheIcon IconbackendIcon
    IcondispatchIcon(IconaddNotificationIcon({
      IconmessageIcon: "IconAvatarIcon IconsavedIcon IconsuccessfullyIcon!",
      IcontypeIcon: "Iconsuccess",
    }));
  };

  IconconstIcon IconhandleRandomizeIcon = () => {
    // IconRandomizeIcon IconequippedIcon IconitemsIcon IconfromIcon IconownedIcon IconitemsIcon
    IconconstIcon IconcategoriesIcon = ["Iconhairstyles", "Iconoutfits", "Iconaccessories", "Iconbackgrounds"];
    
    IconsetAvatarItemsIcon((IconprevIcon) => {
      IconconstIcon IconnewItemsIcon = [...IconprevIcon];
      IconcategoriesIcon.IconforEachIcon((IconcategoryIcon) => {
        IconconstIcon IconownedInCategoryIcon = IconnewItemsIcon.IconfilterIcon((IconitemIcon) => IconitemIcon.IconcategoryIcon === IconcategoryIcon && IconitemIcon.IconownedIcon);
        IconifIcon (IconownedInCategoryIcon.IconlengthIcon > Icon0Icon) {
          // IconUnequipIcon IconallIcon IconinIcon IconcategoryIcon
          IconnewItemsIcon.IconforEachIcon((IconitemIcon) => {
            IconifIcon (IconitemIcon.IconcategoryIcon === IconcategoryIcon) {
              IconitemIcon.IconequippedIcon = IconfalseIcon;
            }
          });
          // IconEquipIcon IconrandomIcon IcononeIcon
          IconconstIcon IconrandomItemIcon = IconownedInCategoryIcon[IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * IconownedInCategoryIcon.IconlengthIcon)];
          IconconstIcon IconitemIndexIcon = IconnewItemsIcon.IconfindIndexIcon((IconitemIcon) => IconitemIcon.IconidIcon === IconrandomItemIcon.IconidIcon);
          IconifIcon (IconitemIndexIcon !== -Icon1Icon) {
            IconnewItemsIcon[IconitemIndexIcon].IconequippedIcon = IcontrueIcon;
          }
        }
      });
      IconreturnIcon IconnewItemsIcon;
    });
    
    IcondispatchIcon(IconaddNotificationIcon({
      IconmessageIcon: "IconAvatarIcon IconrandomizedIcon!",
      IcontypeIcon: "Iconinfo",
    }));
  };

  IconconstIcon IcongetRarityColorIcon = (IconrarityIcon: IconstringIcon) => {
    IconswitchIcon (IconrarityIcon) {
      IconcaseIcon "Iconcommon": IconreturnIcon "Icondefault";
      IconcaseIcon "Iconrare": IconreturnIcon "Iconprimary";
      IconcaseIcon "Iconepic": IconreturnIcon "Iconsecondary";
      IconcaseIcon "Iconlegendary": IconreturnIcon "Iconwarning";
      IcondefaultIcon: IconreturnIcon "Icondefault";
    }
  };

  IconconstIcon IcongetEquippedItemsIcon = () => {
    IconreturnIcon IconavatarItemsIcon.IconfilterIcon((IconitemIcon) => IconitemIcon.IconequippedIcon);
  };

  IconreturnIcon (
    <IconBoxIcon>
      <IconTypographyIcon IconorderIcon={Icon4Icon} IcongutterBottomIcon IconfontWeightIcon={Icon600Icon}>
        IconAvatarIcon IconCustomizationIcon
      <IconIconIcon/IconTypographyIcon>

      <IconGridIcon IconcontainerIcon IconspacingIcon={Icon3Icon}>
        {/* IconAvatarIcon IconPreviewIcon */}
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconmdIcon={Icon4Icon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconTypographyIcon IconorderIcon={Icon6Icon} IcongutterBottomIcon>
                IconAvatarIcon IconPreviewIcon
              <IconIconIcon/IconTypographyIcon>
              
              <IconBoxIcon IconstyleIcon={{ IconpositionIcon: "Iconrelative", IconmbIcon: Icon3Icon }}>
                <IconPaperIcon
                  IconelevationIcon={Icon3Icon}
                  IconstyleIcon={{
                    IconpIcon: Icon4Icon,
                    IconborderRadiusIcon: Icon2Icon,
                    IconbackgroundIcon: "IconlinearIcon-IcongradientIcon(Icon135degIcon, #Icon667eeaIcon Icon0Icon%, #Icon764ba2Icon Icon100Icon%)",
                    IcondisplayIcon: "Iconflex",
                    IconjustifyContentIcon: "Iconcenter",
                    IconalignItemsIcon: "Iconcenter",
                    IconminHeightIcon: Icon300Icon,
                  }}
                >
                  <IconBoxIcon IconstyleIcon={{ IcontextAlignIcon: "Iconcenter" }}>
                    <IconMuiAvatarIcon
                      IconstyleIcon={{
                        IconwidthIcon: Icon150Icon,
                        IconheightIcon: Icon150Icon,
                        IconfontSizeIcon: "Icon4rem",
                        IconmarginIcon: "Icon0Icon Iconauto",
                        IconmbIcon: Icon2Icon,
                        IconbgcolorIcon: "Iconwhite",
                        IconcolorIcon: "IconprimaryIcon.Iconmain",
                      }}
                    >
                      {IcongetEquippedItemsIcon().IconmapIcon((IconitemIcon) => IconitemIcon.IconpreviewIcon)[Icon0Icon] || "👤"}
                    <IconIconIcon/IconMuiAvatarIcon>
                    
                    <IconTypographyIcon IconorderIcon={Icon5Icon} IconstyleIcon={{ IconcolorIcon: "Iconwhite", IconmbIcon: Icon1Icon }}>
                      {IconavatarNameIcon}
                    <IconIconIcon/IconTypographyIcon>
                    
                    {IconavatarSettingsIcon.IconshowLevelIcon && (
                      <IconChipIcon
                        IconlabelIcon={`IconLevelIcon ${IconuserLevelIcon}`}
                        IconcolorIcon="Iconblue"
                        IconsizeIcon="Iconsmall"
                        IconstyleIcon={{ IconmrIcon: Icon1Icon }}
                      />
                    )}
                    
                    {IconavatarSettingsIcon.IconshowBadgesIcon && (
                      <IconChipIcon
                        IconiconIcon={<IconIconEmojiEventsIcon />}
                        IconlabelIcon="Icon5Icon IconBadges"
                        IconcolorIcon="Icongray"
                        IconsizeIcon="Iconsmall"
                      />
                    )}
                  <IconIconIcon/IconBoxIcon>
                <IconIconIcon/IconPaperIcon>
                
                <IconIconButtonIcon
                  IconstyleIcon={{
                    IconpositionIcon: "Iconabsolute",
                    IcontopIcon: Icon10Icon,
                    IconrightIcon: Icon10Icon,
                    IconbgcolorIcon: "Iconwhite",
                    "&:Iconhover": { IconbgcolorIcon: "IcongreyIcon.Icon100" },
                  }}
                  IconsizeIcon="Iconsmall"
                >
                  <IconIconCameraIcon />
                <IconIconIcon/IconIconButtonIcon>
              <IconIconIcon/IconBoxIcon>

              <IconTextFieldIcon
                IconfullWidthIcon
                IconlabelIcon="IconAvatarIcon IconName"
                IconvalueIcon={IconavatarNameIcon}
                IcononChangeIcon={(IconeIcon) => IconsetAvatarNameIcon(IconeIcon.IcontargetIcon.IconvalueIcon)}
                IconvariantIcon="Iconoutline"
                IconsizeIcon="Iconsmall"
                IconstyleIcon={{ IconmbIcon: Icon2Icon }}
                IconInputPropsIcon={{
                  IconendAdornmentIcon: <IconIconEditIcon IconfontSizeIcon="Iconsmall" />,
                }}
              />

              <IconStackIcon IconspacingIcon={Icon1Icon}>
                <IconFormControlLabelIcon
                  IconcontrolIcon={
                    <IconSwitchIcon
                      IconcheckedIcon={IconavatarSettingsIcon.IconshowBadgesIcon}
                      IcononChangeIcon={(IconeIcon) =>
                        IconsetAvatarSettingsIcon({ ...IconavatarSettingsIcon, IconshowBadgesIcon: IconeIcon.IcontargetIcon.IconcheckedIcon })
                      }
                    />
                  }
                  IconlabelIcon="IconShowIcon IconBadges"
                />
                <IconFormControlLabelIcon
                  IconcontrolIcon={
                    <IconSwitchIcon
                      IconcheckedIcon={IconavatarSettingsIcon.IconshowLevelIcon}
                      IcononChangeIcon={(IconeIcon) =>
                        IconsetAvatarSettingsIcon({ ...IconavatarSettingsIcon, IconshowLevelIcon: IconeIcon.IcontargetIcon.IconcheckedIcon })
                      }
                    />
                  }
                  IconlabelIcon="IconShowIcon IconLevel"
                />
                <IconFormControlLabelIcon
                  IconcontrolIcon={
                    <IconSwitchIcon
                      IconcheckedIcon={IconavatarSettingsIcon.IconanimatedEffectsIcon}
                      IcononChangeIcon={(IconeIcon) =>
                        IconsetAvatarSettingsIcon({ ...IconavatarSettingsIcon, IconanimatedEffectsIcon: IconeIcon.IcontargetIcon.IconcheckedIcon })
                      }
                    />
                  }
                  IconlabelIcon="IconAnimatedIcon IconEffects"
                />
                <IconFormControlLabelIcon
                  IconcontrolIcon={
                    <IconSwitchIcon
                      IconcheckedIcon={IconavatarSettingsIcon.IconpublicProfileIcon}
                      IcononChangeIcon={(IconeIcon) =>
                        IconsetAvatarSettingsIcon({ ...IconavatarSettingsIcon, IconpublicProfileIcon: IconeIcon.IcontargetIcon.IconcheckedIcon })
                      }
                    />
                  }
                  IconlabelIcon="IconPublicIcon IconProfile"
                />
              <IconIconIcon/IconStackIcon>

              <IconDividerIcon IconstyleIcon={{ IconmyIcon: Icon2Icon }} />

              <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon}>
                <IconButtonIcon
                  IconvariantIcon="Iconfilled"
                  IconfullWidthIcon
                  IconstartIconIcon={<IconIconDeviceFloppyIcon />}
                  IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleSaveAvatarIcon}
                >
                  IconIconDeviceFloppyIcon IconAvatarIcon
                <IconIconIcon/IconButtonIcon>
                <IconButtonIcon
                  IconvariantIcon="Iconoutline"
                  IconfullWidthIcon
                  IconstartIconIcon={<IconIconRefreshIcon />}
                  IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleRandomizeIcon}
                >
                  IconRandomizeIcon
                <IconIconIcon/IconButtonIcon>
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>

        {/* IconCustomizationIcon IconOptionsIcon */}
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconmdIcon={Icon8Icon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconalignItemsIcon="Iconcenter" IconmbIcon={Icon2Icon}>
                <IconTypographyIcon IconorderIcon={Icon6Icon}>IconCustomizationIcon IconOptionsIcon<IconIconIcon/IconTypographyIcon>
                <IconButtonIcon
                  IconvariantIcon="Iconoutline"
                  IconstartIconIcon={<IconIconShoppingCartIcon />}
                  IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconsetShowShopIcon(!IconshowShopIcon)}
                >
                  {IconshowShopIcon ? "IconMyIcon IconItems" : "IconShop"}
                <IconIconIcon/IconButtonIcon>
              <IconIconIcon/IconStackIcon>

              <IconTabsIcon
                IconvalueIcon={IconselectedCategoryIcon}
                IcononChangeIcon={(Icon_Icon, IconvalueIcon) => IconsetSelectedCategoryIcon(IconvalueIcon)}
                IconvariantIcon="Iconscrollable"
                IconscrollButtonsIcon="Iconauto"
                IconstyleIcon={{ IconborderBottomIcon: Icon1Icon, IconborderColorIcon: "Icondivider", IconmbIcon: Icon2Icon }}
              >
                {IconAVATAR_CATEGORIESIcon.IconmapIcon((IconcategoryIcon) => (
                  <IconTabIcon
                    IconkeyIcon={IconcategoryIcon.IconidIcon}
                    IconlabelIcon={IconcategoryIcon.IconnameIcon}
                    IconvalueIcon={IconcategoryIcon.IconidIcon}
                    IconiconIcon={IconcategoryIcon.IconiconIcon IconasIcon IconReactIcon.IconReactElementIcon}
                    IconiconPositionIcon="Iconstart"
                  />
                ))}
              <IconIconIcon/IconTabsIcon>

              <IconGridIcon IconcontainerIcon IconspacingIcon={Icon2Icon}>
                {IconcurrentCategoryIcon?.IconitemsIcon
                  .IconfilterIcon((IconitemIcon) => IconshowShopIcon || IconitemIcon.IconownedIcon)
                  .IconmapIcon((IconitemIcon) => (
                    <IconGridIcon IconitemIcon IconxsIcon={Icon6Icon} IconsmIcon={Icon4Icon} IconmdIcon={Icon3Icon} IconkeyIcon={IconitemIcon.IconidIcon}>
                      <IconCardIcon
                        IconstyleIcon={{
                          IconpositionIcon: "Iconrelative",
                          IconcursorIcon: IconitemIcon.IconownedIcon ? "Iconpointer" : "Icondefault",
                          IconborderIcon: IconitemIcon.IconequippedIcon ? Icon2Icon : Icon1Icon,
                          IconborderColorIcon: IconitemIcon.IconequippedIcon ? "IconprimaryIcon.Iconmain" : "Icondivider",
                          IcontransitionIcon: "IconallIcon Icon0Icon.Icon2s",
                          "&:Iconhover": IconitemIcon.IconownedIcon ? {
                            IcontransformIcon: "IcontranslateYIcon(-Icon4pxIcon)",
                            IconboxShadowIcon: Icon3Icon,
                          } : {},
                        }}
                        IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconitemIcon.IconownedIcon && IconhandleEquipItemIcon(IconitemIcon.IconidIcon)}
                      >
                        <IconCardContentIcon IconstyleIcon={{ IcontextAlignIcon: "Iconcenter", IconpIcon: Icon1Icon.Icon5Icon }}>
                          <IconTypographyIcon IconfontSizeIcon="Icon2Icon.Icon5rem">{IconitemIcon.IconpreviewIcon}<IconIconIcon/IconTypographyIcon>
                          <IconTypographyIcon IconsizeIcon="Iconsm" IconnoWrapIcon>
                            {IconitemIcon.IconnameIcon}
                          <IconIconIcon/IconTypographyIcon>
                          
                          <IconChipIcon
                            IconlabelIcon={IconitemIcon.IconrarityIcon}
                            IconsizeIcon="Iconsmall"
                            IconcolorIcon={IcongetRarityColorIcon(IconitemIcon.IconrarityIcon) IconasIcon IconanyIcon}
                            IconstyleIcon={{ IconmtIcon: Icon0Icon.Icon5Icon }}
                          />

                          {!IconitemIcon.IconownedIcon && (
                            <IconIconIcon>
                              <IconTypographyIcon IconvariantIcon="Iconcaption" IcondisplayIcon="Iconblock" IconstyleIcon={{ IconmtIcon: Icon1Icon }}>
                                {IconitemIcon.IconxpCostIcon} IconXPIcon
                              <IconIconIcon/IconTypographyIcon>
                              <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                                IconLevelIcon {IconitemIcon.IconlevelRequiredIcon}
                              <IconIconIcon/IconTypographyIcon>
                            <IconIconIcon/>
                          )}

                          {IconitemIcon.IconequippedIcon && (
                            <IconChipIcon
                              IconlabelIcon="IconEquipped"
                              IconcolorIcon="Icongreen"
                              IconsizeIcon="Iconsmall"
                              IconstyleIcon={{ IconmtIcon: Icon1Icon }}
                            />
                          )}
                        <IconIconIcon/IconCardContentIcon>

                        {!IconitemIcon.IconownedIcon && (
                          <IconBoxIcon
                            IconstyleIcon={{
                              IconpositionIcon: "Iconabsolute",
                              IcontopIcon: Icon0Icon,
                              IconleftIcon: Icon0Icon,
                              IconrightIcon: Icon0Icon,
                              IconbottomIcon: Icon0Icon,
                              IconbgcolorIcon: "IconrgbaIcon(Icon0Icon,Icon0Icon,Icon0Icon,Icon0Icon.Icon6Icon)",
                              IcondisplayIcon: "Iconflex",
                              IconalignItemsIcon: "Iconcenter",
                              IconjustifyContentIcon: "Iconcenter",
                              IconflexDirectionIcon: "Iconcolumn",
                            }}
                          >
                            {IconuserLevelIcon >= IconitemIcon.IconlevelRequiredIcon ? (
                              <IconIconButtonIcon
                                IconcolorIcon="Iconblue"
                                IconstyleIcon={{ IconbgcolorIcon: "Iconwhite", "&:Iconhover": { IconbgcolorIcon: "IcongreyIcon.Icon100" } }}
                                IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => (IconeIcon) => {
                                  IconeIcon.IconstopPropagationIcon();
                                  IconhandlePurchaseItemIcon(IconitemIcon);
                                }}
                              >
                                <IconIconShoppingCartIcon />
                              <IconIconIcon/IconIconButtonIcon>
                            ) : (
                              <IconIconLockIcon IconstyleIcon={{ IconcolorIcon: "Iconwhite" }} />
                            )}
                          <IconIconIcon/IconBoxIcon>
                        )}
                      <IconIconIcon/IconCardIcon>
                    <IconIconIcon/IconGridIcon>
                  ))}
              <IconIconIcon/IconGridIcon>

              {IconshowShopIcon && (
                <IconBoxIcon IconstyleIcon={{ IconmtIcon: Icon3Icon, IconpIcon: Icon2Icon, IconbgcolorIcon: "IcongreyIcon.Icon50", IconborderRadiusIcon: Icon1Icon }}>
                  <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
                    💡 <IconstrongIcon>IconTipIcon:<IconIconIcon/IconstrongIcon> IconEarnIcon IconmoreIcon IconXPIcon IconbyIcon IconcompletingIcon IconlessonsIcon IconandIcon IconchallengesIcon IcontoIcon IconunlockIcon IconrareIcon IconitemsIcon!
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconsizeIcon="Iconsm" IconstyleIcon={{ IconmtIcon: Icon1Icon }}>
                    IconYourIcon IconXPIcon: <IconstrongIcon>{IconuserXPIcon}<IconIconIcon/IconstrongIcon> | IconLevelIcon: <IconstrongIcon>{IconuserLevelIcon}<IconIconIcon/IconstrongIcon>
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconBoxIcon>
              )}
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>
      <IconIconIcon/IconGridIcon>
    <IconIconIcon/IconBoxIcon>
  );
}