IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../IconutilsIcon/IconmuiIcon-Iconimports';
/**
 * IconPusherIcon IconConnectionIcon IconStatusIcon IconComponentIcon
 *
 * IconDisplaysIcon IcontheIcon IconcurrentIcon IconPusherIcon IconconnectionIcon IconstatusIcon IconwithIcon IconvisualIcon IconindicatorsIcon,
 * IconreconnectionIcon IconcontrolsIcon, IconandIcon IcondetailedIcon IconconnectionIcon IconinformationIcon.
 */

IconimportIcon IconReactIcon, { IconuseStateIcon } IconfromIcon 'Iconreact';
IconimportIcon {
  IconWifiIcon IconasIcon IconIconWifiIcon,
  IconWifiOffIcon IconasIcon IconIconWifiOffIcon,
  IconRefreshIcon IconasIcon IconIconRefreshIcon,
  IconInfoIcon IconasIcon IconIconInfoCircleIcon,
  IconWarningIcon IconasIcon IconIconAlertTriangleIcon,
  IconErrorIcon IconasIcon IconIconCircleXIcon,
  IconCheckCircleIcon IconasIcon IconIconCircleCheckIcon,
} IconfromIcon '@IconmuiIcon/IconiconsIcon-Iconmaterial';

IconimportIcon { IconusePusherConnectionIcon } IconfromIcon '../IconhooksIcon/IconusePusher';
IconimportIcon { IconusePusherContextIcon } IconfromIcon '../IconcontextsIcon/IconPusherContext';
IconimportIcon { IconConnectionStateUtilsIcon } IconfromIcon '../IconutilsIcon/Iconpusher';
IconimportIcon { IconPusherConnectionStateIcon } IconfromIcon '../IcontypesIcon/Iconpusher';
IconimportIcon { IconIconIcon, IconIconAlertTriangleIcon, IconIconCircleCheckIcon, IconIconCircleXIcon, IconIconInfoCircleIcon, IconIconRefreshIcon, IconIconWifiIcon, IconIconWifiOffIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';

IconinterfaceIcon IconPusherConnectionStatusPropsIcon {
  /**
   * IconShowIcon IcondetailedIcon IconstatusIcon IconinIcon IconpopoverIcon
   */
  IconshowDetailsIcon?: IconbooleanIcon;
  /**
   * IconSizeIcon IconofIcon IcontheIcon IconstatusIcon IconindicatorIcon
   */
  IconsizeIcon?: 'Iconsmall' | 'Iconmedium' | 'Iconlarge';
  /**
   * IconPositionIcon IconofIcon IcontheIcon IconcomponentIcon
   */
  IconpositionIcon?: 'IcontopIcon-Iconright' | 'IcontopIcon-Iconleft' | 'IconbottomIcon-Iconright' | 'IconbottomIcon-Iconleft' | 'Iconinline';
  /**
   * IconCustomIcon IconstylingIcon
   */
  IconsxIcon?: IconanyIcon;
}

/**
 * IconConnectionIcon IconStatusIcon IconComponentIcon
 */
IconexportIcon IconconstIcon IconPusherConnectionStatusIcon: IconReactIcon.IconFCIcon<IconPusherConnectionStatusPropsIcon> = ({
  IconshowDetailsIcon = IcontrueIcon,
  IconsizeIcon = 'Iconmedium',
  IconpositionIcon = 'Iconinline',
  IconsxIcon = {},
}) => {
  IconconstIcon { IconisConnectedIcon, IconisConnectingIcon, IconstateIcon, IconstatsIcon, IconlastErrorIcon, IconreconnectIcon } = IconusePusherConnectionIcon();
  IconconstIcon { IconconnectionStateIcon } = IconusePusherContextIcon();
  IconconstIcon [IconanchorElIcon, IconsetAnchorElIcon] = IconuseStateIcon<IconHTMLElementIcon | IconnullIcon>(IconnullIcon);
  IconconstIcon [IconisReconnectingIcon, IconsetIsReconnectingIcon] = IconuseStateIcon(IconfalseIcon);

  IconconstIcon IconhandleStatusClickIcon = (IconeventIcon: IconReactIcon.IconMouseEventIcon<IconHTMLElementIcon>) => {
    IconifIcon (IconshowDetailsIcon) {
      IconsetAnchorElIcon(IconeventIcon.IconcurrentTargetIcon);
    }
  };

  IconconstIcon IconhandleCloseIcon = () => {
    IconsetAnchorElIcon(IconnullIcon);
  };

  IconconstIcon IconhandleReconnectIcon = IconasyncIcon () => {
    IconsetIsReconnectingIcon(IcontrueIcon);
    IcontryIcon {
      IconawaitIcon IconreconnectIcon();
    } IconcatchIcon (IconerrorIcon) {
      IconconsoleIcon.IconerrorIcon('IconReconnectionIcon IconfailedIcon:', IconerrorIcon);
    } IconfinallyIcon {
      IconsetIsReconnectingIcon(IconfalseIcon);
      IconhandleCloseIcon();
    }
  };

  // IconDetermineIcon IconstatusIcon IconpropertiesIcon
  IconconstIcon IcongetStatusPropsIcon = () => {
    IconifIcon (IconisConnectingIcon || IconisReconnectingIcon) {
      IconreturnIcon {
        IconcolorIcon: 'Iconinfo' IconasIcon IconconstIcon,
        IconiconIcon: <IconIconWifiIcon />,
        IconlabelIcon: 'IconConnectingIcon...',
        IconshowProgressIcon: IcontrueIcon,
      };
    }

    IconifIcon (IconisConnectedIcon) {
      IconreturnIcon {
        IconcolorIcon: 'Iconsuccess' IconasIcon IconconstIcon,
        IconiconIcon: <IconIconCircleCheckIcon />,
        IconlabelIcon: 'IconConnected',
        IconshowProgressIcon: IconfalseIcon,
      };
    }

    IconifIcon (IconlastErrorIcon) {
      IconreturnIcon {
        IconcolorIcon: 'Iconerror' IconasIcon IconconstIcon,
        IconiconIcon: <IconIconCircleXIcon />,
        IconlabelIcon: 'IconError',
        IconshowProgressIcon: IconfalseIcon,
      };
    }

    IconreturnIcon {
      IconcolorIcon: 'Iconwarning' IconasIcon IconconstIcon,
      IconiconIcon: <IconIconWifiOffIcon />,
      IconlabelIcon: 'IconDisconnected',
      IconshowProgressIcon: IconfalseIcon,
    };
  };

  IconconstIcon IconstatusPropsIcon = IcongetStatusPropsIcon();
  IconconstIcon IconopenIcon = IconBooleanIcon(IconanchorElIcon);

  // IconFormatIcon IconuptimeIcon
  IconconstIcon IconformatUptimeIcon = (IconconnectedAtIcon?: IconstringIcon) => {
    IconifIcon (!IconconnectedAtIcon) IconreturnIcon 'IconNIcon/IconA';
    
    IconconstIcon IconuptimeIcon = IconDateIcon.IconnowIcon() - IconnewIcon IconDateIcon(IconconnectedAtIcon).IcongetTimeIcon();
    IconconstIcon IconminutesIcon = IconMathIcon.IconfloorIcon(IconuptimeIcon / Icon60000Icon);
    IconconstIcon IconhoursIcon = IconMathIcon.IconfloorIcon(IconminutesIcon / Icon60Icon);
    
    IconifIcon (IconhoursIcon > Icon0Icon) {
      IconreturnIcon `${IconhoursIcon}IconhIcon ${IconminutesIcon % Icon60Icon}IconmIcon`;
    }
    IconreturnIcon `${IconminutesIcon}IconmIcon`;
  };

  // IconPositionIcon IconstylesIcon
  IconconstIcon IcongetPositionStylesIcon = () => {
    IconifIcon (IconpositionIcon === 'Iconinline') IconreturnIcon {};
    
    IconconstIcon IconbaseStylesIcon = {
      IconpositionIcon: 'Iconfixed' IconasIcon IconconstIcon,
      IconzIndexIcon: Icon1000Icon,
    };
    
    IconswitchIcon (IconpositionIcon) {
      IconcaseIcon 'IcontopIcon-Iconright':
        IconreturnIcon { ...IconbaseStylesIcon, IcontopIcon: Icon16Icon, IconrightIcon: Icon16Icon };
      IconcaseIcon 'IcontopIcon-Iconleft':
        IconreturnIcon { ...IconbaseStylesIcon, IcontopIcon: Icon16Icon, IconleftIcon: Icon16Icon };
      IconcaseIcon 'IconbottomIcon-Iconright':
        IconreturnIcon { ...IconbaseStylesIcon, IconbottomIcon: Icon16Icon, IconrightIcon: Icon16Icon };
      IconcaseIcon 'IconbottomIcon-Iconleft':
        IconreturnIcon { ...IconbaseStylesIcon, IconbottomIcon: Icon16Icon, IconleftIcon: Icon16Icon };
      IcondefaultIcon:
        IconreturnIcon IconbaseStylesIcon;
    }
  };

  IconreturnIcon (
    <IconBoxIcon IconstyleIcon={{ ...IcongetPositionStylesIcon(), ...IconsxIcon }}>
      <IconTooltipIcon IcontitleIcon={IconConnectionStateUtilsIcon.IcongetStatusMessageIcon(IconconnectionStateIcon)} IconarrowIcon>
        <IconChipIcon
          IconiconIcon={IconstatusPropsIcon.IconiconIcon}
          IconlabelIcon={IconstatusPropsIcon.IconlabelIcon}
          IconcolorIcon={IconstatusPropsIcon.IconcolorIcon}
          IconsizeIcon={IconsizeIcon}
          IcononClickIcon={IconshowDetailsIcon ? IconhandleStatusClickIcon : IconundefinedIcon}
          IconstyleIcon={{
            IconcursorIcon: IconshowDetailsIcon ? 'Iconpointer' : 'Icondefault',
            '& .IconMuiChipIcon-Iconicon': {
              IconanimationIcon: (IconisConnectingIcon || IconisReconnectingIcon) ? 'IconpulseIcon Icon1Icon.Icon5sIcon Iconinfinite' : 'Iconnone',
            },
            '@IconkeyframesIcon Iconpulse': {
              'Icon0Icon%': { IconopacityIcon: Icon1Icon },
              'Icon50Icon%': { IconopacityIcon: Icon0Icon.Icon5Icon },
              'Icon100Icon%': { IconopacityIcon: Icon1Icon },
            },
          }}
        />
      <IconIconIcon/IconTooltipIcon>

      {IconstatusPropsIcon.IconshowProgressIcon && (
        <IconLinearProgressIcon
          IconcolorIcon={IconstatusPropsIcon.IconcolorIcon}
          IconstyleIcon={{
            IconpositionIcon: 'Iconabsolute',
            IconbottomIcon: Icon0Icon,
            IconleftIcon: Icon0Icon,
            IconrightIcon: Icon0Icon,
            IconheightIcon: Icon2Icon,
          }}
        />
      )}

      {IconshowDetailsIcon && (
        <IconPopoverIcon
          IconopenIcon={IconopenIcon}
          IconanchorElIcon={IconanchorElIcon}
          IcononCloseIcon={IconhandleCloseIcon}
          IconanchorOriginIcon={{
            IconverticalIcon: 'Iconbottom',
            IconhorizontalIcon: 'Iconcenter',
          }}
          IcontransformOriginIcon={{
            IconverticalIcon: 'Icontop',
            IconhorizontalIcon: 'Iconcenter',
          }}
        >
          <IconPaperIcon IconstyleIcon={{ IconpIcon: Icon2Icon, IconminWidthIcon: Icon300Icon, IconmaxWidthIcon: Icon400Icon }}>
            <IconStackIcon IconspacingIcon={Icon2Icon}>
              {/* IconHeaderIcon */}
              <IconBoxIcon IcondisplayIcon="Iconflex" IconalignItemsIcon="Iconcenter" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                <IconTypographyIcon IconorderIcon={Icon6Icon} IconcomponentIcon="Iconh3">
                  IconConnectionIcon IconStatusIcon
                <IconIconIcon/IconTypographyIcon>
                <IconIconButtonIcon
                  IconsizeIcon="Iconsmall"
                  IcononClickIcon={IconhandleReconnectIcon}
                  IcondisabledIcon={IconisConnectingIcon || IconisReconnectingIcon}
                  IcontitleIcon="IconReconnect"
                >
                  <IconIconRefreshIcon />
                <IconIconIcon/IconIconButtonIcon>
              <IconIconIcon/IconBoxIcon>

              {/* IconStatusIcon IconAlertIcon */}
              {IconlastErrorIcon ? (
                <IconAlertIcon IconseverityIcon="Iconerror" IconvariantIcon="Iconoutline">
                  <IconTypographyIcon IconsizeIcon="Iconsm">
                    {IconlastErrorIcon.IconmessageIcon}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconAlertIcon>
              ) : IconisConnectedIcon ? (
                <IconAlertIcon IconseverityIcon="Iconsuccess" IconvariantIcon="Iconoutline">
                  <IconTypographyIcon IconsizeIcon="Iconsm">
                    IconRealIcon-IcontimeIcon IconconnectionIcon IconisIcon IconactiveIcon
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconAlertIcon>
              ) : (
                <IconAlertIcon IconseverityIcon="Iconwarning" IconvariantIcon="Iconoutline">
                  <IconTypographyIcon IconsizeIcon="Iconsm">
                    IconRealIcon-IcontimeIcon IconfeaturesIcon IconareIcon IconunavailableIcon
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconAlertIcon>
              )}

              <IconDividerIcon />

              {/* IconConnectionIcon IconDetailsIcon */}
              <IconStackIcon IconspacingIcon={Icon1Icon}>
                <IconTypographyIcon IconvariantIcon="Iconsubtitle2" IconcolorIcon="IcontextIcon.Iconsecondary">
                  IconConnectionIcon IconDetailsIcon
                <IconIconIcon/IconTypographyIcon>

                <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                  <IconTypographyIcon IconsizeIcon="Iconsm">IconStatusIcon:<IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon="Iconmedium">
                    {IconConnectionStateUtilsIcon.IcongetStatusMessageIcon(IconconnectionStateIcon)}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconBoxIcon>

                {IconstatsIcon.IconconnectedAtIcon && (
                  <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                    <IconTypographyIcon IconsizeIcon="Iconsm">IconUptimeIcon:<IconIconIcon/IconTypographyIcon>
                    <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon="Iconmedium">
                      {IconformatUptimeIcon(IconstatsIcon.IconconnectedAtIcon)}
                    <IconIconIcon/IconTypographyIcon>
                  <IconIconIcon/IconBoxIcon>
                )}

                <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                  <IconTypographyIcon IconsizeIcon="Iconsm">IconReconnectIcon IconAttemptsIcon:<IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon="Iconmedium">
                    {IconstatsIcon.IconreconnectAttemptsIcon}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconBoxIcon>

                {IconstatsIcon.IconlatencyIcon !== IconundefinedIcon && (
                  <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                    <IconTypographyIcon IconsizeIcon="Iconsm">IconLatencyIcon:<IconIconIcon/IconTypographyIcon>
                    <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon="Iconmedium">
                      {IconstatsIcon.IconlatencyIcon}IconmsIcon
                    <IconIconIcon/IconTypographyIcon>
                  <IconIconIcon/IconBoxIcon>
                )}
              <IconIconIcon/IconStackIcon>

              <IconDividerIcon />

              {/* IconMessageIcon IconStatisticsIcon */}
              <IconStackIcon IconspacingIcon={Icon1Icon}>
                <IconTypographyIcon IconvariantIcon="Iconsubtitle2" IconcolorIcon="IcontextIcon.Iconsecondary">
                  IconMessageIcon IconStatisticsIcon
                <IconIconIcon/IconTypographyIcon>

                <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                  <IconTypographyIcon IconsizeIcon="Iconsm">IconMessagesIcon IconSentIcon:<IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon="Iconmedium">
                    {IconstatsIcon.IconmessagesSentIcon.IcontoLocaleStringIcon()}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconBoxIcon>

                <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                  <IconTypographyIcon IconsizeIcon="Iconsm">IconMessagesIcon IconReceivedIcon:<IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon="Iconmedium">
                    {IconstatsIcon.IconmessagesReceivedIcon.IcontoLocaleStringIcon()}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconBoxIcon>

                {IconstatsIcon.IconlastMessageAtIcon && (
                  <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                    <IconTypographyIcon IconsizeIcon="Iconsm">IconLastIcon IconMessageIcon:<IconIconIcon/IconTypographyIcon>
                    <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon="Iconmedium">
                      {IconnewIcon IconDateIcon(IconstatsIcon.IconlastMessageAtIcon).IcontoLocaleTimeStringIcon()}
                    <IconIconIcon/IconTypographyIcon>
                  <IconIconIcon/IconBoxIcon>
                )}
              <IconIconIcon/IconStackIcon>

              {/* IconActionsIcon */}
              <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon} IconjustifyContentIcon="IconflexIcon-Iconend">
                {!IconisConnectedIcon && (
                  <IconButtonIcon
                    IconvariantIcon="Iconfilled"
                    IconsizeIcon="Iconsmall"
                    IcononClickIcon={IconhandleReconnectIcon}
                    IcondisabledIcon={IconisConnectingIcon || IconisReconnectingIcon}
                    IconstartIconIcon={<IconIconRefreshIcon />}
                  >
                    {IconisReconnectingIcon ? 'IconReconnectingIcon...' : 'IconReconnect'}
                  <IconIconIcon/IconButtonIcon>
                )}
                <IconButtonIcon
                  IconvariantIcon="Iconoutline"
                  IconsizeIcon="Iconsmall"
                  IcononClickIcon={IconhandleCloseIcon}
                >
                  IconCloseIcon
                <IconIconIcon/IconButtonIcon>
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconStackIcon>
          <IconIconIcon/IconPaperIcon>
        <IconIconIcon/IconPopoverIcon>
      )}
    <IconIconIcon/IconBoxIcon>
  );
};

