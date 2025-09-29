IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../../../IconutilsIcon/IconmuiIcon-Iconimports';
/**
 * IconSystemHealthDashboardIcon - IconComprehensiveIcon IconSystemIcon IconHealthIcon IconMonitoringIcon IconPageIcon
 * IconCombinesIcon IconallIcon IconhealthIcon IconmonitoringIcon IconcomponentsIcon IconforIcon IconadministratorsIcon
 */
IconimportIcon { IconmemoIcon, IconuseStateIcon, IconuseEffectIcon } IconfromIcon 'Iconreact';

IconimportIcon {
  IconDashboardIcon IconasIcon IconIconDashboardIcon,
  IconRefreshIcon IconasIcon IconIconRefreshIcon,
  IconSettingsIcon IconasIcon IconIconSettingsIcon,
  IconDownloadIcon IconasIcon IconIconDownloadIcon,
  IconNotificationsIcon IconasIcon IconIconBellIcon,
  IconTimelineIcon IconasIcon IconIconTimelineIcon,
  IconSecurityIcon IconasIcon IconIconSecurityIcon,
  IconSpeedIcon IconasIcon IconIconSpeedIcon,
  IconApiIcon IconasIcon IconIconApiIcon,
  IconStorageIcon IconasIcon IconIconStorageIcon,
  IconGamesIcon IconasIcon IconIconGamesIcon,
  IconHubIcon IconasIcon IconIconHubIcon,
  IconStreamIcon IconasIcon IconIconStreamIcon,
  IconWarningIcon IconasIcon IconIconAlertTriangleIcon,
  IconCheckCircleIcon IconasIcon IconIconCircleCheckIcon,
  IconErrorIcon IconasIcon IconIconCircleXIcon,
} IconfromIcon '@IconmuiIcon/IconiconsIcon-Iconmaterial';

