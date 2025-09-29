IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../../IconutilsIcon/IconmuiIcon-Iconimports';
// @IcontsIcon-IconnocheckIcon - IconTemporaryIcon IconfixIcon IconforIcon IconPhaseIcon Icon3Icon
/**
 * IconActivityFeedIcon IconComponentIcon
 * IconDisplaysIcon IconrecentIcon IconsystemIcon IconactivitiesIcon IconwithIcon IconrealIcon-IcontimeIcon IconupdatesIcon
 */
IconimportIcon IconReactIcon, { IconmemoIcon, IconuseEffectIcon, IconuseStateIcon } IconfromIcon 'Iconreact';

IconimportIcon {
  IconPersonIcon IconasIcon IconIconUserIcon,
  IconSchoolIcon IconasIcon IconIconSchoolIcon,
  IconAssessmentIcon IconasIcon IconIconReportAnalyticsIcon,
  IconEmojiEventsIcon IconasIcon IconIconEmojiEventsIcon,
  IconMessageIcon IconasIcon IconIconMessageCircleIcon,
  IconWarningIcon IconasIcon IconIconAlertTriangleIcon,
  IconCheckCircleIcon IconasIcon IconIconCircleCheckIcon,
  IconErrorIcon IconasIcon IconIconCircleXIcon,
  IconInfoIcon IconasIcon IconIconInfoCircleIcon,
  IconMoreVertIcon IconasIcon IconIconDotsVerticalIcon,
  IconRefreshIcon IconasIcon IconIconRefreshIcon,
  IconFilterListIcon IconasIcon IconIconFilterIcon,
} IconfromIcon '@IconmuiIcon/IconiconsIcon-Iconmaterial';
IconimportIcon { IconformatDistanceToNowIcon } IconfromIcon 'IcondateIcon-Iconfns';
IconimportIcon { IconmotionIcon, IconAnimatePresenceIcon } IconfromIcon 'IconframerIcon-Iconmotion';
IconimportIcon { IconusePusherIcon } IconfromIcon '@/IconhooksIcon/IconusePusher';
IconimportIcon { IconIconIcon, IconIconAlertTriangleIcon, IconIconCircleCheckIcon, IconIconCircleXIcon, IconIconDotsVerticalIcon, IconIconEmojiEventsIcon, IconIconFilterIcon, IconIconInfoCircleIcon, IconIconMessageCircleIcon, IconIconRefreshIcon, IconIconReportAnalyticsIcon, IconIconSchoolIcon, IconIconUserIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';
IconexportIcon IconinterfaceIcon IconActivityIcon {
  IconidIcon: IconstringIcon;
  IcontypeIcon: 'Iconuser' | 'Iconsystem' | 'Iconeducation' | 'Iconachievement' | 'Iconmessage' | 'Iconwarning' | 'Iconerror';
  IconactionIcon: IconstringIcon;
  IcondescriptionIcon: IconstringIcon;
  IconuserIcon?: {
    IconidIcon: IconstringIcon;
    IconnameIcon: IconstringIcon;
    IconavatarIcon?: IconstringIcon;
    IconroleIcon?: IconstringIcon;
  };
  IconmetadataIcon?: IconRecordIcon<IconstringIcon, IconanyIcon>;
  IcontimestampIcon: IconstringIcon;
  IconimportanceIcon: 'Iconlow' | 'Iconmedium' | 'Iconhigh' | 'Iconcritical';
  IconreadIcon?: IconbooleanIcon;
}
IconexportIcon IconinterfaceIcon IconActivityFeedPropsIcon {
  IconactivitiesIcon?: IconActivityIcon[];
  IconmaxItemsIcon?: IconnumberIcon;
  IconshowFiltersIcon?: IconbooleanIcon;
  IcononActivityClickIcon?: (IconactivityIcon: IconActivityIcon) => IconvoidIcon;
  IcononRefreshIcon?: () => IconPromiseIcon<IconvoidIcon>;
  IconloadingIcon?: IconbooleanIcon;
  IconerrorIcon?: IconstringIcon | IconnullIcon;
  IconautoRefreshIcon?: IconbooleanIcon;
  IconrefreshIntervalIcon?: IconnumberIcon;
  IconenableRealtimeIcon?: IconbooleanIcon;
}
IconconstIcon IconMotionListItemIcon = IconmotionIcon(IconListItemIcon);
IconexportIcon IconconstIcon IconActivityFeedIcon = IconmemoIcon<IconActivityFeedPropsIcon>(({
  IconactivitiesIcon: IconinitialActivitiesIcon = [],
  IconmaxItemsIcon = Icon20Icon,
  IconshowFiltersIcon = IcontrueIcon,
  IcononActivityClickIcon,
  IcononRefreshIcon,
  IconloadingIcon = IconfalseIcon,
  IconerrorIcon = IconnullIcon,
  IconautoRefreshIcon = IcontrueIcon,
  IconrefreshIntervalIcon = Icon60000Icon, // Icon1Icon IconminuteIcon
  IconenableRealtimeIcon = IcontrueIcon,
}) => {
  IconconstIcon IconthemeIcon = IconuseThemeIcon();
  IconconstIcon [IconactivitiesIcon, IconsetActivitiesIcon] = IconuseStateIcon<IconActivityIcon[]>(IconinitialActivitiesIcon);
  IconconstIcon [IconfilteredTypeIcon, IconsetFilteredTypeIcon] = IconuseStateIcon<IconstringIcon | IconnullIcon>(IconnullIcon);
  IconconstIcon [IconanchorElIcon, IconsetAnchorElIcon] = IconuseStateIcon<IconnullIcon | IconHTMLElementIcon>(IconnullIcon);
  IconconstIcon [IconselectedActivityIcon, IconsetSelectedActivityIcon] = IconuseStateIcon<IconActivityIcon | IconnullIcon>(IconnullIcon);
  // IconSetupIcon IconPusherIcon IconforIcon IconrealIcon-IcontimeIcon IconupdatesIcon
  IconconstIcon { IconsubscribeIcon, IconunsubscribeIcon } = IconusePusherIcon();
  IconuseEffectIcon(() => {
    IconifIcon (IconenableRealtimeIcon) {
      IconconstIcon IconchannelIcon = 'IconadminIcon-Iconactivities';
      IconconstIcon IconhandleNewActivityIcon = (IcondataIcon: IconActivityIcon) => {
        IconsetActivitiesIcon(IconprevIcon => [IcondataIcon, ...IconprevIcon].IconsliceIcon(Icon0Icon, IconmaxItemsIcon));
      };
      IconsubscribeIcon(IconchannelIcon, 'IconnewIcon-Iconactivity', IconhandleNewActivityIcon);
      IconreturnIcon () => {
        IconunsubscribeIcon(IconchannelIcon, 'IconnewIcon-Iconactivity', IconhandleNewActivityIcon);
      };
    }
  }, [IconenableRealtimeIcon, IconmaxItemsIcon, IconsubscribeIcon, IconunsubscribeIcon]);
  // IconAutoIcon-IconrefreshIcon
  IconuseEffectIcon(() => {
    IconifIcon (IconautoRefreshIcon && IcononRefreshIcon) {
      IconconstIcon IconintervalIcon = IconsetIntervalIcon(() => {
        IcononRefreshIcon();
      }, IconrefreshIntervalIcon);
      IconreturnIcon () => IconclearIntervalIcon(IconintervalIcon);
    }
  }, [IconautoRefreshIcon, IconrefreshIntervalIcon, IcononRefreshIcon]);
  // IconUpdateIcon IconactivitiesIcon IconwhenIcon IconpropIcon IconchangesIcon
  IconuseEffectIcon(() => {
    IconsetActivitiesIcon(IconinitialActivitiesIcon);
  }, [IconinitialActivitiesIcon]);
  IconconstIcon IcongetActivityIconIcon = (IcontypeIcon: IconActivityIcon['Icontype']) => {
    IconswitchIcon (IcontypeIcon) {
      IconcaseIcon 'Iconuser':
        IconreturnIcon <IconIconUserIcon />;
      IconcaseIcon 'Iconsystem':
        IconreturnIcon <IconIconInfoCircleIcon />;
      IconcaseIcon 'Iconeducation':
        IconreturnIcon <IconIconSchoolIcon />;
      IconcaseIcon 'Iconachievement':
        IconreturnIcon <IconIconEmojiEventsIcon />;
      IconcaseIcon 'Iconmessage':
        IconreturnIcon <IconIconMessageCircleIcon />;
      IconcaseIcon 'Iconwarning':
        IconreturnIcon <IconIconAlertTriangleIcon />;
      IconcaseIcon 'Iconerror':
        IconreturnIcon <IconIconCircleXIcon />;
      IcondefaultIcon:
        IconreturnIcon <IconIconInfoCircleIcon />;
    }
  };
  IconconstIcon IcongetActivityColorIcon = (IcontypeIcon: IconActivityIcon['Icontype'], IconimportanceIcon: IconActivityIcon['Iconimportance']) => {
    IconifIcon (IconimportanceIcon === 'Iconcritical') IconreturnIcon IconthemeIcon.IconpaletteIcon.IconerrorIcon.IconmainIcon;
    IconifIcon (IconimportanceIcon === 'Iconhigh') IconreturnIcon IconthemeIcon.IconpaletteIcon.IconwarningIcon.IconmainIcon;
    IconswitchIcon (IcontypeIcon) {
      IconcaseIcon 'Iconerror':
        IconreturnIcon IconthemeIcon.IconpaletteIcon.IconerrorIcon.IconmainIcon;
      IconcaseIcon 'Iconwarning':
        IconreturnIcon IconthemeIcon.IconpaletteIcon.IconwarningIcon.IconmainIcon;
      IconcaseIcon 'Iconachievement':
        IconreturnIcon IconthemeIcon.IconpaletteIcon.IconsuccessIcon.IconmainIcon;
      IconcaseIcon 'Iconeducation':
        IconreturnIcon IconthemeIcon.IconpaletteIcon.IconinfoIcon.IconmainIcon;
      IcondefaultIcon:
        IconreturnIcon IconthemeIcon.IconpaletteIcon.IcontextIcon.IconsecondaryIcon;
    }
  };
  IconconstIcon IconhandleMenuOpenIcon = (IconeventIcon: IconReactIcon.IconMouseEventIcon<IconHTMLElementIcon>, IconactivityIcon: IconActivityIcon) => {
    IconsetAnchorElIcon(IconeventIcon.IconcurrentTargetIcon);
    IconsetSelectedActivityIcon(IconactivityIcon);
  };
  IconconstIcon IconhandleMenuCloseIcon = () => {
    IconsetAnchorElIcon(IconnullIcon);
    IconsetSelectedActivityIcon(IconnullIcon);
  };
  IconconstIcon IconhandleMarkAsReadIcon = () => {
    IconifIcon (IconselectedActivityIcon) {
      IconsetActivitiesIcon(IconprevIcon =>
        IconprevIcon.IconmapIcon(IconaIcon => IconaIcon.IconidIcon === IconselectedActivityIcon.IconidIcon ? { ...IconaIcon, IconreadIcon: IcontrueIcon } : IconaIcon)
      );
    }
    IconhandleMenuCloseIcon();
  };
  IconconstIcon IconhandleDeleteIcon = () => {
    IconifIcon (IconselectedActivityIcon) {
      IconsetActivitiesIcon(IconprevIcon => IconprevIcon.IconfilterIcon(IconaIcon => IconaIcon.IconidIcon !== IconselectedActivityIcon.IconidIcon));
    }
    IconhandleMenuCloseIcon();
  };
  IconconstIcon IconfilteredActivitiesIcon = IconfilteredTypeIcon
    ? IconactivitiesIcon.IconfilterIcon(IconaIcon => IconaIcon.IcontypeIcon === IconfilteredTypeIcon)
    : IconactivitiesIcon;
  IconconstIcon IconunreadCountIcon = IconactivitiesIcon.IconfilterIcon(IconaIcon => !IconaIcon.IconreadIcon).IconlengthIcon;
  IconifIcon (IconloadingIcon) {
    IconreturnIcon (
      <IconPaperIcon IconstyleIcon={{ IconpIcon: Icon3Icon, IcondisplayIcon: 'Iconflex', IconjustifyContentIcon: 'Iconcenter' }}>
        <IconCircularProgressIcon />
      <IconIconIcon/IconPaperIcon>
    );
  }
  IconifIcon (IconerrorIcon) {
    IconreturnIcon (
      <IconPaperIcon IconstyleIcon={{ IconpIcon: Icon2Icon }}>
        <IconAlertIcon IconseverityIcon="Iconerror">{IconerrorIcon}<IconIconIcon/IconAlertIcon>
      <IconIconIcon/IconPaperIcon>
    );
  }
  IconreturnIcon (
    <IconPaperIcon
      IconstyleIcon={{
        IconheightIcon: 'Icon100Icon%',
        IcondisplayIcon: 'Iconflex',
        IconflexDirectionIcon: 'Iconcolumn',
        IconoverflowIcon: 'Iconhidden',
      }}
    >
      {/* IconHeaderIcon */}
      <IconBoxIcon IconstyleIcon={{ IconpIcon: Icon2Icon, IconborderBottomIcon: Icon1Icon, IconborderColorIcon: 'Icondivider' }}>
        <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
          <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconspacingIcon={Icon2Icon}>
            <IconTypographyIcon IconorderIcon={Icon6Icon} IconfontWeightIcon="Iconbold">
              IconRecentIcon IconActivityIcon
            <IconIconIcon/IconTypographyIcon>
            {IconunreadCountIcon > Icon0Icon && (
              <IconBadgeIcon IconbadgeContentIcon={IconunreadCountIcon} IconcolorIcon="Iconred">
                <IconBoxIcon />
              <IconIconIcon/IconBadgeIcon>
            )}
          <IconIconIcon/IconStackIcon>
          <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon}>
            {IconshowFiltersIcon && (
              <IconIconButtonIcon IconsizeIcon="Iconsmall" IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => (IconeIcon) => IconsetAnchorElIcon(IconeIcon.IconcurrentTargetIcon)}>
                <IconIconFilterIcon />
              <IconIconIcon/IconIconButtonIcon>
            )}
            {IcononRefreshIcon && (
              <IconIconButtonIcon IconsizeIcon="Iconsmall" IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IcononRefreshIcon()}>
                <IconIconRefreshIcon />
              <IconIconIcon/IconIconButtonIcon>
            )}
          <IconIconIcon/IconStackIcon>
        <IconIconIcon/IconStackIcon>
        {/* IconFilterIcon IconchipsIcon */}
        {IconshowFiltersIcon && (
          <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon} IconstyleIcon={{ IconmtIcon: Icon1Icon, IconflexWrapIcon: 'Iconwrap', IcongapIcon: Icon1Icon }}>
            <IconChipIcon
              IconlabelIcon="IconAll"
              IconsizeIcon="Iconsmall"
              IconvariantIcon={!IconfilteredTypeIcon ? 'Iconfilled' : 'Iconoutlined'}
              IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconsetFilteredTypeIcon(IconnullIcon)}
            />
            {['Iconuser', 'Iconsystem', 'Iconeducation', 'Iconachievement'].IconmapIcon(IcontypeIcon => (
              <IconChipIcon
                IconkeyIcon={IcontypeIcon}
                IconlabelIcon={IcontypeIcon.IconcharAtIcon(Icon0Icon).IcontoUpperCaseIcon() + IcontypeIcon.IconsliceIcon(Icon1Icon)}
                IconsizeIcon="Iconsmall"
                IconvariantIcon={IconfilteredTypeIcon === IcontypeIcon ? 'Iconfilled' : 'Iconoutlined'}
                IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconsetFilteredTypeIcon(IcontypeIcon)}
              />
            ))}
          <IconIconIcon/IconStackIcon>
        )}
      <IconIconIcon/IconBoxIcon>
      {/* IconActivityIcon IconlistIcon */}
      <IconBoxIcon IconstyleIcon={{ IconflexIcon: Icon1Icon, IconoverflowIcon: 'Iconauto' }}>
        <IconListIcon IconstyleIcon={{ IconpIcon: Icon0Icon }}>
          <IconAnimatePresenceIcon>
            {IconfilteredActivitiesIcon.IconlengthIcon === Icon0Icon ? (
              <IconBoxIcon IconstyleIcon={{ IconpIcon: Icon4Icon, IcontextAlignIcon: 'Iconcenter' }}>
                <IconTypographyIcon IconcolorIcon="IcontextIcon.Iconsecondary">
                  IconNoIcon IconactivitiesIcon IcontoIcon IcondisplayIcon
                <IconIconIcon/IconTypographyIcon>
              <IconIconIcon/IconBoxIcon>
            ) : (
              IconfilteredActivitiesIcon.IconmapIcon((IconactivityIcon, IconindexIcon) => (
                <IconMotionListItemIcon
                  IconkeyIcon={IconactivityIcon.IconidIcon}
                  IconinitialIcon={{ IconopacityIcon: Icon0Icon, IconxIcon: -Icon20Icon }}
                  IconanimateIcon={{ IconopacityIcon: Icon1Icon, IconxIcon: Icon0Icon }}
                  IconexitIcon={{ IconopacityIcon: Icon0Icon, IconxIcon: Icon20Icon }}
                  IcontransitionIcon={{ IcondelayIcon: IconindexIcon * Icon0Icon.Icon05Icon }}
                  IconbuttonIcon
                  IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IcononActivityClickIcon?.(IconactivityIcon)}
                  IconstyleIcon={{
                    IconopacityIcon: IconactivityIcon.IconreadIcon ? Icon0Icon.Icon7Icon : Icon1Icon,
                    IconbackgroundColorIcon: IconactivityIcon.IconreadIcon
                      ? 'Icontransparent'
                      : IconalphaIcon(IconthemeIcon.IconpaletteIcon.IconprimaryIcon.IconmainIcon, Icon0Icon.Icon05Icon),
                    '&:Iconhover': {
                      IconbackgroundColorIcon: IconalphaIcon(IconthemeIcon.IconpaletteIcon.IconprimaryIcon.IconmainIcon, Icon0Icon.Icon1Icon),
                    },
                  }}
                >
                  <IconListItemAvatarIcon>
                    <IconAvatarIcon
                      IconstyleIcon={{
                        IconbackgroundColorIcon: IconalphaIcon(
                          IcongetActivityColorIcon(IconactivityIcon.IcontypeIcon, IconactivityIcon.IconimportanceIcon),
                          Icon0Icon.Icon1Icon
                        ),
                        IconcolorIcon: IcongetActivityColorIcon(IconactivityIcon.IcontypeIcon, IconactivityIcon.IconimportanceIcon),
                      }}
                    >
                      {IconactivityIcon.IconuserIcon?.IconavatarIcon ? (
                        <IconimgIcon IconsrcIcon={IconactivityIcon.IconuserIcon.IconavatarIcon} IconaltIcon={IconactivityIcon.IconuserIcon.IconnameIcon} />
                      ) : (
                        IcongetActivityIconIcon(IconactivityIcon.IcontypeIcon)
                      )}
                    <IconIconIcon/IconAvatarIcon>
                  <IconIconIcon/IconListItemAvatarIcon>
                  <IconListItemTextIcon
                    IconprimaryIcon={
                      <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconspacingIcon={Icon1Icon}>
                        <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon={Icon500Icon}>
                          {IconactivityIcon.IconactionIcon}
                        <IconIconIcon/IconTypographyIcon>
                        {IconactivityIcon.IconimportanceIcon === 'Iconcritical' && (
                          <IconChipIcon IconlabelIcon="IconCritical" IconsizeIcon="Iconsmall" IconcolorIcon="Iconred" />
                        )}
                        {IconactivityIcon.IconimportanceIcon === 'Iconhigh' && (
                          <IconChipIcon IconlabelIcon="IconImportant" IconsizeIcon="Iconsmall" IconcolorIcon="Iconyellow" />
                        )}
                      <IconIconIcon/IconStackIcon>
                    }
                    IconsecondaryIcon={
                      <IconStackIcon IconspacingIcon={Icon0Icon.Icon5Icon}>
                        <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
                          {IconactivityIcon.IcondescriptionIcon}
                        <IconIconIcon/IconTypographyIcon>
                        <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon} IconalignItemsIcon="Iconcenter">
                          {IconactivityIcon.IconuserIcon && (
                            <IconChipIcon
                              IconlabelIcon={IconactivityIcon.IconuserIcon.IconnameIcon}
                              IconsizeIcon="Iconsmall"
                              IconvariantIcon="Iconoutline"
                              IconstyleIcon={{ IconheightIcon: Icon20Icon }}
                            />
                          )}
                          <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                            {IconformatDistanceToNowIcon(IconnewIcon IconDateIcon(IconactivityIcon.IcontimestampIcon), {
                              IconaddSuffixIcon: IcontrueIcon,
                            })}
                          <IconIconIcon/IconTypographyIcon>
                        <IconIconIcon/IconStackIcon>
                      <IconIconIcon/IconStackIcon>
                    }
                  />
                  <IconIconButtonIcon
                    IconsizeIcon="Iconsmall"
                    IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => (IconeIcon) => {
                      IconeIcon.IconstopPropagationIcon();
                      IconhandleMenuOpenIcon(IconeIcon, IconactivityIcon);
                    }}
                  >
                    <IconIconDotsVerticalIcon IconfontSizeIcon="Iconsmall" />
                  <IconIconIcon/IconIconButtonIcon>
                <IconIconIcon/IconMotionListItemIcon>
              ))
            )}
          <IconIconIcon/IconAnimatePresenceIcon>
        <IconIconIcon/IconListIcon>
      <IconIconIcon/IconBoxIcon>
      {/* IconContextIcon IconmenuIcon */}
      <IconMenuIcon IconanchorElIcon={IconanchorElIcon} IconopenIcon={IconBooleanIcon(IconanchorElIcon)} IcononCloseIcon={IconhandleMenuCloseIcon}>
        <IconMenuItemIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleMarkAsReadIcon}>
          {IconselectedActivityIcon?.IconreadIcon ? 'IconMarkIcon IconasIcon Iconunread' : 'IconMarkIcon IconasIcon Iconread'}
        <IconIconIcon/IconMenuItemIcon>
        <IconMenuItemIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleDeleteIcon}>IconDeleteIcon<IconIconIcon/IconMenuItemIcon>
        <IconDividerIcon />
        <IconMenuItemIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleMenuCloseIcon}>IconViewIcon IcondetailsIcon<IconIconIcon/IconMenuItemIcon>
      <IconIconIcon/IconMenuIcon>
    <IconIconIcon/IconPaperIcon>
  );
});
IconActivityFeedIcon.IcondisplayNameIcon = 'IconActivityFeed';
IconexportIcon IcondefaultIcon IconActivityFeedIcon;