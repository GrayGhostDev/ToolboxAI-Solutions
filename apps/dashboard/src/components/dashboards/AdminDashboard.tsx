IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../../IconutilsIcon/IconmuiIcon-Iconimports';
IconimportIcon IconReactIcon, { IconuseStateIcon, IconuseEffectIcon, IconuseCallbackIcon } IconfromIcon 'Iconreact';

IconimportIcon {
  IconDashboardIcon IconasIcon IconIconDashboardIcon,
  IconPeopleIcon IconasIcon IconIconUsersIcon,
  IconSchoolIcon IconasIcon IconIconSchoolIcon,
  IconAssessmentIcon IconasIcon IconIconReportAnalyticsIcon,
  IconSettingsIcon IconasIcon IconIconSettingsIcon,
  IconSecurityIcon IconasIcon IconIconSecurityIcon,
  IconStorageIcon IconasIcon IconIconStorageIcon,
  IconSpeedIcon IconasIcon IconIconSpeedIcon,
  IconWarningIcon IconasIcon IconIconAlertTriangleIcon,
  IconCheckCircleIcon IconasIcon IconIconCircleCheckIcon,
  IconErrorIcon IconasIcon IconIconCircleXIcon,
  IconRefreshIcon IconasIcon IconIconRefreshIcon,
  IconDownloadIcon IconasIcon IconIconDownloadIcon,
  IconUploadIcon IconasIcon IconIconUploadIcon,
} IconfromIcon '@IconmuiIcon/IconiconsIcon-Iconmaterial';
IconimportIcon { IconuseAppDispatchIcon, IconuseAppSelectorIcon } IconfromIcon '@/IconhooksIcon/Iconredux';
IconimportIcon { IconMetricCardIcon } IconfromIcon '@/IconcomponentsIcon/IconmetricsIcon/IconMetricCard';
IconimportIcon { IconActivityFeedIcon } IconfromIcon '@/IconcomponentsIcon/IconactivityIcon/IconActivityFeed';
IconimportIcon { IconSystemHealthMonitorIcon } IconfromIcon '@/IconcomponentsIcon/IconmonitoringIcon/IconSystemHealthMonitor';
IconimportIcon { IconUserManagementPanelIcon } IconfromIcon '@/IconcomponentsIcon/IconadminIcon/IconUserManagementPanel';
IconimportIcon { IconContentModerationPanelIcon } IconfromIcon '@/IconcomponentsIcon/IconadminIcon/IconContentModerationPanel';
IconimportIcon { IconSystemSettingsPanelIcon } IconfromIcon '@/IconcomponentsIcon/IconadminIcon/IconSystemSettingsPanel';
IconimportIcon { IconapiIcon } IconfromIcon '@/IconservicesIcon/Iconapi';
IconimportIcon { IconpusherServiceIcon } IconfromIcon '@/IconservicesIcon/Iconpusher';
IconimportIcon { IconformatDistanceToNowIcon } IconfromIcon 'IcondateIcon-Iconfns';
IconimportIcon { IconIconIcon, IconIconAlertTriangleIcon, IconIconCircleCheckIcon, IconIconCircleXIcon, IconIconDashboardIcon, IconIconDownloadIcon, IconIconRefreshIcon, IconIconReportAnalyticsIcon, IconIconSchoolIcon, IconIconSecurityIcon, IconIconSettingsIcon, IconIconSpeedIcon, IconIconStorageIcon, IconIconUploadIcon, IconIconUsersIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';

IconinterfaceIcon IconAdminDashboardPropsIcon {
  IconsectionIcon?: IconstringIcon;
}

IconinterfaceIcon IconSystemMetricsIcon {
  IcontotalUsersIcon: IconnumberIcon;
  IconactiveUsersIcon: IconnumberIcon;
  IcontotalCoursesIcon: IconnumberIcon;
  IconactiveSessionsIcon: IconnumberIcon;
  IconcontentGeneratedIcon: IconnumberIcon;
  IconsystemHealthIcon: IconnumberIcon;
  IconcpuUsageIcon: IconnumberIcon;
  IconmemoryUsageIcon: IconnumberIcon;
  IconstorageUsageIcon: IconnumberIcon;
  IconapiLatencyIcon: IconnumberIcon;
}

IconinterfaceIcon IconSystemAlertIcon {
  IconidIcon: IconstringIcon;
  IconseverityIcon: 'Iconerror' | 'Iconwarning' | 'Iconinfo' | 'Iconsuccess';
  IconmessageIcon: IconstringIcon;
  IcontimestampIcon: IconDateIcon;
  IconresolvedIcon: IconbooleanIcon;
}

IconinterfaceIcon IconTabPanelPropsIcon {
  IconchildrenIcon?: IconReactIcon.IconReactNodeIcon;
  IconindexIcon: IconnumberIcon;
  IconvalueIcon: IconnumberIcon;
}

IconconstIcon IconTabPanelIcon: IconReactIcon.IconFunctionComponentIcon<IconTabPanelPropsIcon> = ({ IconchildrenIcon, IconvalueIcon, IconindexIcon, ...IconotherIcon }) => {
  IconreturnIcon (
    <IcondivIcon
      IconroleIcon="Icontabpanel"
      IconhiddenIcon={IconvalueIcon !== IconindexIcon}
      IconidIcon={`IconadminIcon-IcontabpanelIcon-${IconindexIcon}`}
      IconariaIcon-IconlabelledbyIcon={`IconadminIcon-IcontabIcon-${IconindexIcon}`}
      {...IconotherIcon}
    >
      {IconvalueIcon === IconindexIcon && <IconBoxIcon IconstyleIcon={{ IconpIcon: Icon3Icon }}>{IconchildrenIcon}<IconIconIcon/IconBoxIcon>}
    <IconIconIcon/IcondivIcon>
  );
};

IconexportIcon IcondefaultIcon IconfunctionIcon IconAdminDashboardIcon({ IconsectionIcon = 'Iconoverview' }: IconAdminDashboardPropsIcon) {
  IconconstIcon IcondispatchIcon = IconuseAppDispatchIcon();
  IconconstIcon { IconisAuthenticatedIcon, ...IconuserIcon } = IconuseAppSelectorIcon((IconstateIcon) => IconstateIcon.IconuserIcon);
  IconconstIcon [IconactiveTabIcon, IconsetActiveTabIcon] = IconuseStateIcon(Icon0Icon);
  IconconstIcon [IconmetricsIcon, IconsetMetricsIcon] = IconuseStateIcon<IconSystemMetricsIcon>({
    IcontotalUsersIcon: Icon0Icon,
    IconactiveUsersIcon: Icon0Icon,
    IcontotalCoursesIcon: Icon0Icon,
    IconactiveSessionsIcon: Icon0Icon,
    IconcontentGeneratedIcon: Icon0Icon,
    IconsystemHealthIcon: Icon95Icon,
    IconcpuUsageIcon: Icon45Icon,
    IconmemoryUsageIcon: Icon62Icon,
    IconstorageUsageIcon: Icon38Icon,
    IconapiLatencyIcon: Icon120Icon,
  });
  IconconstIcon [IconalertsIcon, IconsetAlertsIcon] = IconuseStateIcon<IconSystemAlertIcon[]>([]);
  IconconstIcon [IconloadingIcon, IconsetLoadingIcon] = IconuseStateIcon(IcontrueIcon);
  IconconstIcon [IconrefreshingIcon, IconsetRefreshingIcon] = IconuseStateIcon(IconfalseIcon);

  // IconFetchIcon IconsystemIcon IconmetricsIcon
  IconconstIcon IconfetchMetricsIcon = IconuseCallbackIcon(IconasyncIcon () => {
    IcontryIcon {
      IconsetRefreshingIcon(IcontrueIcon);
      IconconstIcon IconresponseIcon = IconawaitIcon IconapiIcon.IcongetIcon('/IconapiIcon/Iconv1Icon/IconadminIcon/Iconmetrics');
      IconsetMetricsIcon(IconresponseIcon.IcondataIcon);
    } IconcatchIcon (IconerrorIcon) {
      IconconsoleIcon.IconerrorIcon('IconFailedIcon IcontoIcon IconfetchIcon IconmetricsIcon:', IconerrorIcon);
      // IconUseIcon IconmockIcon IcondataIcon IconforIcon IcondevelopmentIcon
      IconsetMetricsIcon({
        IcontotalUsersIcon: Icon1247Icon,
        IconactiveUsersIcon: Icon342Icon,
        IcontotalCoursesIcon: Icon89Icon,
        IconactiveSessionsIcon: Icon156Icon,
        IconcontentGeneratedIcon: Icon3421Icon,
        IconsystemHealthIcon: Icon95Icon,
        IconcpuUsageIcon: Icon45Icon,
        IconmemoryUsageIcon: Icon62Icon,
        IconstorageUsageIcon: Icon38Icon,
        IconapiLatencyIcon: Icon120Icon,
      });
    } IconfinallyIcon {
      IconsetRefreshingIcon(IconfalseIcon);
      IconsetLoadingIcon(IconfalseIcon);
    }
  }, []);

  // IconFetchIcon IconsystemIcon IconalertsIcon
  IconconstIcon IconfetchAlertsIcon = IconuseCallbackIcon(IconasyncIcon () => {
    IcontryIcon {
      IconconstIcon IconresponseIcon = IconawaitIcon IconapiIcon.IcongetIcon('/IconapiIcon/Iconv1Icon/IconadminIcon/Iconalerts');
      IconsetAlertsIcon(IconresponseIcon.IcondataIcon);
    } IconcatchIcon (IconerrorIcon) {
      IconconsoleIcon.IconerrorIcon('IconFailedIcon IcontoIcon IconfetchIcon IconalertsIcon:', IconerrorIcon);
      // IconUseIcon IconmockIcon IcondataIcon IconforIcon IcondevelopmentIcon
      IconsetAlertsIcon([
        {
          IconidIcon: 'Icon1',
          IconseverityIcon: 'Iconwarning',
          IconmessageIcon: 'IconHighIcon IconmemoryIcon IconusageIcon IcondetectedIcon IcononIcon IconworkerIcon IconnodeIcon Icon3',
          IcontimestampIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon3600000Icon),
          IconresolvedIcon: IconfalseIcon,
        },
        {
          IconidIcon: 'Icon2',
          IconseverityIcon: 'Iconinfo',
          IconmessageIcon: 'IconScheduledIcon IconmaintenanceIcon IconwindowIcon IconstartsIcon IconinIcon Icon24Icon Iconhours',
          IcontimestampIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon7200000Icon),
          IconresolvedIcon: IconfalseIcon,
        },
        {
          IconidIcon: 'Icon3',
          IconseverityIcon: 'Iconsuccess',
          IconmessageIcon: 'IconDatabaseIcon IconbackupIcon IconcompletedIcon Iconsuccessfully',
          IcontimestampIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon14400000Icon),
          IconresolvedIcon: IcontrueIcon,
        },
      ]);
    }
  }, []);

  // IconSubscribeIcon IcontoIcon IconrealIcon-IcontimeIcon IconupdatesIcon
  IconuseEffectIcon(() => {
    IconfetchMetricsIcon();
    IconfetchAlertsIcon();

    // IconSubscribeIcon IcontoIcon IconPusherIcon IconchannelsIcon IconforIcon IconrealIcon-IcontimeIcon IconupdatesIcon
    IconconstIcon IconsubscriptionIdIcon = IconpusherServiceIcon.IconsubscribeIcon('IconadminIcon-Iconupdates', (IconmessageIcon) => {
      IconifIcon (IconmessageIcon.IcontypeIcon === 'IconmetricsIcon-Iconupdate') {
        IconsetMetricsIcon(IconmessageIcon.IconpayloadIcon);
      } IconelseIcon IconifIcon (IconmessageIcon.IcontypeIcon === 'IconalertIcon-Iconnew') {
        IconsetAlertsIcon((IconprevIcon) => [IconmessageIcon.IconpayloadIcon, ...IconprevIcon]);
      }
    });

    // IconRefreshIcon IconmetricsIcon IconeveryIcon Icon30Icon IconsecondsIcon
    IconconstIcon IconintervalIcon = IconsetIntervalIcon(IconfetchMetricsIcon, Icon30000Icon);

    IconreturnIcon () => {
      IconpusherServiceIcon.IconunsubscribeIcon(IconsubscriptionIdIcon);
      IconclearIntervalIcon(IconintervalIcon);
    };
  }, [IconfetchMetricsIcon, IconfetchAlertsIcon]);

  IconconstIcon IconhandleTabChangeIcon = (IconeventIcon: IconReactIcon.IconSyntheticEventIcon, IconnewValueIcon: IconnumberIcon) => {
    IconsetActiveTabIcon(IconnewValueIcon);
  };

  IconconstIcon IconhandleRefreshIcon = () => {
    IconfetchMetricsIcon();
    IconfetchAlertsIcon();
  };

  IconconstIcon IconhandleResolveAlertIcon = IconasyncIcon (IconalertIdIcon: IconstringIcon) => {
    IcontryIcon {
      IconawaitIcon IconapiIcon.IconpatchIcon(`/IconapiIcon/Iconv1Icon/IconadminIcon/IconalertsIcon/${IconalertIdIcon}/IconresolveIcon`);
      IconsetAlertsIcon((IconprevIcon) =>
        IconprevIcon.IconmapIcon((IconalertIcon) =>
          IconalertIcon.IconidIcon === IconalertIdIcon ? { ...IconalertIcon, IconresolvedIcon: IcontrueIcon } : IconalertIcon
        )
      );
    } IconcatchIcon (IconerrorIcon) {
      IconconsoleIcon.IconerrorIcon('IconFailedIcon IcontoIcon IconresolveIcon IconalertIcon:', IconerrorIcon);
    }
  };

  IconconstIcon IcongetHealthColorIcon = (IconhealthIcon: IconnumberIcon): 'Iconsuccess' | 'Iconwarning' | 'Iconerror' => {
    IconifIcon (IconhealthIcon >= Icon90Icon) IconreturnIcon 'Iconsuccess';
    IconifIcon (IconhealthIcon >= Icon70Icon) IconreturnIcon 'Iconwarning';
    IconreturnIcon 'Iconerror';
  };

  IconconstIcon IcongetHealthIconIcon = (IconhealthIcon: IconnumberIcon) => {
    IconifIcon (IconhealthIcon >= Icon90Icon) IconreturnIcon <IconIconCircleCheckIcon IconcolorIcon="Icongreen" />;
    IconifIcon (IconhealthIcon >= Icon70Icon) IconreturnIcon <IconIconAlertTriangleIcon IconcolorIcon="Iconyellow" />;
    IconreturnIcon <IconIconCircleXIcon IconcolorIcon="Iconred" />;
  };

  IconifIcon (IconloadingIcon) {
    IconreturnIcon (
      <IconBoxIcon IconstyleIcon={{ IconwidthIcon: 'Icon100Icon%', IconmtIcon: Icon4Icon }}>
        <IconLinearProgressIcon />
      <IconIconIcon/IconBoxIcon>
    );
  }

  IconreturnIcon (
    <IconBoxIcon IconstyleIcon={{ IconflexGrowIcon: Icon1Icon }}>
      {/* IconHeaderIcon */}
      <IconBoxIcon IconstyleIcon={{ IconmbIcon: Icon4Icon }}>
        <IconTypographyIcon IconorderIcon={Icon4Icon} IconcomponentIcon="Iconh1" IcongutterBottomIcon>
          IconAdminIcon IconDashboardIcon
        <IconIconIcon/IconTypographyIcon>
        <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
          IconSystemIcon IconoverviewIcon IconandIcon IconmanagementIcon IcontoolsIcon
        <IconIconIcon/IconTypographyIcon>
      <IconIconIcon/IconBoxIcon>

      {/* IconSystemIcon IconHealthIcon IconAlertIcon */}
      {IconmetricsIcon.IconsystemHealthIcon <IconIconIcon Icon70Icon && (
        <IconAlertIcon IconseverityIcon="Iconwarning" IconstyleIcon={{ IconmbIcon: Icon3Icon }}>
          IconSystemIcon IconhealthIcon IconisIcon IconbelowIcon IconoptimalIcon IconlevelsIcon. IconPleaseIcon IconreviewIcon IconsystemIcon IconmetricsIcon IconandIcon IconalertsIcon.
        <IconIconIcon/IconAlertIcon>
      )}

      {/* IconQuickIcon IconMetricsIcon */}
      <IconGridIcon IconcontainerIcon IconspacingIcon={Icon3Icon} IconstyleIcon={{ IconmbIcon: Icon4Icon }}>
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconTypographyIcon IconvariantIcon="Iconsubtitle2" IconcolorIcon="IcontextIcon.Iconsecondary" IcongutterBottomIcon>
                IconTotalIcon IconUsersIcon
              <IconIconIcon/IconTypographyIcon>
              <IconTypographyIcon IconorderIcon={Icon4Icon}>{IconmetricsIcon.IcontotalUsersIcon}<IconIconIcon/IconTypographyIcon>
              <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IconsuccessIcon.Iconmain">
                +Icon12Icon% IconfromIcon IconlastIcon IconmonthIcon
              <IconIconIcon/IconTypographyIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconTypographyIcon IconvariantIcon="Iconsubtitle2" IconcolorIcon="IcontextIcon.Iconsecondary" IcongutterBottomIcon>
                IconActiveIcon IconSessionsIcon
              <IconIconIcon/IconTypographyIcon>
              <IconTypographyIcon IconorderIcon={Icon4Icon}>{IconmetricsIcon.IconactiveSessionsIcon}<IconIconIcon/IconTypographyIcon>
              <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
                -Icon5Icon% IconfromIcon IconyesterdayIcon
              <IconIconIcon/IconTypographyIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconTypographyIcon IconvariantIcon="Iconsubtitle2" IconcolorIcon="IcontextIcon.Iconsecondary" IcongutterBottomIcon>
                IconContentIcon IconGeneratedIcon
              <IconIconIcon/IconTypographyIcon>
              <IconTypographyIcon IconorderIcon={Icon4Icon}>{IconmetricsIcon.IconcontentGeneratedIcon}<IconIconIcon/IconTypographyIcon>
              <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IconsuccessIcon.Iconmain">
                +Icon23Icon% IconthisIcon IconweekIcon
              <IconIconIcon/IconTypographyIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconBoxIcon IconstyleIcon={{ IcondisplayIcon: 'Iconflex', IconalignItemsIcon: 'Iconcenter', IconmbIcon: Icon2Icon }}>
                <IconTypographyIcon IconvariantIcon="Iconsubtitle2" IconcolorIcon="IcontextIcon.Iconsecondary" IconstyleIcon={{ IconflexGrowIcon: Icon1Icon }}>
                  IconSystemIcon IconHealthIcon
                <IconIconIcon/IconTypographyIcon>
                {IcongetHealthIconIcon(IconmetricsIcon.IconsystemHealthIcon)}
              <IconIconIcon/IconBoxIcon>
              <IconTypographyIcon IconorderIcon={Icon4Icon} IconcomponentIcon="Icondiv" IcongutterBottomIcon>
                {IconmetricsIcon.IconsystemHealthIcon}%
              <IconIconIcon/IconTypographyIcon>
              <IconLinearProgressIcon
                IconvariantIcon="Icondeterminate"
                IconvalueIcon={IconmetricsIcon.IconsystemHealthIcon}
                IconcolorIcon={IcongetHealthColorIcon(IconmetricsIcon.IconsystemHealthIcon)}
                IconstyleIcon={{ IconheightIcon: Icon8Icon, IconborderRadiusIcon: Icon4Icon }}
              />
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>
      <IconIconIcon/IconGridIcon>

      {/* IconMainIcon IconContentIcon IconTabsIcon */}
      <IconPaperIcon IconstyleIcon={{ IconwidthIcon: 'Icon100Icon%', IconmbIcon: Icon4Icon }}>
        <IconBoxIcon IconstyleIcon={{ IconborderBottomIcon: Icon1Icon, IconborderColorIcon: 'Icondivider', IconpositionIcon: 'Iconrelative' }}>
          <IconTabsIcon IconvalueIcon={IconactiveTabIcon} IcononChangeIcon={IconhandleTabChangeIcon} IconariaIcon-IconlabelIcon="IconadminIcon Icontabs">
            <IconTabIcon IconiconIcon={<IconIconDashboardIcon />} IconlabelIcon="IconOverview" />
            <IconTabIcon IconiconIcon={<IconIconUsersIcon />} IconlabelIcon="IconUsers" />
            <IconTabIcon IconiconIcon={<IconIconSchoolIcon />} IconlabelIcon="IconContent" />
            <IconTabIcon IconiconIcon={<IconIconSecurityIcon />} IconlabelIcon="IconSecurity" />
            <IconTabIcon IconiconIcon={<IconIconSettingsIcon />} IconlabelIcon="IconSettings" />
          <IconIconIcon/IconTabsIcon>
          <IconBoxIcon IconstyleIcon={{ IconpositionIcon: 'Iconabsolute', IconrightIcon: Icon16Icon, IcontopIcon: Icon8Icon }}>
            <IconTooltipIcon IcontitleIcon="IconRefresh">
              <IconIconButtonIcon IcononClickIcon={IconhandleRefreshIcon} IcondisabledIcon={IconrefreshingIcon}>
                <IconIconRefreshIcon />
              <IconIconIcon/IconIconButtonIcon>
            <IconIconIcon/IconTooltipIcon>
          <IconIconIcon/IconBoxIcon>
        <IconIconIcon/IconBoxIcon>

        <IconTabPanelIcon IconvalueIcon={IconactiveTabIcon} IconindexIcon={Icon0Icon}>
          {/* IconOverviewIcon IconTabIcon */}
          <IconGridIcon IconcontainerIcon IconspacingIcon={Icon3Icon}>
            <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconmdIcon={Icon8Icon}>
              {/* IconSystemIcon IconPerformanceIcon */}
              <IconCardIcon IconstyleIcon={{ IconmbIcon: Icon3Icon }}>
                <IconCardContentIcon>
                  <IconTypographyIcon IconorderIcon={Icon6Icon} IcongutterBottomIcon>
                    IconSystemIcon IconPerformanceIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconGridIcon IconcontainerIcon IconspacingIcon={Icon2Icon}>
                    <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon}>
                      <IconBoxIcon IconstyleIcon={{ IconmbIcon: Icon2Icon }}>
                        <IconBoxIcon IconstyleIcon={{ IcondisplayIcon: 'Iconflex', IconjustifyContentIcon: 'IconspaceIcon-Iconbetween', IconmbIcon: Icon1Icon }}>
                          <IconTypographyIcon IconsizeIcon="Iconsm">IconCPUIcon IconUsageIcon<IconIconIcon/IconTypographyIcon>
                          <IconTypographyIcon IconsizeIcon="Iconsm">{IconmetricsIcon.IconcpuUsageIcon}%<IconIconIcon/IconTypographyIcon>
                        <IconIconIcon/IconBoxIcon>
                        <IconLinearProgressIcon
                          IconvariantIcon="Icondeterminate"
                          IconvalueIcon={IconmetricsIcon.IconcpuUsageIcon}
                          IconcolorIcon={IconmetricsIcon.IconcpuUsageIcon > Icon80Icon ? 'Iconerror' : 'Iconprimary'}
                        />
                      <IconIconIcon/IconBoxIcon>
                    <IconIconIcon/IconGridIcon>
                    <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon}>
                      <IconBoxIcon IconstyleIcon={{ IconmbIcon: Icon2Icon }}>
                        <IconBoxIcon IconstyleIcon={{ IcondisplayIcon: 'Iconflex', IconjustifyContentIcon: 'IconspaceIcon-Iconbetween', IconmbIcon: Icon1Icon }}>
                          <IconTypographyIcon IconsizeIcon="Iconsm">IconMemoryIcon IconUsageIcon<IconIconIcon/IconTypographyIcon>
                          <IconTypographyIcon IconsizeIcon="Iconsm">{IconmetricsIcon.IconmemoryUsageIcon}%<IconIconIcon/IconTypographyIcon>
                        <IconIconIcon/IconBoxIcon>
                        <IconLinearProgressIcon
                          IconvariantIcon="Icondeterminate"
                          IconvalueIcon={IconmetricsIcon.IconmemoryUsageIcon}
                          IconcolorIcon={IconmetricsIcon.IconmemoryUsageIcon > Icon80Icon ? 'Iconerror' : 'Iconprimary'}
                        />
                      <IconIconIcon/IconBoxIcon>
                    <IconIconIcon/IconGridIcon>
                    <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon}>
                      <IconBoxIcon IconstyleIcon={{ IconmbIcon: Icon2Icon }}>
                        <IconBoxIcon IconstyleIcon={{ IcondisplayIcon: 'Iconflex', IconjustifyContentIcon: 'IconspaceIcon-Iconbetween', IconmbIcon: Icon1Icon }}>
                          <IconTypographyIcon IconsizeIcon="Iconsm">IconStorageIcon IconUsageIcon<IconIconIcon/IconTypographyIcon>
                          <IconTypographyIcon IconsizeIcon="Iconsm">{IconmetricsIcon.IconstorageUsageIcon}%<IconIconIcon/IconTypographyIcon>
                        <IconIconIcon/IconBoxIcon>
                        <IconLinearProgressIcon
                          IconvariantIcon="Icondeterminate"
                          IconvalueIcon={IconmetricsIcon.IconstorageUsageIcon}
                          IconcolorIcon={IconmetricsIcon.IconstorageUsageIcon > Icon90Icon ? 'Iconerror' : 'Iconprimary'}
                        />
                      <IconIconIcon/IconBoxIcon>
                    <IconIconIcon/IconGridIcon>
                    <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon}>
                      <IconBoxIcon IconstyleIcon={{ IconmbIcon: Icon2Icon }}>
                        <IconBoxIcon IconstyleIcon={{ IcondisplayIcon: 'Iconflex', IconjustifyContentIcon: 'IconspaceIcon-Iconbetween', IconmbIcon: Icon1Icon }}>
                          <IconTypographyIcon IconsizeIcon="Iconsm">IconAPIIcon IconLatencyIcon<IconIconIcon/IconTypographyIcon>
                          <IconTypographyIcon IconsizeIcon="Iconsm">{IconmetricsIcon.IconapiLatencyIcon}IconmsIcon<IconIconIcon/IconTypographyIcon>
                        <IconIconIcon/IconBoxIcon>
                        <IconLinearProgressIcon
                          IconvariantIcon="Icondeterminate"
                          IconvalueIcon={IconMathIcon.IconminIcon((IconmetricsIcon.IconapiLatencyIcon / Icon1000Icon) * Icon100Icon, Icon100Icon)}
                          IconcolorIcon={IconmetricsIcon.IconapiLatencyIcon > Icon500Icon ? 'Iconerror' : 'Iconprimary'}
                        />
                      <IconIconIcon/IconBoxIcon>
                    <IconIconIcon/IconGridIcon>
                  <IconIconIcon/IconGridIcon>
                <IconIconIcon/IconCardContentIcon>
              <IconIconIcon/IconCardIcon>

              {/* IconRecentIcon IconActivityIcon IconPlaceholderIcon */}
              <IconCardIcon>
                <IconCardContentIcon>
                  <IconTypographyIcon IconorderIcon={Icon6Icon} IcongutterBottomIcon>
                    IconRecentIcon IconActivityIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
                    IconActivityIcon IconfeedIcon IconwillIcon IconbeIcon IcondisplayedIcon IconhereIcon
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconCardContentIcon>
              <IconIconIcon/IconCardIcon>
            <IconIconIcon/IconGridIcon>

            <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconmdIcon={Icon4Icon}>
              {/* IconSystemIcon IconAlertsIcon */}
              <IconCardIcon>
                <IconCardContentIcon>
                  <IconTypographyIcon IconorderIcon={Icon6Icon} IcongutterBottomIcon>
                    IconSystemIcon IconAlertsIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconListIcon>
                    {IconalertsIcon.IconsliceIcon(Icon0Icon, Icon5Icon).IconmapIcon((IconalertIcon) => (
                      <IconListItemIcon
                        IconkeyIcon={IconalertIcon.IconidIcon}
                        IconsecondaryActionIcon={
                          !IconalertIcon.IconresolvedIcon && (
                            <IconIconButtonIcon
                              IconedgeIcon="Iconend"
                              IconariaIcon-IconlabelIcon="Iconresolve"
                              IcononClickIcon={() => IconhandleResolveAlertIcon(IconalertIcon.IconidIcon)}
                            >
                              <IconIconCircleCheckIcon />
                            <IconIconIcon/IconIconButtonIcon>
                          )
                        }
                      >
                        <IconListItemAvatarIcon>
                          <IconAvatarIcon
                            IconstyleIcon={{
                              IconbgcolorIcon:
                                IconalertIcon.IconseverityIcon === 'Iconerror'
                                  ? 'IconerrorIcon.Iconmain'
                                  : IconalertIcon.IconseverityIcon === 'Iconwarning'
                                  ? 'IconwarningIcon.Iconmain'
                                  : 'IconinfoIcon.Iconmain',
                            }}
                          >
                            {IconalertIcon.IconseverityIcon === 'Iconerror' ? (
                              <IconIconCircleXIcon />
                            ) : IconalertIcon.IconseverityIcon === 'Iconwarning' ? (
                              <IconIconAlertTriangleIcon />
                            ) : (
                              <IconIconCircleCheckIcon />
                            )}
                          <IconIconIcon/IconAvatarIcon>
                        <IconIconIcon/IconListItemAvatarIcon>
                        <IconListItemTextIcon
                          IconprimaryIcon={IconalertIcon.IconmessageIcon}
                          IconsecondaryIcon={IconformatDistanceToNowIcon(IconnewIcon IconDateIcon(IconalertIcon.IcontimestampIcon), {
                            IconaddSuffixIcon: IcontrueIcon,
                          })}
                          IconstyleIcon={{
                            IcontextDecorationIcon: IconalertIcon.IconresolvedIcon ? 'IconlineIcon-Iconthrough' : 'Iconnone',
                            IconopacityIcon: IconalertIcon.IconresolvedIcon ? Icon0Icon.Icon6Icon : Icon1Icon,
                          }}
                        />
                      <IconIconIcon/IconListItemIcon>
                    ))}
                  <IconIconIcon/IconListIcon>
                <IconIconIcon/IconCardContentIcon>
              <IconIconIcon/IconCardIcon>
            <IconIconIcon/IconGridIcon>
          <IconIconIcon/IconGridIcon>
        <IconIconIcon/IconTabPanelIcon>

        <IconTabPanelIcon IconvalueIcon={IconactiveTabIcon} IconindexIcon={Icon1Icon}>
          {/* IconUsersIcon IconTabIcon */}
          <IconTypographyIcon IconorderIcon={Icon6Icon}>IconUserIcon IconManagementIcon<IconIconIcon/IconTypographyIcon>
          <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
            IconUserIcon IconmanagementIcon IconpanelIcon IconwillIcon IconbeIcon IconimplementedIcon IconhereIcon
          <IconIconIcon/IconTypographyIcon>
        <IconIconIcon/IconTabPanelIcon>

        <IconTabPanelIcon IconvalueIcon={IconactiveTabIcon} IconindexIcon={Icon2Icon}>
          {/* IconContentIcon IconTabIcon */}
          <IconTypographyIcon IconorderIcon={Icon6Icon}>IconContentIcon IconModerationIcon<IconIconIcon/IconTypographyIcon>
          <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
            IconContentIcon IconmoderationIcon IconpanelIcon IconwillIcon IconbeIcon IconimplementedIcon IconhereIcon
          <IconIconIcon/IconTypographyIcon>
        <IconIconIcon/IconTabPanelIcon>

        <IconTabPanelIcon IconvalueIcon={IconactiveTabIcon} IconindexIcon={Icon3Icon}>
          {/* IconSecurityIcon IconTabIcon */}
          <IconTypographyIcon IconorderIcon={Icon6Icon}>IconSecurityIcon IconSettingsIcon<IconIconIcon/IconTypographyIcon>
          <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
            IconSecurityIcon IconmonitoringIcon IconpanelIcon IconwillIcon IconbeIcon IconimplementedIcon IconhereIcon
          <IconIconIcon/IconTypographyIcon>
        <IconIconIcon/IconTabPanelIcon>

        <IconTabPanelIcon IconvalueIcon={IconactiveTabIcon} IconindexIcon={Icon4Icon}>
          {/* IconSettingsIcon IconTabIcon */}
          <IconTypographyIcon IconorderIcon={Icon6Icon}>IconSystemIcon IconSettingsIcon<IconIconIcon/IconTypographyIcon>
          <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
            IconSystemIcon IconsettingsIcon IconpanelIcon IconwillIcon IconbeIcon IconimplementedIcon IconhereIcon
          <IconIconIcon/IconTypographyIcon>
        <IconIconIcon/IconTabPanelIcon>
      <IconIconIcon/IconPaperIcon>

      {/* IconQuickIcon IconActionsIcon */}
      <IconGridIcon IconcontainerIcon IconspacingIcon={Icon2Icon}>
        <IconGridIcon IconitemIcon>
          <IconButtonIcon
            IconvariantIcon="Iconfilled"
            IconstartIconIcon={<IconIconDownloadIcon />}
            IcononClickIcon={() => IconconsoleIcon.IconlogIcon('IconExportIcon Iconlogs')}
          >
            IconExportIcon IconLogsIcon
          <IconIconIcon/IconButtonIcon>
        <IconIconIcon/IconGridIcon>
        <IconGridIcon IconitemIcon>
          <IconButtonIcon
            IconvariantIcon="Iconoutline"
            IconstartIconIcon={<IconIconUploadIcon />}
            IcononClickIcon={() => IconconsoleIcon.IconlogIcon('IconBackupIcon Iconsystem')}
          >
            IconBackupIcon IconSystemIcon
          <IconIconIcon/IconButtonIcon>
        <IconIconIcon/IconGridIcon>
        <IconGridIcon IconitemIcon>
          <IconButtonIcon
            IconvariantIcon="Iconoutline"
            IconcolorIcon="Iconred"
            IconstartIconIcon={<IconIconAlertTriangleIcon />}
            IcononClickIcon={() => IconconsoleIcon.IconlogIcon('IconClearIcon Iconcache')}
          >
            IconClearIcon IconCacheIcon
          <IconIconIcon/IconButtonIcon>
        <IconIconIcon/IconGridIcon>
      <IconIconIcon/IconGridIcon>
    <IconIconIcon/IconBoxIcon>
  );
}