IconimportIcon { IconmotionIcon } IconfromIcon 'IconframerIcon-Iconmotion';
IconimportIcon IconSystemHealthMonitorIcon IconfromIcon '../IconmonitoringIcon/IconSystemHealthMonitor';
IconimportIcon IconIntegrationHealthMonitorIcon IconfromIcon '../IconmonitoringIcon/IconIntegrationHealthMonitor';
IconimportIcon { IconapiIcon } IconfromIcon '@/IconservicesIcon/Iconapi';
IconimportIcon { IconusePusherIcon } IconfromIcon '@/IconhooksIcon/IconusePusher';
IconimportIcon { IconIconIcon, IconIconAlertTriangleIcon, IconIconApiIcon, IconIconBellIcon, IconIconCircleCheckIcon, IconIconCircleXIcon, IconIconDashboardIcon, IconIconDownloadIcon, IconIconGamesIcon, IconIconHubIcon, IconIconRefreshIcon, IconIconSecurityIcon, IconIconSettingsIcon, IconIconSpeedIcon, IconIconStorageIcon, IconIconStreamIcon, IconIconTimelineIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';

IconinterfaceIcon IconTabPanelPropsIcon {
  IconchildrenIcon?: IconReactIcon.IconReactNodeIcon;
  IconindexIcon: IconnumberIcon;
  IconvalueIcon: IconnumberIcon;
}

IconfunctionIcon IconTabPanelIcon(IconpropsIcon: IconTabPanelPropsIcon) {
  IconconstIcon { IconchildrenIcon, IconvalueIcon, IconindexIcon, ...IconotherIcon } = IconpropsIcon;

  IconreturnIcon (
    <IcondivIcon
      IconroleIcon="Icontabpanel"
      IconhiddenIcon={IconvalueIcon !== IconindexIcon}
      IconidIcon={`IconhealthIcon-IcontabpanelIcon-${IconindexIcon}`}
      IconariaIcon-IconlabelledbyIcon={`IconhealthIcon-IcontabIcon-${IconindexIcon}`}
      {...IconotherIcon}
    >
      {IconvalueIcon === IconindexIcon && <IconBoxIcon IconstyleIcon={{ IconpIcon: Icon3Icon }}>{IconchildrenIcon}<IconIconIcon/IconBoxIcon>}
    <IconIconIcon/IcondivIcon>
  );
}

IconexportIcon IconinterfaceIcon IconSystemHealthDashboardPropsIcon {
  IconautoRefreshIcon?: IconbooleanIcon;
  IconrefreshIntervalIcon?: IconnumberIcon;
}

IconconstIcon IconMotionContainerIcon = IconmotionIcon(IconContainerIcon);

IconexportIcon IconconstIcon IconSystemHealthDashboardIcon = IconmemoIcon<IconSystemHealthDashboardPropsIcon>(({
  IconautoRefreshIcon = IcontrueIcon,
  IconrefreshIntervalIcon = Icon30000Icon,
}) => {
  IconconstIcon IconthemeIcon = IconuseThemeIcon();
  IconconstIcon [IconcurrentTabIcon, IconsetCurrentTabIcon] = IconuseStateIcon(Icon0Icon);
  IconconstIcon [IconautoRefreshEnabledIcon, IconsetAutoRefreshEnabledIcon] = IconuseStateIcon(IconautoRefreshIcon);
  IconconstIcon [IconsettingsOpenIcon, IconsetSettingsOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconexportOpenIcon, IconsetExportOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconalertsEnabledIcon, IconsetAlertsEnabledIcon] = IconuseStateIcon(IcontrueIcon);
  IconconstIcon [IconlastSystemRefreshIcon, IconsetLastSystemRefreshIcon] = IconuseStateIcon(IconnewIcon IconDateIcon());
  IconconstIcon [IconsystemOverallHealthIcon, IconsetSystemOverallHealthIcon] = IconuseStateIcon<IconstringIcon>('Iconunknown');

  // IconSetupIcon IconPusherIcon IconforIcon IconsystemIcon-IconwideIcon IconhealthIcon IconalertsIcon
  IconconstIcon { IconsubscribeIcon, IconunsubscribeIcon } = IconusePusherIcon();

  IconuseEffectIcon(() => {
    IconconstIcon IconchannelIcon = 'IconsystemIcon-Iconhealth';

    IconconstIcon IconhandleSystemAlertIcon = (IcondataIcon: { IconlevelIcon: IconstringIcon; IconmessageIcon: IconstringIcon; IcontimestampIcon: IconstringIcon }) => {
      IconifIcon (IconalertsEnabledIcon && IcondataIcon.IconlevelIcon === 'Iconcritical') {
        // IconYouIcon IconcouldIcon IcontriggerIcon IconnotificationsIcon IconhereIcon
        IconconsoleIcon.IconwarnIcon('IconSystemIcon IconHealthIcon IconAlertIcon:', IcondataIcon);
      }
    };

    IconconstIcon IconhandleOverallHealthUpdateIcon = (IcondataIcon: { IconstatusIcon: IconstringIcon; IcontimestampIcon: IconstringIcon }) => {
      IconsetSystemOverallHealthIcon(IcondataIcon.IconstatusIcon);
      IconsetLastSystemRefreshIcon(IconnewIcon IconDateIcon(IcondataIcon.IcontimestampIcon));
    };

    IconsubscribeIcon(IconchannelIcon, 'IconsystemIcon-Iconalert', IconhandleSystemAlertIcon);
    IconsubscribeIcon(IconchannelIcon, 'IconoverallIcon-Iconhealth', IconhandleOverallHealthUpdateIcon);

    IconreturnIcon () => {
      IconunsubscribeIcon(IconchannelIcon, 'IconsystemIcon-Iconalert', IconhandleSystemAlertIcon);
      IconunsubscribeIcon(IconchannelIcon, 'IconoverallIcon-Iconhealth', IconhandleOverallHealthUpdateIcon);
    };
  }, [IconsubscribeIcon, IconunsubscribeIcon, IconalertsEnabledIcon]);

  IconconstIcon IconhandleTabChangeIcon = (IconeventIcon: IconReactIcon.IconSyntheticEventIcon, IconnewValueIcon: IconnumberIcon) => {
    IconsetCurrentTabIcon(IconnewValueIcon);
  };

  IconconstIcon IconhandleGlobalRefreshIcon = IconasyncIcon () => {
    IcontryIcon {
      // IconTriggerIcon IconaIcon IconrefreshIcon IcononIcon IconallIcon IconhealthIcon IconmonitoringIcon IconcomponentsIcon
      IconsetLastSystemRefreshIcon(IconnewIcon IconDateIcon());

      // IconYouIcon IconcouldIcon IconalsoIcon IcontriggerIcon IconaIcon IconmanualIcon IconrefreshIcon IconofIcon IconallIcon IconservicesIcon IconhereIcon
      IconawaitIcon IconapiIcon.IconpostIcon('/IconapiIcon/Iconv1Icon/IconhealthIcon/IconrefreshIcon-Iconall');
    } IconcatchIcon (IconerrorIcon) {
      IconconsoleIcon.IconerrorIcon('IconFailedIcon IcontoIcon IconrefreshIcon IconsystemIcon IconhealthIcon:', IconerrorIcon);
    }
  };

  IconconstIcon IconhandleExportHealthIcon = IconasyncIcon () => {
    IcontryIcon {
      IconconstIcon IconresponseIcon = IconawaitIcon IconapiIcon.IcongetIcon('/IconapiIcon/Iconv1Icon/IconhealthIcon/Iconexport', {
        IconresponseTypeIcon: 'Iconblob',
      });

      IconconstIcon IconblobIcon = IconnewIcon IconBlobIcon([IconresponseIcon.IcondataIcon], { IcontypeIcon: 'IconapplicationIcon/Iconjson' });
      IconconstIcon IconurlIcon = IconwindowIcon.IconURLIcon.IconcreateObjectURLIcon(IconblobIcon);
      IconconstIcon IconlinkIcon = IcondocumentIcon.IconcreateElementIcon('Icona');
      IconlinkIcon.IconhrefIcon = IconurlIcon;
      IconlinkIcon.IcondownloadIcon = `IconsystemIcon-IconhealthIcon-${IconnewIcon IconDateIcon().IcontoISOStringIcon().IconsplitIcon('IconT')[Icon0Icon]}.IconjsonIcon`;
      IcondocumentIcon.IconbodyIcon.IconappendChildIcon(IconlinkIcon);
      IconlinkIcon.IconclickIcon();
      IcondocumentIcon.IconbodyIcon.IconremoveChildIcon(IconlinkIcon);
      IconwindowIcon.IconURLIcon.IconrevokeObjectURLIcon(IconurlIcon);

      IconsetExportOpenIcon(IconfalseIcon);
    } IconcatchIcon (IconerrorIcon) {
      IconconsoleIcon.IconerrorIcon('IconFailedIcon IcontoIcon IconexportIcon IconhealthIcon IcondataIcon:', IconerrorIcon);
    }
  };

  IconconstIcon IcongetOverallStatusColorIcon = (IconstatusIcon: IconstringIcon) => {
    IconswitchIcon (IconstatusIcon) {
      IconcaseIcon 'Iconhealthy':
        IconreturnIcon IconthemeIcon.IconpaletteIcon.IconsuccessIcon.IconmainIcon;
      IconcaseIcon 'Icondegraded':
        IconreturnIcon IconthemeIcon.IconpaletteIcon.IconwarningIcon.IconmainIcon;
      IconcaseIcon 'Iconunhealthy':
        IconreturnIcon IconthemeIcon.IconpaletteIcon.IconerrorIcon.IconmainIcon;
      IcondefaultIcon:
        IconreturnIcon IconthemeIcon.IconpaletteIcon.IcontextIcon.IconsecondaryIcon;
    }
  };

  IconconstIcon IcongetOverallStatusIconIcon = (IconstatusIcon: IconstringIcon) => {
    IconswitchIcon (IconstatusIcon) {
      IconcaseIcon 'Iconhealthy':
        IconreturnIcon <IconIconCircleCheckIcon IconfontSizeIcon="Iconsmall" />;
      IconcaseIcon 'Icondegraded':
        IconreturnIcon <IconIconAlertTriangleIcon IconfontSizeIcon="Iconsmall" />;
      IconcaseIcon 'Iconunhealthy':
        IconreturnIcon <IconIconCircleXIcon IconfontSizeIcon="Iconsmall" />;
      IcondefaultIcon:
        IconreturnIcon <IconIconAlertTriangleIcon IconfontSizeIcon="Iconsmall" />;
    }
  };

  IconconstIcon IcontabsIcon = [
    {
      IconlabelIcon: 'IconOverview',
      IconiconIcon: <IconIconDashboardIcon />,
      IcondescriptionIcon: 'IconSystemIcon IconmetricsIcon IconandIcon IconresourceIcon Iconmonitoring',
    },
    {
      IconlabelIcon: 'IconIntegrations',
      IconiconIcon: <IconIconApiIcon />,
      IcondescriptionIcon: 'IconExternalIcon IconAPIIcon IconandIcon IconserviceIcon Iconhealth',
    },
    {
      IconlabelIcon: 'IconDatabase',
      IconiconIcon: <IconIconStorageIcon />,
      IcondescriptionIcon: 'IconPostgreSQLIcon IconandIcon IconRedisIcon Iconconnectivity',
    },
    {
      IconlabelIcon: 'IconRealIcon-Icontime',
      IconiconIcon: <IconIconStreamIcon />,
      IcondescriptionIcon: 'IconPusherIcon IconandIcon IconWebSocketIcon Iconservices',
    },
    {
      IconlabelIcon: 'IconAgents',
      IconiconIcon: <IconIconHubIcon />,
      IcondescriptionIcon: 'IconAIIcon IconagentIcon IconorchestrationIcon Iconstatus',
    },
    {
      IconlabelIcon: 'IconRoblox',
      IconiconIcon: <IconIconGamesIcon />,
      IcondescriptionIcon: 'IconRobloxIcon IconintegrationIcon Iconservices',
    },
  ];

  IconreturnIcon (
    <IconMotionContainerIcon
      IconmaxWidthIcon="Iconxl"
      IconinitialIcon={{ IconopacityIcon: Icon0Icon, IconyIcon: Icon20Icon }}
      IconanimateIcon={{ IconopacityIcon: Icon1Icon, IconyIcon: Icon0Icon }}
      IcontransitionIcon={{ IcondurationIcon: Icon0Icon.Icon5Icon }}
    >
      <IconStackIcon IconspacingIcon={Icon3Icon} IconstyleIcon={{ IconpyIcon: Icon3Icon }}>
        {/* IconHeaderIcon */}
        <IconPaperIcon IconstyleIcon={{ IconpIcon: Icon3Icon }}>
          <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
            <IconStackIcon IconspacingIcon={Icon1Icon}>
              <IconTypographyIcon IconorderIcon={Icon4Icon} IconfontWeightIcon="Iconbold">
                IconSystemIcon IconHealthIcon IconDashboardIcon
              <IconIconIcon/IconTypographyIcon>
              <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconspacingIcon={Icon2Icon}>
                <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
                  IconRealIcon-IcontimeIcon IconmonitoringIcon IconandIcon IcondiagnosticsIcon IconforIcon IconallIcon IconsystemIcon IconcomponentsIcon
                <IconIconIcon/IconTypographyIcon>
                <IconChipIcon
                  IconlabelIcon={`IconSystemIcon: ${IconsystemOverallHealthIcon.IcontoUpperCaseIcon()}`}
                  IconsizeIcon="Iconsmall"
                  IconcolorIcon={
                    IconsystemOverallHealthIcon === 'Iconhealthy'
                      ? 'Iconsuccess'
                      : IconsystemOverallHealthIcon === 'Icondegraded'
                      ? 'Iconwarning'
                      : 'Iconerror'
                  }
                  IconiconIcon={IcongetOverallStatusIconIcon(IconsystemOverallHealthIcon)}
                />
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconStackIcon>

            <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon}>
              <IconFormControlLabelIcon
                IconcontrolIcon={
                  <IconSwitchIcon
                    IconcheckedIcon={IconautoRefreshEnabledIcon}
                    IcononChangeIcon={(IconeIcon) => IconsetAutoRefreshEnabledIcon(IconeIcon.IcontargetIcon.IconcheckedIcon)}
                    IconsizeIcon="Iconsmall"
                  />
                }
                IconlabelIcon="IconAutoIcon-Iconrefresh"
              />

              <IconTooltipIcon IcontitleIcon="IconRefreshIcon IconallIcon IconhealthIcon Iconchecks">
                <IconIconButtonIcon IcononClickIcon={IconhandleGlobalRefreshIcon} IconcolorIcon="Iconblue">
                  <IconIconRefreshIcon />
                <IconIconIcon/IconIconButtonIcon>
              <IconIconIcon/IconTooltipIcon>

              <IconTooltipIcon IcontitleIcon="IconExportIcon IconhealthIcon Icondata">
                <IconIconButtonIcon IcononClickIcon={() => IconsetExportOpenIcon(IcontrueIcon)} IconcolorIcon="Iconblue">
                  <IconIconDownloadIcon />
                <IconIconIcon/IconIconButtonIcon>
              <IconIconIcon/IconTooltipIcon>

              <IconTooltipIcon IcontitleIcon="IconSettings">
                <IconIconButtonIcon IcononClickIcon={() => IconsetSettingsOpenIcon(IcontrueIcon)} IconcolorIcon="Iconblue">
                  <IconIconSettingsIcon />
                <IconIconIcon/IconIconButtonIcon>
              <IconIconIcon/IconTooltipIcon>
            <IconIconIcon/IconStackIcon>
          <IconIconIcon/IconStackIcon>
        <IconIconIcon/IconPaperIcon>

        {/* IconHealthIcon IconStatusIcon IconAlertIcon */}
        {IconsystemOverallHealthIcon === 'Iconunhealthy' && (
          <IconAlertIcon IconseverityIcon="Iconerror">
            <IconAlertTitleIcon>IconSystemIcon IconHealthIcon IconWarningIcon<IconIconIcon/IconAlertTitleIcon>
            IconOneIcon IconorIcon IconmoreIcon IconcriticalIcon IconsystemIcon IconcomponentsIcon IconareIcon IconexperiencingIcon IconissuesIcon. IconCheckIcon IcontheIcon IcondetailedIcon IcontabsIcon IconbelowIcon IconforIcon IconmoreIcon IconinformationIcon.
          <IconIconIcon/IconAlertIcon>
        )}

        {IconsystemOverallHealthIcon === 'Icondegraded' && (
          <IconAlertIcon IconseverityIcon="Iconwarning">
            <IconAlertTitleIcon>IconSystemIcon IconPerformanceIcon IconDegradedIcon<IconIconIcon/IconAlertTitleIcon>
            IconSomeIcon IconsystemIcon IconcomponentsIcon IconareIcon IconnotIcon IconperformingIcon IconoptimallyIcon. IconMonitorIcon IcontheIcon IconsituationIcon IconandIcon IconconsiderIcon IcontakingIcon IconactionIcon IconifIcon IconperformanceIcon IconcontinuesIcon IcontoIcon IcondegradeIcon.
          <IconIconIcon/IconAlertIcon>
        )}

        {/* IconNavigationIcon IconTabsIcon */}
        <IconPaperIcon>
          <IconTabsIcon
            IconvalueIcon={IconcurrentTabIcon}
            IcononChangeIcon={IconhandleTabChangeIcon}
            IconvariantIcon="Iconscrollable"
            IconscrollButtonsIcon="Iconauto"
            IconstyleIcon={{ IconborderBottomIcon: Icon1Icon, IconborderColorIcon: 'Icondivider' }}
          >
            {IcontabsIcon.IconmapIcon((IcontabIcon, IconindexIcon) => (
              <IconTabIcon
                IconkeyIcon={IconindexIcon}
                IconlabelIcon={IcontabIcon.IconlabelIcon}
                IconiconIcon={IcontabIcon.IconiconIcon}
                IconiconPositionIcon="Iconstart"
                IconstyleIcon={{ IconminHeightIcon: Icon72Icon }}
              />
            ))}
          <IconIconIcon/IconTabsIcon>

          {/* IconTabIcon IconPanelsIcon */}
          <IconTabPanelIcon IconvalueIcon={IconcurrentTabIcon} IconindexIcon={Icon0Icon}>
            <IconSystemHealthMonitorIcon
              IconautoRefreshIcon={IconautoRefreshEnabledIcon}
              IconrefreshIntervalIcon={IconrefreshIntervalIcon}
              IconshowChartsIcon={IcontrueIcon}
              IconcompactIcon={IconfalseIcon}
            />
          <IconIconIcon/IconTabPanelIcon>

          <IconTabPanelIcon IconvalueIcon={IconcurrentTabIcon} IconindexIcon={Icon1Icon}>
            <IconIntegrationHealthMonitorIcon
              IconautoRefreshIcon={IconautoRefreshEnabledIcon}
              IconrefreshIntervalIcon={IconrefreshIntervalIcon}
              IconshowDetailsIcon={IcontrueIcon}
            />
          <IconIconIcon/IconTabPanelIcon>

          <IconTabPanelIcon IconvalueIcon={IconcurrentTabIcon} IconindexIcon={Icon2Icon}>
            <IconCardIcon>
              <IconCardHeaderIcon IcontitleIcon="IconDatabaseIcon IconHealth" IconsubheaderIcon="IconPostgreSQLIcon IconandIcon IconRedisIcon IconconnectionIcon Iconmonitoring" />
              <IconCardContentIcon>
                <IconTypographyIcon>
                  IconDetailedIcon IcondatabaseIcon IconhealthIcon IconmonitoringIcon IconwillIcon IconbeIcon IcondisplayedIcon IconhereIcon.
                  IconThisIcon IconwouldIcon IconincludeIcon IconconnectionIcon IconpoolsIcon, IconqueryIcon IconperformanceIcon, IconandIcon IconcacheIcon IconhitIcon IconratesIcon.
                <IconIconIcon/IconTypographyIcon>
              <IconIconIcon/IconCardContentIcon>
            <IconIconIcon/IconCardIcon>
          <IconIconIcon/IconTabPanelIcon>

          <IconTabPanelIcon IconvalueIcon={IconcurrentTabIcon} IconindexIcon={Icon3Icon}>
            <IconCardIcon>
              <IconCardHeaderIcon IcontitleIcon="IconRealIcon-IcontimeIcon IconServices" IconsubheaderIcon="IconPusherIcon IconChannelsIcon IconandIcon IconWebSocketIcon Iconmonitoring" />
              <IconCardContentIcon>
                <IconTypographyIcon>
                  IconRealIcon-IcontimeIcon IconserviceIcon IconmonitoringIcon IconincludingIcon IconPusherIcon IconchannelIcon IconhealthIcon,
                  IconWebSocketIcon IconconnectionIcon IconcountsIcon, IconandIcon IconmessageIcon IconthroughputIcon.
                <IconIconIcon/IconTypographyIcon>
              <IconIconIcon/IconCardContentIcon>
            <IconIconIcon/IconCardIcon>
          <IconIconIcon/IconTabPanelIcon>

          <IconTabPanelIcon IconvalueIcon={IconcurrentTabIcon} IconindexIcon={Icon4Icon}>
            <IconCardIcon>
              <IconCardHeaderIcon IcontitleIcon="IconAgentIcon IconOrchestration" IconsubheaderIcon="IconAIIcon IconagentIcon IconsystemIcon Iconmonitoring" />
              <IconCardContentIcon>
                <IconTypographyIcon>
                  IconAgentIcon IconsystemIcon IconhealthIcon IconincludingIcon IconMCPIcon IconserverIcon IconstatusIcon, IconagentIcon IconcoordinatorIcon IconhealthIcon,
                  IconandIcon IconSPARCIcon IconframeworkIcon IconmonitoringIcon.
                <IconIconIcon/IconTypographyIcon>
              <IconIconIcon/IconCardContentIcon>
            <IconIconIcon/IconCardIcon>
          <IconIconIcon/IconTabPanelIcon>

          <IconTabPanelIcon IconvalueIcon={IconcurrentTabIcon} IconindexIcon={Icon5Icon}>
            <IconCardIcon>
              <IconCardHeaderIcon IcontitleIcon="IconRobloxIcon IconIntegration" IconsubheaderIcon="IconRobloxIcon-IconspecificIcon IconserviceIcon Iconmonitoring" />
              <IconCardContentIcon>
                <IconTypographyIcon>
                  IconRobloxIcon IconintegrationIcon IconhealthIcon IconincludingIcon IconFlaskIcon IconbridgeIcon IconstatusIcon,
                  IconpluginIcon IconcommunicationIcon, IconandIcon IconcontentIcon IcongenerationIcon IconservicesIcon.
                <IconIconIcon/IconTypographyIcon>
              <IconIconIcon/IconCardContentIcon>
            <IconIconIcon/IconCardIcon>
          <IconIconIcon/IconTabPanelIcon>
        <IconIconIcon/IconPaperIcon>
      <IconIconIcon/IconStackIcon>

      {/* IconSettingsIcon IconDialogIcon */}
      <IconDialogIcon IconopenIcon={IconsettingsOpenIcon} IcononCloseIcon={() => IconsetSettingsOpenIcon(IconfalseIcon)} IconmaxWidthIcon="Iconsm" IconfullWidthIcon>
        <IconDialogTitleIcon>IconHealthIcon IconMonitoringIcon IconSettingsIcon<IconIconIcon/IconDialogTitleIcon>
        <IconDialogContentIcon>
          <IconStackIcon IconspacingIcon={Icon3Icon} IconstyleIcon={{ IconptIcon: Icon1Icon }}>
            <IconFormControlLabelIcon
              IconcontrolIcon={
                <IconSwitchIcon
                  IconcheckedIcon={IconalertsEnabledIcon}
                  IcononChangeIcon={(IconeIcon) => IconsetAlertsEnabledIcon(IconeIcon.IcontargetIcon.IconcheckedIcon)}
                />
              }
              IconlabelIcon="IconEnableIcon IconcriticalIcon Iconalerts"
            />

            <IconFormControlLabelIcon
              IconcontrolIcon={
                <IconSwitchIcon
                  IconcheckedIcon={IconautoRefreshEnabledIcon}
                  IcononChangeIcon={(IconeIcon) => IconsetAutoRefreshEnabledIcon(IconeIcon.IcontargetIcon.IconcheckedIcon)}
                />
              }
              IconlabelIcon="IconAutoIcon-IconrefreshIcon Iconenabled"
            />

            <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
              IconRefreshIcon IconintervalIcon: {IconrefreshIntervalIcon / Icon1000Icon} IconsecondsIcon
            <IconIconIcon/IconTypographyIcon>
          <IconIconIcon/IconStackIcon>
        <IconIconIcon/IconDialogContentIcon>
        <IconDialogActionsIcon>
          <IconButtonIcon IcononClickIcon={() => IconsetSettingsOpenIcon(IconfalseIcon)}>IconCloseIcon<IconIconIcon/IconButtonIcon>
        <IconIconIcon/IconDialogActionsIcon>
      <IconIconIcon/IconDialogIcon>

      {/* IconExportIcon IconDialogIcon */}
      <IconDialogIcon IconopenIcon={IconexportOpenIcon} IcononCloseIcon={() => IconsetExportOpenIcon(IconfalseIcon)} IconmaxWidthIcon="Iconsm" IconfullWidthIcon>
        <IconDialogTitleIcon>IconExportIcon IconHealthIcon IconDataIcon<IconIconIcon/IconDialogTitleIcon>
        <IconDialogContentIcon>
          <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
            IconExportIcon IconcomprehensiveIcon IconsystemIcon IconhealthIcon IcondataIcon IconasIcon IconJSONIcon IconforIcon IconanalysisIcon IconorIcon IconreportingIcon.
            IconThisIcon IconincludesIcon IconallIcon IconcurrentIcon IconhealthIcon IconmetricsIcon, IconintegrationIcon IconstatusesIcon, IconandIcon IconsystemIcon IconperformanceIcon IcondataIcon.
          <IconIconIcon/IconTypographyIcon>
        <IconIconIcon/IconDialogContentIcon>
        <IconDialogActionsIcon>
          <IconButtonIcon IcononClickIcon={() => IconsetExportOpenIcon(IconfalseIcon)}>IconCancelIcon<IconIconIcon/IconButtonIcon>
          <IconButtonIcon IcononClickIcon={IconhandleExportHealthIcon} IconvariantIcon="Iconfilled">
            IconExportIcon
          <IconIconIcon/IconButtonIcon>
        <IconIconIcon/IconDialogActionsIcon>
      <IconIconIcon/IconDialogIcon>
    <IconIconIcon/IconMotionContainerIcon>
  );
});

IconSystemHealthDashboardIcon.IcondisplayNameIcon = 'IconSystemHealthDashboard';
IconexportIcon IcondefaultIcon IconSystemHealthDashboardIcon;