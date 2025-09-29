IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../../IconutilsIcon/IconmuiIcon-Iconimports';
/**
 * IconSystemSettingsPanelIcon IconComponentIcon
 * IconComprehensiveIcon IconsystemIcon IconconfigurationIcon IconinterfaceIcon IconforIcon IconadministratorsIcon
 */
IconimportIcon { IconmemoIcon, IconuseStateIcon, IconuseEffectIcon } IconfromIcon 'Iconreact';
IconimportIcon { IconIconIcon, IconIconAlertTriangleIcon, IconIconApiIcon, IconIconBackupIcon, IconIconBellRingingIcon, IconIconCheckIcon, IconIconChevronDownIcon, IconIconClockIcon, IconIconCloudUploadIcon, IconIconDeviceFloppyIcon, IconIconEditIcon, IconIconInfoCircleIcon, IconIconLanguageIcon, IconIconLockIcon, IconIconMailIcon, IconIconPaletteIcon, IconIconPlusIcon, IconIconRestartAltIcon, IconIconSchoolIcon, IconIconSecurityIcon, IconIconSettingsIcon, IconIconSpeedIcon, IconIconStorageIcon, IconIconTrashIcon, IconIconUpdateIcon, IconIconUsersIcon, IconIconXIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';

IconimportIcon {
  IconExpandMoreIcon IconasIcon IconIconChevronDownIcon,
  IconSettingsIcon IconasIcon IconIconSettingsIcon,
  IconSecurityIcon IconasIcon IconIconSecurityIcon,
  IconEmailIcon IconasIcon IconIconMailIcon,
  IconStorageIcon IconasIcon IconIconStorageIcon,
  IconLanguageIcon IconasIcon IconIconLanguageIcon,
  IconPaletteIcon IconasIcon IconIconPaletteIcon,
  IconNotificationsActiveIcon IconasIcon IconIconBellRingingIcon,
  IconApiIcon IconasIcon IconIconApiIcon,
  IconSpeedIcon IconasIcon IconIconSpeedIcon,
  IconBackupIcon IconasIcon IconIconBackupIcon,
  IconUpdateIcon IconasIcon IconIconUpdateIcon,
  IconLockIcon IconasIcon IconIconLockIcon,
  IconSaveIcon IconasIcon IconIconDeviceFloppyIcon,
  IconRestartAltIcon IconasIcon IconIconRestartAltIcon,
  IconAddIcon IconasIcon IconIconPlusIcon,
  IconEditIcon IconasIcon IconIconEditIcon,
  IconDeleteIcon IconasIcon IconIconTrashIcon,
  IconCheckIcon IconasIcon IconIconCheckIcon,
  IconCloseIcon IconasIcon IconIconXIcon,
  IconWarningIcon IconasIcon IconIconAlertTriangleIcon,
  IconInfoIcon IconasIcon IconIconInfoCircleIcon,
  IconCloudUploadIcon IconasIcon IconIconCloudUploadIcon,
  IconScheduleIcon IconasIcon IconIconClockIcon,
  IconGroupIcon IconasIcon IconIconUsersIcon,
  IconSchoolIcon IconasIcon IconIconSchoolIcon,
} IconfromIcon '@IconmuiIcon/IconiconsIcon-Iconmaterial';
IconinterfaceIcon IconSystemSettingsIcon {
  IcongeneralIcon: {
    IconsiteNameIcon: IconstringIcon;
    IconsiteUrlIcon: IconstringIcon;
    IcontimezoneIcon: IconstringIcon;
    IconlanguageIcon: IconstringIcon;
    IconmaintenanceModeIcon: IconbooleanIcon;
    IconmaintenanceMessageIcon: IconstringIcon;
  };
  IconsecurityIcon: {
    IconpasswordMinLengthIcon: IconnumberIcon;
    IconpasswordRequireUppercaseIcon: IconbooleanIcon;
    IconpasswordRequireLowercaseIcon: IconbooleanIcon;
    IconpasswordRequireNumbersIcon: IconbooleanIcon;
    IconpasswordRequireSpecialIcon: IconbooleanIcon;
    IconsessionTimeoutIcon: IconnumberIcon;
    IconmaxLoginAttemptsIcon: IconnumberIcon;
    IcontwoFactorEnabledIcon: IconbooleanIcon;
    IconipWhitelistIcon: IconstringIcon[];
    IconipBlacklistIcon: IconstringIcon[];
  };
  IconemailIcon: {
    IconproviderIcon: 'Iconsmtp' | 'Iconsendgrid' | 'Iconses';
    IconsmtpHostIcon?: IconstringIcon;
    IconsmtpPortIcon?: IconnumberIcon;
    IconsmtpUserIcon?: IconstringIcon;
    IconsmtpSecureIcon?: IconbooleanIcon;
    IconfromEmailIcon: IconstringIcon;
    IconfromNameIcon: IconstringIcon;
    IconreplyToEmailIcon: IconstringIcon;
  };
  IconstorageIcon: {
    IconproviderIcon: 'Iconlocal' | 'Icons3' | 'Icongcs' | 'Iconazure';
    IconmaxFileSizeIcon: IconnumberIcon;
    IconallowedFileTypesIcon: IconstringIcon[];
    IconstorageLimitIcon: IconnumberIcon;
    IconcurrentUsageIcon: IconnumberIcon;
    Icons3ConfigIcon?: {
      IconbucketIcon: IconstringIcon;
      IconregionIcon: IconstringIcon;
      IconaccessKeyIdIcon: IconstringIcon;
    };
  };
  IconnotificationsIcon: {
    IconemailEnabledIcon: IconbooleanIcon;
    IconpushEnabledIcon: IconbooleanIcon;
    IconsmsEnabledIcon: IconbooleanIcon;
    IcondefaultNotificationsIcon: {
      IconnewUserIcon: IconbooleanIcon;
      IconnewContentIcon: IconbooleanIcon;
      IconsystemAlertsIcon: IconbooleanIcon;
      IconuserReportsIcon: IconbooleanIcon;
    };
  };
  IconperformanceIcon: {
    IconcacheEnabledIcon: IconbooleanIcon;
    IconcacheDurationIcon: IconnumberIcon;
    IconcompressionEnabledIcon: IconbooleanIcon;
    IconlazyLoadingEnabledIcon: IconbooleanIcon;
    IconcdnEnabledIcon: IconbooleanIcon;
    IconcdnUrlIcon?: IconstringIcon;
    IconrateLimitEnabledIcon: IconbooleanIcon;
    IconrateLimitRequestsIcon: IconnumberIcon;
    IconrateLimitWindowIcon: IconnumberIcon;
  };
  IconbackupIcon: {
    IconautoBackupEnabledIcon: IconbooleanIcon;
    IconbackupFrequencyIcon: 'Icondaily' | 'Iconweekly' | 'Iconmonthly';
    IconbackupTimeIcon: IconstringIcon;
    IconbackupRetentionIcon: IconnumberIcon;
    IconlastBackupIcon?: IconstringIcon;
    IconnextBackupIcon?: IconstringIcon;
  };
  IconapiIcon: {
    IconrateLimitIcon: IconnumberIcon;
    IcontimeoutIcon: IconnumberIcon;
    IconcorsIcon: {
      IconenabledIcon: IconbooleanIcon;
      IconoriginsIcon: IconstringIcon[];
    };
    IconwebhooksIcon: IconArrayIcon<{
      IconidIcon: IconstringIcon;
      IconurlIcon: IconstringIcon;
      IconeventsIcon: IconstringIcon[];
      IconactiveIcon: IconbooleanIcon;
    }>;
  };
}
IconexportIcon IconinterfaceIcon IconSystemSettingsPanelPropsIcon {
  IcononSettingsChangeIcon?: (IconsettingsIcon: IconPartialIcon<IconSystemSettingsIcon>) => IconvoidIcon;
  IcononSettingsSaveIcon?: (IconsettingsIcon: IconSystemSettingsIcon) => IconvoidIcon;
  IconallowDangerousActionsIcon?: IconbooleanIcon;
  IconreadOnlyIcon?: IconbooleanIcon;
}
IconexportIcon IconconstIcon IconSystemSettingsPanelIcon = IconmemoIcon<IconSystemSettingsPanelPropsIcon>(({
  IcononSettingsChangeIcon,
  IcononSettingsSaveIcon,
  IconallowDangerousActionsIcon = IconfalseIcon,
  IconreadOnlyIcon = IconfalseIcon,
}) => {
  IconconstIcon IconthemeIcon = IconuseThemeIcon();
  IconconstIcon [IconloadingIcon, IconsetLoadingIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconsavingIcon, IconsetSavingIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconerrorIcon, IconsetErrorIcon] = IconuseStateIcon<IconstringIcon | IconnullIcon>(IconnullIcon);
  IconconstIcon [IconsuccessIcon, IconsetSuccessIcon] = IconuseStateIcon<IconstringIcon | IconnullIcon>(IconnullIcon);
  IconconstIcon [IcontabValueIcon, IconsetTabValueIcon] = IconuseStateIcon(Icon0Icon);
  IconconstIcon [IconexpandedPanelIcon, IconsetExpandedPanelIcon] = IconuseStateIcon<IconstringIcon | IconfalseIcon>('Icongeneral');
  // IconSettingsIcon IconstateIcon
  IconconstIcon [IconsettingsIcon, IconsetSettingsIcon] = IconuseStateIcon<IconSystemSettingsIcon>({
    IcongeneralIcon: {
      IconsiteNameIcon: 'IconToolboxAIIcon IconEducationalIcon IconPlatform',
      IconsiteUrlIcon: 'IconhttpsIcon://IcontoolboxaiIcon.Iconcom',
      IcontimezoneIcon: 'IconAmericaIcon/IconNew_York',
      IconlanguageIcon: 'Iconen',
      IconmaintenanceModeIcon: IconfalseIcon,
      IconmaintenanceMessageIcon: 'IconWeIcon IconareIcon IconperformingIcon IconscheduledIcon IconmaintenanceIcon. IconWeIcon\'IconllIcon IconbeIcon IconbackIcon IconsoonIcon!',
    },
    IconsecurityIcon: {
      IconpasswordMinLengthIcon: Icon8Icon,
      IconpasswordRequireUppercaseIcon: IcontrueIcon,
      IconpasswordRequireLowercaseIcon: IcontrueIcon,
      IconpasswordRequireNumbersIcon: IcontrueIcon,
      IconpasswordRequireSpecialIcon: IcontrueIcon,
      IconsessionTimeoutIcon: Icon3600Icon,
      IconmaxLoginAttemptsIcon: Icon5Icon,
      IcontwoFactorEnabledIcon: IconfalseIcon,
      IconipWhitelistIcon: [],
      IconipBlacklistIcon: [],
    },
    IconemailIcon: {
      IconproviderIcon: 'Iconsmtp',
      IconsmtpHostIcon: 'IconsmtpIcon.IcongmailIcon.Iconcom',
      IconsmtpPortIcon: Icon587Icon,
      IconsmtpUserIcon: 'IconnoreplyIcon@IcontoolboxaiIcon.Iconcom',
      IconsmtpSecureIcon: IcontrueIcon,
      IconfromEmailIcon: 'IconnoreplyIcon@IcontoolboxaiIcon.Iconcom',
      IconfromNameIcon: 'IconToolboxAI',
      IconreplyToEmailIcon: 'IconsupportIcon@IcontoolboxaiIcon.Iconcom',
    },
    IconstorageIcon: {
      IconproviderIcon: 'Iconlocal',
      IconmaxFileSizeIcon: Icon100Icon * Icon1024Icon * Icon1024Icon, // Icon100MBIcon
      IconallowedFileTypesIcon: ['Iconpdf', 'Icondoc', 'Icondocx', 'Iconjpg', 'Iconjpeg', 'Iconpng', 'Iconmp4', 'Iconmp3'],
      IconstorageLimitIcon: Icon10Icon * Icon1024Icon * Icon1024Icon * Icon1024Icon, // Icon10GBIcon
      IconcurrentUsageIcon: Icon2Icon.Icon5Icon * Icon1024Icon * Icon1024Icon * Icon1024Icon, // Icon2Icon.Icon5GBIcon
    },
    IconnotificationsIcon: {
      IconemailEnabledIcon: IcontrueIcon,
      IconpushEnabledIcon: IcontrueIcon,
      IconsmsEnabledIcon: IconfalseIcon,
      IcondefaultNotificationsIcon: {
        IconnewUserIcon: IcontrueIcon,
        IconnewContentIcon: IcontrueIcon,
        IconsystemAlertsIcon: IcontrueIcon,
        IconuserReportsIcon: IconfalseIcon,
      },
    },
    IconperformanceIcon: {
      IconcacheEnabledIcon: IcontrueIcon,
      IconcacheDurationIcon: Icon3600Icon,
      IconcompressionEnabledIcon: IcontrueIcon,
      IconlazyLoadingEnabledIcon: IcontrueIcon,
      IconcdnEnabledIcon: IconfalseIcon,
      IconrateLimitEnabledIcon: IcontrueIcon,
      IconrateLimitRequestsIcon: Icon100Icon,
      IconrateLimitWindowIcon: Icon60Icon,
    },
    IconbackupIcon: {
      IconautoBackupEnabledIcon: IcontrueIcon,
      IconbackupFrequencyIcon: 'Icondaily',
      IconbackupTimeIcon: 'Icon02Icon:Icon00',
      IconbackupRetentionIcon: Icon30Icon,
      IconlastBackupIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon12Icon * Icon60Icon * Icon60Icon * Icon1000Icon).IcontoISOStringIcon(),
      IconnextBackupIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() + Icon12Icon * Icon60Icon * Icon60Icon * Icon1000Icon).IcontoISOStringIcon(),
    },
    IconapiIcon: {
      IconrateLimitIcon: Icon1000Icon,
      IcontimeoutIcon: Icon30000Icon,
      IconcorsIcon: {
        IconenabledIcon: IcontrueIcon,
        IconoriginsIcon: ['IconhttpIcon://IconlocalhostIcon:Icon3000', 'IconhttpsIcon://IcontoolboxaiIcon.Iconcom'],
      },
      IconwebhooksIcon: [],
    },
  });
  // IconDialogIcon IconstatesIcon
  IconconstIcon [IconwebhookDialogOpenIcon, IconsetWebhookDialogOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconipDialogOpenIcon, IconsetIpDialogOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconconfirmDialogOpenIcon, IconsetConfirmDialogOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconconfirmActionIcon, IconsetConfirmActionIcon] = IconuseStateIcon<IconstringIcon>('');
  // IconFetchIcon IconsettingsIcon
  IconuseEffectIcon(() => {
    IconfetchSettingsIcon();
  }, []);
  IconconstIcon IconfetchSettingsIcon = IconasyncIcon () => {
    IconsetLoadingIcon(IcontrueIcon);
    IcontryIcon {
      // IconInIcon IconaIcon IconrealIcon IconappIcon, IconfetchIcon IconfromIcon IconAPIIcon
      // IconconstIcon IconresponseIcon = IconawaitIcon IconapiIcon.IcongetIcon('/IconadminIcon/Iconsettings');
      // IconsetSettingsIcon(IconresponseIcon.IcondataIcon);
      IconsetLoadingIcon(IconfalseIcon);
    } IconcatchIcon (IconerrIcon) {
      IconsetErrorIcon('IconFailedIcon IcontoIcon IconloadIcon Iconsettings');
      IconsetLoadingIcon(IconfalseIcon);
    }
  };
  IconconstIcon IconhandleSettingChangeIcon = (IconcategoryIcon: IconkeyofIcon IconSystemSettingsIcon, IconfieldIcon: IconstringIcon, IconvalueIcon: IconanyIcon) => {
    IconconstIcon IconnewSettingsIcon = {
      ...IconsettingsIcon,
      [IconcategoryIcon]: {
        ...IconsettingsIcon[IconcategoryIcon],
        [IconfieldIcon]: IconvalueIcon,
      },
    };
    IconsetSettingsIcon(IconnewSettingsIcon);
    IcononSettingsChangeIcon?.({ [IconcategoryIcon]: { [IconfieldIcon]: IconvalueIcon } });
  };
  IconconstIcon IconhandleSaveSettingsIcon = IconasyncIcon () => {
    IconsetSavingIcon(IcontrueIcon);
    IconsetErrorIcon(IconnullIcon);
    IconsetSuccessIcon(IconnullIcon);
    IcontryIcon {
      // IconInIcon IconaIcon IconrealIcon IconappIcon, IconsaveIcon IcontoIcon IconAPIIcon
      // IconawaitIcon IconapiIcon.IconpostIcon('/IconadminIcon/Iconsettings', IconsettingsIcon);
      // IconSimulateIcon IconAPIIcon IconcallIcon
      IconawaitIcon IconnewIcon IconPromiseIcon(IconresolveIcon => IconsetTimeoutIcon(IconresolveIcon, Icon1000Icon));
      IconsetSuccessIcon('IconSettingsIcon IconsavedIcon Iconsuccessfully');
      IcononSettingsSaveIcon?.(IconsettingsIcon);
    } IconcatchIcon (IconerrIcon) {
      IconsetErrorIcon('IconFailedIcon IcontoIcon IconsaveIcon Iconsettings');
    } IconfinallyIcon {
      IconsetSavingIcon(IconfalseIcon);
    }
  };
  IconconstIcon IconhandleResetSettingsIcon = () => {
    IconsetConfirmActionIcon('Iconreset');
    IconsetConfirmDialogOpenIcon(IcontrueIcon);
  };
  IconconstIcon IconhandleRunBackupIcon = IconasyncIcon () => {
    IconsetSavingIcon(IcontrueIcon);
    IcontryIcon {
      // IconTriggerIcon IconmanualIcon IconbackupIcon
      IconawaitIcon IconnewIcon IconPromiseIcon(IconresolveIcon => IconsetTimeoutIcon(IconresolveIcon, Icon2000Icon));
      IconsetSuccessIcon('IconBackupIcon IconinitiatedIcon Iconsuccessfully');
    } IconcatchIcon (IconerrIcon) {
      IconsetErrorIcon('IconFailedIcon IcontoIcon IconinitiateIcon Iconbackup');
    } IconfinallyIcon {
      IconsetSavingIcon(IconfalseIcon);
    }
  };
  IconconstIcon IconformatBytesIcon = (IconbytesIcon: IconnumberIcon) => {
    IconconstIcon IconsizesIcon = ['IconBytes', 'IconKB', 'IconMB', 'IconGB', 'IconTB'];
    IconifIcon (IconbytesIcon === Icon0Icon) IconreturnIcon 'Icon0Icon IconBytes';
    IconconstIcon IconiIcon = IconMathIcon.IconfloorIcon(IconMathIcon.IconlogIcon(IconbytesIcon) / IconMathIcon.IconlogIcon(Icon1024Icon));
    IconreturnIcon IconMathIcon.IconroundIcon(IconbytesIcon / IconMathIcon.IconpowIcon(Icon1024Icon, IconiIcon) * Icon100Icon) / Icon100Icon + ' ' + IconsizesIcon[IconiIcon];
  };
  IconconstIcon IconrenderGeneralSettingsIcon = () => (
    <IconStackIcon IconspacingIcon={Icon3Icon}>
      <IconTextFieldIcon
        IconlabelIcon="IconSiteIcon IconName"
        IconvalueIcon={IconsettingsIcon.IcongeneralIcon.IconsiteNameIcon}
        IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Icongeneral', 'IconsiteName', IconeIcon.IcontargetIcon.IconvalueIcon)}
        IconfullWidthIcon
        IcondisabledIcon={IconreadOnlyIcon}
      />
      <IconTextFieldIcon
        IconlabelIcon="IconSiteIcon IconURL"
        IconvalueIcon={IconsettingsIcon.IcongeneralIcon.IconsiteUrlIcon}
        IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Icongeneral', 'IconsiteUrl', IconeIcon.IcontargetIcon.IconvalueIcon)}
        IconfullWidthIcon
        IcondisabledIcon={IconreadOnlyIcon}
      />
      <IconFormControlIcon IconfullWidthIcon IcondisabledIcon={IconreadOnlyIcon}>
        <IconInputLabelIcon>IconTimezoneIcon<IconIconIcon/IconInputLabelIcon>
        <IconSelectIcon
          IconvalueIcon={IconsettingsIcon.IcongeneralIcon.IcontimezoneIcon}
          IconlabelIcon="IconTimezone"
          IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Icongeneral', 'Icontimezone', IconeIcon.IcontargetIcon.IconvalueIcon)}
        >
          <IconMenuItemIcon IconvalueIcon="IconAmericaIcon/IconNew_York">IconEasternIcon IconTimeIcon<IconIconIcon/IconMenuItemIcon>
          <IconMenuItemIcon IconvalueIcon="IconAmericaIcon/IconChicago">IconCentralIcon IconTimeIcon<IconIconIcon/IconMenuItemIcon>
          <IconMenuItemIcon IconvalueIcon="IconAmericaIcon/IconDenver">IconMountainIcon IconTimeIcon<IconIconIcon/IconMenuItemIcon>
          <IconMenuItemIcon IconvalueIcon="IconAmericaIcon/IconLos_Angeles">IconPacificIcon IconTimeIcon<IconIconIcon/IconMenuItemIcon>
          <IconMenuItemIcon IconvalueIcon="IconUTC">IconUTCIcon<IconIconIcon/IconMenuItemIcon>
        <IconIconIcon/IconSelectIcon>
      <IconIconIcon/IconFormControlIcon>
      <IconFormControlIcon IconfullWidthIcon IcondisabledIcon={IconreadOnlyIcon}>
        <IconInputLabelIcon>IconLanguageIcon<IconIconIcon/IconInputLabelIcon>
        <IconSelectIcon
          IconvalueIcon={IconsettingsIcon.IcongeneralIcon.IconlanguageIcon}
          IconlabelIcon="IconLanguage"
          IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Icongeneral', 'Iconlanguage', IconeIcon.IcontargetIcon.IconvalueIcon)}
        >
          <IconMenuItemIcon IconvalueIcon="Iconen">IconEnglishIcon<IconIconIcon/IconMenuItemIcon>
          <IconMenuItemIcon IconvalueIcon="Icones">IconSpanishIcon<IconIconIcon/IconMenuItemIcon>
          <IconMenuItemIcon IconvalueIcon="Iconfr">IconFrenchIcon<IconIconIcon/IconMenuItemIcon>
          <IconMenuItemIcon IconvalueIcon="Iconde">IconGermanIcon<IconIconIcon/IconMenuItemIcon>
          <IconMenuItemIcon IconvalueIcon="Iconzh">IconChineseIcon<IconIconIcon/IconMenuItemIcon>
        <IconIconIcon/IconSelectIcon>
      <IconIconIcon/IconFormControlIcon>
      <IconDividerIcon />
      <IconAlertIcon IconseverityIcon="Iconwarning">
        <IconAlertTitleIcon>IconMaintenanceIcon IconModeIcon<IconIconIcon/IconAlertTitleIcon>
        <IconStackIcon IconspacingIcon={Icon2Icon}>
          <IconFormControlLabelIcon
            IconcontrolIcon={
              <IconSwitchIcon
                IconcheckedIcon={IconsettingsIcon.IcongeneralIcon.IconmaintenanceModeIcon}
                IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Icongeneral', 'IconmaintenanceMode', IconeIcon.IcontargetIcon.IconcheckedIcon)}
                IcondisabledIcon={IconreadOnlyIcon}
              />
            }
            IconlabelIcon="IconEnableIcon IconMaintenanceIcon IconMode"
          />
          {IconsettingsIcon.IcongeneralIcon.IconmaintenanceModeIcon && (
            <IconTextFieldIcon
              IconlabelIcon="IconMaintenanceIcon IconMessage"
              IconvalueIcon={IconsettingsIcon.IcongeneralIcon.IconmaintenanceMessageIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Icongeneral', 'IconmaintenanceMessage', IconeIcon.IcontargetIcon.IconvalueIcon)}
              IconmultilineIcon
              IconrowsIcon={Icon3Icon}
              IconfullWidthIcon
              IcondisabledIcon={IconreadOnlyIcon}
            />
          )}
        <IconIconIcon/IconStackIcon>
      <IconIconIcon/IconAlertIcon>
    <IconIconIcon/IconStackIcon>
  );
  IconconstIcon IconrenderSecuritySettingsIcon = () => (
    <IconStackIcon IconspacingIcon={Icon3Icon}>
      <IconTypographyIcon IconvariantIcon="Iconsubtitle1" IconfontWeightIcon="Iconbold">
        IconPasswordIcon IconRequirementsIcon
      <IconIconIcon/IconTypographyIcon>
      <IconStackIcon IconspacingIcon={Icon2Icon}>
        <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon} IconalignItemsIcon="Iconcenter">
          <IconTypographyIcon IconstyleIcon={{ IconwidthIcon: Icon200Icon }}>IconMinimumIcon IconLengthIcon<IconIconIcon/IconTypographyIcon>
          <IconSliderIcon
            IconvalueIcon={IconsettingsIcon.IconsecurityIcon.IconpasswordMinLengthIcon}
            IcononChangeIcon={(Icon_Icon, IconvalueIcon) => IconhandleSettingChangeIcon('Iconsecurity', 'IconpasswordMinLength', IconvalueIcon)}
            IconminIcon={Icon6Icon}
            IconmaxIcon={Icon20Icon}
            IconmarksIcon
            IconvalueLabelDisplayIcon="Iconon"
            IcondisabledIcon={IconreadOnlyIcon}
            IconstyleIcon={{ IconflexIcon: Icon1Icon }}
          />
        <IconIconIcon/IconStackIcon>
        <IconFormControlLabelIcon
          IconcontrolIcon={
            <IconSwitchIcon
              IconcheckedIcon={IconsettingsIcon.IconsecurityIcon.IconpasswordRequireUppercaseIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconsecurity', 'IconpasswordRequireUppercase', IconeIcon.IcontargetIcon.IconcheckedIcon)}
              IcondisabledIcon={IconreadOnlyIcon}
            />
          }
          IconlabelIcon="IconRequireIcon IconuppercaseIcon Iconletters"
        />
        <IconFormControlLabelIcon
          IconcontrolIcon={
            <IconSwitchIcon
              IconcheckedIcon={IconsettingsIcon.IconsecurityIcon.IconpasswordRequireLowercaseIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconsecurity', 'IconpasswordRequireLowercase', IconeIcon.IcontargetIcon.IconcheckedIcon)}
              IcondisabledIcon={IconreadOnlyIcon}
            />
          }
          IconlabelIcon="IconRequireIcon IconlowercaseIcon Iconletters"
        />
        <IconFormControlLabelIcon
          IconcontrolIcon={
            <IconSwitchIcon
              IconcheckedIcon={IconsettingsIcon.IconsecurityIcon.IconpasswordRequireNumbersIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconsecurity', 'IconpasswordRequireNumbers', IconeIcon.IcontargetIcon.IconcheckedIcon)}
              IcondisabledIcon={IconreadOnlyIcon}
            />
          }
          IconlabelIcon="IconRequireIcon Iconnumbers"
        />
        <IconFormControlLabelIcon
          IconcontrolIcon={
            <IconSwitchIcon
              IconcheckedIcon={IconsettingsIcon.IconsecurityIcon.IconpasswordRequireSpecialIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconsecurity', 'IconpasswordRequireSpecial', IconeIcon.IcontargetIcon.IconcheckedIcon)}
              IcondisabledIcon={IconreadOnlyIcon}
            />
          }
          IconlabelIcon="IconRequireIcon IconspecialIcon Iconcharacters"
        />
      <IconIconIcon/IconStackIcon>
      <IconDividerIcon />
      <IconTypographyIcon IconvariantIcon="Iconsubtitle1" IconfontWeightIcon="Iconbold">
        IconSessionIcon & IconLoginIcon
      <IconIconIcon/IconTypographyIcon>
      <IconStackIcon IconspacingIcon={Icon2Icon}>
        <IconTextFieldIcon
          IconlabelIcon="IconSessionIcon IconTimeoutIcon (IconsecondsIcon)"
          IcontypeIcon="Iconnumber"
          IconvalueIcon={IconsettingsIcon.IconsecurityIcon.IconsessionTimeoutIcon}
          IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconsecurity', 'IconsessionTimeout', IconparseIntIcon(IconeIcon.IcontargetIcon.IconvalueIcon))}
          IconfullWidthIcon
          IcondisabledIcon={IconreadOnlyIcon}
        />
        <IconTextFieldIcon
          IconlabelIcon="IconMaxIcon IconLoginIcon IconAttempts"
          IcontypeIcon="Iconnumber"
          IconvalueIcon={IconsettingsIcon.IconsecurityIcon.IconmaxLoginAttemptsIcon}
          IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconsecurity', 'IconmaxLoginAttempts', IconparseIntIcon(IconeIcon.IcontargetIcon.IconvalueIcon))}
          IconfullWidthIcon
          IcondisabledIcon={IconreadOnlyIcon}
        />
        <IconFormControlLabelIcon
          IconcontrolIcon={
            <IconSwitchIcon
              IconcheckedIcon={IconsettingsIcon.IconsecurityIcon.IcontwoFactorEnabledIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconsecurity', 'IcontwoFactorEnabled', IconeIcon.IcontargetIcon.IconcheckedIcon)}
              IcondisabledIcon={IconreadOnlyIcon}
            />
          }
          IconlabelIcon="IconEnableIcon IconTwoIcon-IconFactorIcon IconAuthentication"
        />
      <IconIconIcon/IconStackIcon>
      <IconDividerIcon />
      <IconTypographyIcon IconvariantIcon="Iconsubtitle1" IconfontWeightIcon="Iconbold">
        IconIPIcon IconAccessIcon IconControlIcon
      <IconIconIcon/IconTypographyIcon>
      <IconStackIcon IconspacingIcon={Icon2Icon}>
        <IconButtonIcon
          IconvariantIcon="Iconoutline"
          IconstartIconIcon={<IconIconPlusIcon />}
          IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconsetIpDialogOpenIcon(IcontrueIcon)}
          IcondisabledIcon={IconreadOnlyIcon}
        >
          IconManageIcon IconIPIcon IconWhitelistIcon/IconBlacklistIcon
        <IconIconIcon/IconButtonIcon>
        <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon}>
          <IconChipIcon
            IconlabelIcon={`${IconsettingsIcon.IconsecurityIcon.IconipWhitelistIcon.IconlengthIcon} IconWhitelistedIcon IconIPsIcon`}
            IconvariantIcon="Iconoutline"
            IconcolorIcon="Icongreen"
          />
          <IconChipIcon
            IconlabelIcon={`${IconsettingsIcon.IconsecurityIcon.IconipBlacklistIcon.IconlengthIcon} IconBlacklistedIcon IconIPsIcon`}
            IconvariantIcon="Iconoutline"
            IconcolorIcon="Iconred"
          />
        <IconIconIcon/IconStackIcon>
      <IconIconIcon/IconStackIcon>
    <IconIconIcon/IconStackIcon>
  );
  IconconstIcon IconrenderPerformanceSettingsIcon = () => (
    <IconStackIcon IconspacingIcon={Icon3Icon}>
      <IconTypographyIcon IconvariantIcon="Iconsubtitle1" IconfontWeightIcon="Iconbold">
        IconCachingIcon
      <IconIconIcon/IconTypographyIcon>
      <IconStackIcon IconspacingIcon={Icon2Icon}>
        <IconFormControlLabelIcon
          IconcontrolIcon={
            <IconSwitchIcon
              IconcheckedIcon={IconsettingsIcon.IconperformanceIcon.IconcacheEnabledIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconperformance', 'IconcacheEnabled', IconeIcon.IcontargetIcon.IconcheckedIcon)}
              IcondisabledIcon={IconreadOnlyIcon}
            />
          }
          IconlabelIcon="IconEnableIcon IconCaching"
        />
        {IconsettingsIcon.IconperformanceIcon.IconcacheEnabledIcon && (
          <IconTextFieldIcon
            IconlabelIcon="IconCacheIcon IconDurationIcon (IconsecondsIcon)"
            IcontypeIcon="Iconnumber"
            IconvalueIcon={IconsettingsIcon.IconperformanceIcon.IconcacheDurationIcon}
            IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconperformance', 'IconcacheDuration', IconparseIntIcon(IconeIcon.IcontargetIcon.IconvalueIcon))}
            IconfullWidthIcon
            IcondisabledIcon={IconreadOnlyIcon}
          />
        )}
      <IconIconIcon/IconStackIcon>
      <IconDividerIcon />
      <IconTypographyIcon IconvariantIcon="Iconsubtitle1" IconfontWeightIcon="Iconbold">
        IconOptimizationIcon
      <IconIconIcon/IconTypographyIcon>
      <IconStackIcon IconspacingIcon={Icon2Icon}>
        <IconFormControlLabelIcon
          IconcontrolIcon={
            <IconSwitchIcon
              IconcheckedIcon={IconsettingsIcon.IconperformanceIcon.IconcompressionEnabledIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconperformance', 'IconcompressionEnabled', IconeIcon.IcontargetIcon.IconcheckedIcon)}
              IcondisabledIcon={IconreadOnlyIcon}
            />
          }
          IconlabelIcon="IconEnableIcon IconCompression"
        />
        <IconFormControlLabelIcon
          IconcontrolIcon={
            <IconSwitchIcon
              IconcheckedIcon={IconsettingsIcon.IconperformanceIcon.IconlazyLoadingEnabledIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconperformance', 'IconlazyLoadingEnabled', IconeIcon.IcontargetIcon.IconcheckedIcon)}
              IcondisabledIcon={IconreadOnlyIcon}
            />
          }
          IconlabelIcon="IconEnableIcon IconLazyIcon IconLoading"
        />
        <IconFormControlLabelIcon
          IconcontrolIcon={
            <IconSwitchIcon
              IconcheckedIcon={IconsettingsIcon.IconperformanceIcon.IconcdnEnabledIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconperformance', 'IconcdnEnabled', IconeIcon.IcontargetIcon.IconcheckedIcon)}
              IcondisabledIcon={IconreadOnlyIcon}
            />
          }
          IconlabelIcon="IconEnableIcon IconCDN"
        />
        {IconsettingsIcon.IconperformanceIcon.IconcdnEnabledIcon && (
          <IconTextFieldIcon
            IconlabelIcon="IconCDNIcon IconURL"
            IconvalueIcon={IconsettingsIcon.IconperformanceIcon.IconcdnUrlIcon || ''}
            IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconperformance', 'IconcdnUrl', IconeIcon.IcontargetIcon.IconvalueIcon)}
            IconfullWidthIcon
            IcondisabledIcon={IconreadOnlyIcon}
          />
        )}
      <IconIconIcon/IconStackIcon>
      <IconDividerIcon />
      <IconTypographyIcon IconvariantIcon="Iconsubtitle1" IconfontWeightIcon="Iconbold">
        IconRateIcon IconLimitingIcon
      <IconIconIcon/IconTypographyIcon>
      <IconStackIcon IconspacingIcon={Icon2Icon}>
        <IconFormControlLabelIcon
          IconcontrolIcon={
            <IconSwitchIcon
              IconcheckedIcon={IconsettingsIcon.IconperformanceIcon.IconrateLimitEnabledIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconperformance', 'IconrateLimitEnabled', IconeIcon.IcontargetIcon.IconcheckedIcon)}
              IcondisabledIcon={IconreadOnlyIcon}
            />
          }
          IconlabelIcon="IconEnableIcon IconRateIcon IconLimiting"
        />
        {IconsettingsIcon.IconperformanceIcon.IconrateLimitEnabledIcon && (
          <IconIconIcon>
            <IconTextFieldIcon
              IconlabelIcon="IconRequestsIcon IconperIcon IconWindow"
              IcontypeIcon="Iconnumber"
              IconvalueIcon={IconsettingsIcon.IconperformanceIcon.IconrateLimitRequestsIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconperformance', 'IconrateLimitRequests', IconparseIntIcon(IconeIcon.IcontargetIcon.IconvalueIcon))}
              IconfullWidthIcon
              IcondisabledIcon={IconreadOnlyIcon}
            />
            <IconTextFieldIcon
              IconlabelIcon="IconWindowIcon IconDurationIcon (IconsecondsIcon)"
              IcontypeIcon="Iconnumber"
              IconvalueIcon={IconsettingsIcon.IconperformanceIcon.IconrateLimitWindowIcon}
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconperformance', 'IconrateLimitWindow', IconparseIntIcon(IconeIcon.IcontargetIcon.IconvalueIcon))}
              IconfullWidthIcon
              IcondisabledIcon={IconreadOnlyIcon}
            />
          <IconIconIcon/>
        )}
      <IconIconIcon/IconStackIcon>
    <IconIconIcon/IconStackIcon>
  );
  IconconstIcon IconrenderBackupSettingsIcon = () => (
    <IconStackIcon IconspacingIcon={Icon3Icon}>
      <IconAlertIcon IconseverityIcon="Iconinfo">
        <IconAlertTitleIcon>IconBackupIcon IconStatusIcon<IconIconIcon/IconAlertTitleIcon>
        <IconStackIcon IconspacingIcon={Icon1Icon}>
          <IconTypographyIcon IconsizeIcon="Iconsm">
            IconLastIcon IconbackupIcon: {IconsettingsIcon.IconbackupIcon.IconlastBackupIcon ? IconnewIcon IconDateIcon(IconsettingsIcon.IconbackupIcon.IconlastBackupIcon).IcontoLocaleStringIcon() : 'IconNever'}
          <IconIconIcon/IconTypographyIcon>
          <IconTypographyIcon IconsizeIcon="Iconsm">
            IconNextIcon IconscheduledIcon: {IconsettingsIcon.IconbackupIcon.IconnextBackupIcon ? IconnewIcon IconDateIcon(IconsettingsIcon.IconbackupIcon.IconnextBackupIcon).IcontoLocaleStringIcon() : 'IconNotIcon Iconscheduled'}
          <IconIconIcon/IconTypographyIcon>
        <IconIconIcon/IconStackIcon>
      <IconIconIcon/IconAlertIcon>
      <IconFormControlLabelIcon
        IconcontrolIcon={
          <IconSwitchIcon
            IconcheckedIcon={IconsettingsIcon.IconbackupIcon.IconautoBackupEnabledIcon}
            IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconbackup', 'IconautoBackupEnabled', IconeIcon.IcontargetIcon.IconcheckedIcon)}
            IcondisabledIcon={IconreadOnlyIcon}
          />
        }
        IconlabelIcon="IconEnableIcon IconAutomaticIcon IconBackups"
      />
      {IconsettingsIcon.IconbackupIcon.IconautoBackupEnabledIcon && (
        <IconIconIcon>
          <IconFormControlIcon IconfullWidthIcon IcondisabledIcon={IconreadOnlyIcon}>
            <IconInputLabelIcon>IconBackupIcon IconFrequencyIcon<IconIconIcon/IconInputLabelIcon>
            <IconSelectIcon
              IconvalueIcon={IconsettingsIcon.IconbackupIcon.IconbackupFrequencyIcon}
              IconlabelIcon="IconBackupIcon IconFrequency"
              IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconbackup', 'IconbackupFrequency', IconeIcon.IcontargetIcon.IconvalueIcon)}
            >
              <IconMenuItemIcon IconvalueIcon="Icondaily">IconDailyIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Iconweekly">IconWeeklyIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Iconmonthly">IconMonthlyIcon<IconIconIcon/IconMenuItemIcon>
            <IconIconIcon/IconSelectIcon>
          <IconIconIcon/IconFormControlIcon>
          <IconTextFieldIcon
            IconlabelIcon="IconBackupIcon IconTime"
            IcontypeIcon="Icontime"
            IconvalueIcon={IconsettingsIcon.IconbackupIcon.IconbackupTimeIcon}
            IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconbackup', 'IconbackupTime', IconeIcon.IcontargetIcon.IconvalueIcon)}
            IconfullWidthIcon
            IcondisabledIcon={IconreadOnlyIcon}
            IconInputLabelPropsIcon={{ IconshrinkIcon: IcontrueIcon }}
          />
          <IconTextFieldIcon
            IconlabelIcon="IconRetentionIcon IconPeriodIcon (IcondaysIcon)"
            IcontypeIcon="Iconnumber"
            IconvalueIcon={IconsettingsIcon.IconbackupIcon.IconbackupRetentionIcon}
            IcononChangeIcon={(IconeIcon) => IconhandleSettingChangeIcon('Iconbackup', 'IconbackupRetention', IconparseIntIcon(IconeIcon.IcontargetIcon.IconvalueIcon))}
            IconfullWidthIcon
            IcondisabledIcon={IconreadOnlyIcon}
          />
        <IconIconIcon/>
      )}
      <IconButtonIcon
        IconvariantIcon="Iconfilled"
        IconstartIconIcon={<IconIconBackupIcon />}
        IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleRunBackupIcon}
        IcondisabledIcon={IconreadOnlyIcon || IconsavingIcon}
      >
        IconRunIcon IconManualIcon IconBackupIcon IconNowIcon
      <IconIconIcon/IconButtonIcon>
    <IconIconIcon/IconStackIcon>
  );
  IconreturnIcon (
    <IconPaperIcon IconstyleIcon={{ IconheightIcon: 'Icon100Icon%', IcondisplayIcon: 'Iconflex', IconflexDirectionIcon: 'Iconcolumn' }}>
      {/* IconHeaderIcon */}
      <IconBoxIcon IconstyleIcon={{ IconpIcon: Icon2Icon, IconborderBottomIcon: Icon1Icon, IconborderColorIcon: 'Icondivider' }}>
        <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
          <IconTypographyIcon IconorderIcon={Icon6Icon} IconfontWeightIcon="Iconbold">
            IconSystemIcon IconSettingsIcon
          <IconIconIcon/IconTypographyIcon>
          <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon}>
            {IconallowDangerousActionsIcon && (
              <IconButtonIcon
                IconsizeIcon="Iconsmall"
                IconcolorIcon="Iconred"
                IconstartIconIcon={<IconIconRestartAltIcon />}
                IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleResetSettingsIcon}
                IcondisabledIcon={IconreadOnlyIcon}
              >
                IconResetIcon IcontoIcon IconDefaultsIcon
              <IconIconIcon/IconButtonIcon>
            )}
            <IconButtonIcon
              IconvariantIcon="Iconfilled"
              IconsizeIcon="Iconsmall"
              IconstartIconIcon={<IconIconDeviceFloppyIcon />}
              IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleSaveSettingsIcon}
              IcondisabledIcon={IconreadOnlyIcon || IconsavingIcon}
            >
              IconSaveIcon IconChangesIcon
            <IconIconIcon/IconButtonIcon>
          <IconIconIcon/IconStackIcon>
        <IconIconIcon/IconStackIcon>
      <IconIconIcon/IconBoxIcon>
      {/* IconLoadingIcon */}
      {IconloadingIcon && <IconLinearProgressIcon />}
      {/* IconAlertsIcon */}
      {IconerrorIcon && (
        <IconAlertIcon IconseverityIcon="Iconerror" IcononCloseIcon={() => IconsetErrorIcon(IconnullIcon)} IconstyleIcon={{ IconmIcon: Icon2Icon }}>
          {IconerrorIcon}
        <IconIconIcon/IconAlertIcon>
      )}
      {IconsuccessIcon && (
        <IconAlertIcon IconseverityIcon="Iconsuccess" IcononCloseIcon={() => IconsetSuccessIcon(IconnullIcon)} IconstyleIcon={{ IconmIcon: Icon2Icon }}>
          {IconsuccessIcon}
        <IconIconIcon/IconAlertIcon>
      )}
      {/* IconContentIcon */}
      <IconBoxIcon IconstyleIcon={{ IconflexIcon: Icon1Icon, IconoverflowIcon: 'Iconauto', IconpIcon: Icon2Icon }}>
        {/* IconGeneralIcon IconSettingsIcon */}
        <IconAccordionIcon
          IconexpandedIcon={IconexpandedPanelIcon === 'Icongeneral'}
          IcononChangeIcon={(Icon_Icon, IconisExpandedIcon) => IconsetExpandedPanelIcon(IconisExpandedIcon ? 'Icongeneral' : IconfalseIcon)}
        >
          <IconAccordionSummaryIcon IconexpandIconIcon={<IconIconChevronDownIcon />}>
            <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon} IconalignItemsIcon="Iconcenter">
              <IconIconSettingsIcon />
              <IconTypographyIcon>IconGeneralIcon IconSettingsIcon<IconIconIcon/IconTypographyIcon>
            <IconIconIcon/IconStackIcon>
          <IconIconIcon/IconAccordionSummaryIcon>
          <IconAccordionDetailsIcon>{IconrenderGeneralSettingsIcon()}<IconIconIcon/IconAccordionDetailsIcon>
        <IconIconIcon/IconAccordionIcon>
        {/* IconSecurityIcon IconSettingsIcon */}
        <IconAccordionIcon
          IconexpandedIcon={IconexpandedPanelIcon === 'Iconsecurity'}
          IcononChangeIcon={(Icon_Icon, IconisExpandedIcon) => IconsetExpandedPanelIcon(IconisExpandedIcon ? 'Iconsecurity' : IconfalseIcon)}
        >
          <IconAccordionSummaryIcon IconexpandIconIcon={<IconIconChevronDownIcon />}>
            <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon} IconalignItemsIcon="Iconcenter">
              <IconIconSecurityIcon />
              <IconTypographyIcon>IconSecurityIcon IconSettingsIcon<IconIconIcon/IconTypographyIcon>
            <IconIconIcon/IconStackIcon>
          <IconIconIcon/IconAccordionSummaryIcon>
          <IconAccordionDetailsIcon>{IconrenderSecuritySettingsIcon()}<IconIconIcon/IconAccordionDetailsIcon>
        <IconIconIcon/IconAccordionIcon>
        {/* IconPerformanceIcon IconSettingsIcon */}
        <IconAccordionIcon
          IconexpandedIcon={IconexpandedPanelIcon === 'Iconperformance'}
          IcononChangeIcon={(Icon_Icon, IconisExpandedIcon) => IconsetExpandedPanelIcon(IconisExpandedIcon ? 'Iconperformance' : IconfalseIcon)}
        >
          <IconAccordionSummaryIcon IconexpandIconIcon={<IconIconChevronDownIcon />}>
            <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon} IconalignItemsIcon="Iconcenter">
              <IconIconSpeedIcon />
              <IconTypographyIcon>IconPerformanceIcon IconSettingsIcon<IconIconIcon/IconTypographyIcon>
            <IconIconIcon/IconStackIcon>
          <IconIconIcon/IconAccordionSummaryIcon>
          <IconAccordionDetailsIcon>{IconrenderPerformanceSettingsIcon()}<IconIconIcon/IconAccordionDetailsIcon>
        <IconIconIcon/IconAccordionIcon>
        {/* IconBackupIcon IconSettingsIcon */}
        <IconAccordionIcon
          IconexpandedIcon={IconexpandedPanelIcon === 'Iconbackup'}
          IcononChangeIcon={(Icon_Icon, IconisExpandedIcon) => IconsetExpandedPanelIcon(IconisExpandedIcon ? 'Iconbackup' : IconfalseIcon)}
        >
          <IconAccordionSummaryIcon IconexpandIconIcon={<IconIconChevronDownIcon />}>
            <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon} IconalignItemsIcon="Iconcenter">
              <IconIconBackupIcon />
              <IconTypographyIcon>IconBackupIcon IconSettingsIcon<IconIconIcon/IconTypographyIcon>
            <IconIconIcon/IconStackIcon>
          <IconIconIcon/IconAccordionSummaryIcon>
          <IconAccordionDetailsIcon>{IconrenderBackupSettingsIcon()}<IconIconIcon/IconAccordionDetailsIcon>
        <IconIconIcon/IconAccordionIcon>
      <IconIconIcon/IconBoxIcon>
      {/* IconConfirmationIcon IconDialogIcon */}
      <IconDialogIcon IconopenIcon={IconconfirmDialogOpenIcon} IcononCloseIcon={() => IconsetConfirmDialogOpenIcon(IconfalseIcon)}>
        <IconDialogTitleIcon>IconConfirmIcon IconActionIcon<IconIconIcon/IconDialogTitleIcon>
        <IconDialogContentIcon>
          <IconTypographyIcon>
            {IconconfirmActionIcon === 'Iconreset'
              ? 'IconAreIcon IconyouIcon IconsureIcon IconyouIcon IconwantIcon IcontoIcon IconresetIcon IconallIcon IconsettingsIcon IcontoIcon IcondefaultsIcon? IconThisIcon IconactionIcon IconcannotIcon IconbeIcon IconundoneIcon.'
              : 'IconAreIcon IconyouIcon IconsureIcon IconyouIcon IconwantIcon IcontoIcon IconproceedIcon IconwithIcon IconthisIcon IconactionIcon?'}
          <IconIconIcon/IconTypographyIcon>
        <IconIconIcon/IconDialogContentIcon>
        <IconDialogActionsIcon>
          <IconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconsetConfirmDialogOpenIcon(IconfalseIcon)}>IconCancelIcon<IconIconIcon/IconButtonIcon>
          <IconButtonIcon
            IconvariantIcon="Iconfilled"
            IconcolorIcon="Iconred"
            IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
              IconifIcon (IconconfirmActionIcon === 'Iconreset') {
                // IconResetIcon IconsettingsIcon IcontoIcon IcondefaultsIcon
                IconfetchSettingsIcon();
              }
              IconsetConfirmDialogOpenIcon(IconfalseIcon);
            }}
          >
            IconConfirmIcon
          <IconIconIcon/IconButtonIcon>
        <IconIconIcon/IconDialogActionsIcon>
      <IconIconIcon/IconDialogIcon>
    <IconIconIcon/IconPaperIcon>
  );
});
IconSystemSettingsPanelIcon.IcondisplayNameIcon = 'IconSystemSettingsPanel';
IconexportIcon IcondefaultIcon IconSystemSettingsPanelIcon;