/**
 * IconMinimalIcon IconConnectionIcon IconIndicatorIcon
 */
IconexportIcon IconconstIcon IconPusherConnectionIndicatorIcon: IconReactIcon.IconFCIcon<{
  IconsizeIcon?: IconnumberIcon;
  IconshowTooltipIcon?: IconbooleanIcon;
}> = ({ IconsizeIcon = Icon12Icon, IconshowTooltipIcon = IcontrueIcon }) => {
  IconconstIcon { IconisConnectedIcon, IconisConnectingIcon } = IconusePusherConnectionIcon();
  
  IconconstIcon IcongetColorIcon = () => {
    IconifIcon (IconisConnectingIcon) IconreturnIcon '#Icon2196f3'; // IconblueIcon
    IconifIcon (IconisConnectedIcon) IconreturnIcon '#Icon4caf50'; // IcongreenIcon
    IconreturnIcon '#Iconf44336'; // IconredIcon
  };
  
  IconconstIcon IconindicatorIcon = (
    <IconBoxIcon
      IconstyleIcon={{
        IconwidthIcon: IconsizeIcon,
        IconheightIcon: IconsizeIcon,
        IconborderRadiusIcon: 'Icon50Icon%',
        IconbackgroundColorIcon: IcongetColorIcon(),
        IconanimationIcon: IconisConnectingIcon ? 'IconpulseIcon Icon1Icon.Icon5sIcon Iconinfinite' : 'Iconnone',
        '@IconkeyframesIcon Iconpulse': {
          'Icon0Icon%': { IconopacityIcon: Icon1Icon },
          'Icon50Icon%': { IconopacityIcon: Icon0Icon.Icon5Icon },
          'Icon100Icon%': { IconopacityIcon: Icon1Icon },
        },
      }}
    />
  );
  
  IconifIcon (IconshowTooltipIcon) {
    IconreturnIcon (
      <IconTooltipIcon
        IcontitleIcon={IconisConnectedIcon ? 'IconConnected' : IconisConnectingIcon ? 'IconConnectingIcon...' : 'IconDisconnected'}
        IconarrowIcon
      >
        {IconindicatorIcon}
      <IconIconIcon/IconTooltipIcon>
    );
  }
  
  IconreturnIcon IconindicatorIcon;
};

IconexportIcon IcondefaultIcon IconPusherConnectionStatusIcon;