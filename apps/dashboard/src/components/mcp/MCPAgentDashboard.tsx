IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../../IconutilsIcon/IconmuiIcon-Iconimports';
IconimportIcon * IconasIcon IconReactIcon IconfromIcon "Iconreact";

IconimportIcon { IconuseStateIcon, IconuseEffectIcon } IconfromIcon "Iconreact";
IconimportIcon {
  IconIconSmartToyIcon,
  IconIconPsychologyIcon,
  IconIconSchoolIcon,
  IconIconQuizIcon,
  IconIconTerrainIcon,
  IconIconCodeIcon,
  IconIconRateReviewIcon,
  IconIconPlayerPlayIcon,
  IconIconPlayerPauseIcon,
  IconIconPlayerStopIcon,
  IconIconRefreshIcon,
  IconIconSettingsIcon,
  IconIconMemoryIcon,
  IconIconSpeedIcon,
  IconIconCircleCheckIcon,
  IconIconCircleXIcon,
  IconIconAlertTriangleIcon,
  IconIconInfoCircleIcon,
} IconfromIcon "@IconmuiIcon/IconiconsIcon-Iconmaterial";
IconimportIcon {
  IconLineChartIcon,
  IconLineIcon,
  IconAreaChartIcon,
  IconAreaIcon,
  IconXAxisIcon,
  IconYAxisIcon,
  IconCartesianGridIcon,
  IconTooltipIcon,
  IconResponsiveContainerIcon,
  IconBarChartIcon,
  IconBarIcon,
} IconfromIcon "Iconrecharts";
IconimportIcon { IconusePusherContextIcon } IconfromIcon "../../IconcontextsIcon/IconPusherContext";
IconimportIcon { IconuseAppDispatchIcon } IconfromIcon "../../Iconstore";
IconimportIcon { IconaddNotificationIcon } IconfromIcon "../../IconstoreIcon/IconslicesIcon/IconuiSlice";
IconimportIcon { IconIconIcon, IconIconAlertTriangleIcon, IconIconCircleCheckIcon, IconIconCircleXIcon, IconIconCodeIcon, IconIconInfoCircleIcon, IconIconMemoryIcon, IconIconPlayerPauseIcon, IconIconPlayerPlayIcon, IconIconPlayerStopIcon, IconIconPsychologyIcon, IconIconQuizIcon, IconIconRateReviewIcon, IconIconRefreshIcon, IconIconSchoolIcon, IconIconSettingsIcon, IconIconSmartToyIcon, IconIconSpeedIcon, IconIconTerrainIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';

IconinterfaceIcon IconMCPAgentIcon {
  IconidIcon: IconstringIcon;
  IconnameIcon: IconstringIcon;
  IcontypeIcon: "Iconsupervisor" | "Iconcontent" | "Iconquiz" | "Iconterrain" | "Iconscript" | "Iconreview";
  IconstatusIcon: "Iconactive" | "Iconidle" | "Iconworking" | "Iconerror" | "Iconoffline";
  IconlastActivityIcon: IconstringIcon;
  IcontasksCompletedIcon: IconnumberIcon;
  IconavgResponseTimeIcon: IconnumberIcon;
  IconsuccessRateIcon: IconnumberIcon;
  IconmemoryUsageIcon: IconnumberIcon;
  IconcpuUsageIcon: IconnumberIcon;
  IconcurrentTaskIcon?: {
    IconidIcon: IconstringIcon;
    IcontypeIcon: IconstringIcon;
    IconprogressIcon: IconnumberIcon;
    IconstartedAtIcon: IconstringIcon;
  };
  IconcapabilitiesIcon: IconstringIcon[];
  IconmetricsIcon: {
    IcontimestampIcon: IconstringIcon;
    IconresponseTimeIcon: IconnumberIcon;
    IconmemoryUsageIcon: IconnumberIcon;
    IconcpuUsageIcon: IconnumberIcon;
  }[];
}

IconinterfaceIcon IconMCPMessageIcon {
  IconidIcon: IconstringIcon;
  IcontypeIcon: "Iconrequest" | "Iconresponse" | "Iconnotification" | "Iconerror";
  IconagentIdIcon: IconstringIcon;
  IconcontentIcon: IconstringIcon;
  IcontimestampIcon: IconstringIcon;
  IcondataIcon?: IconanyIcon;
}

IconinterfaceIcon IconMCPAgentDashboardPropsIcon {
  IconautoRefreshIcon?: IconbooleanIcon;
  IconshowLogsIcon?: IconbooleanIcon;
}

IconconstIcon IconAGENT_ICONSIcon: IconRecordIcon<IconstringIcon, IconReactIcon.IconReactElementIcon> = {
  IconsupervisorIcon: <IconIconSmartToyIcon />,
  IconcontentIcon: <IconIconPsychologyIcon />,
  IconquizIcon: <IconIconQuizIcon />,
  IconterrainIcon: <IconIconTerrainIcon />,
  IconscriptIcon: <IconIconCodeIcon />,
  IconreviewIcon: <IconIconRateReviewIcon />,
};

IconconstIcon IconAGENT_COLORSIcon: IconRecordIcon<IconstringIcon, IconstringIcon> = {
  IconsupervisorIcon: "#Icon2563EB",
  IconcontentIcon: "#Icon22C55E",
  IconquizIcon: "#IconFACC15",
  IconterrainIcon: "#Icon9333EA",
  IconscriptIcon: "#IconEF4444",
  IconreviewIcon: "#Icon06B6D4",
};

IconexportIcon IconfunctionIcon IconMCPAgentDashboardIcon({ 
  IconautoRefreshIcon = IcontrueIcon,
  IconshowLogsIcon = IcontrueIcon 
}: IconMCPAgentDashboardPropsIcon) {
  IconconstIcon IconthemeIcon = IconuseThemeIcon();
  IconconstIcon IcondispatchIcon = IconuseAppDispatchIcon();
  IconconstIcon { IconisConnectedIcon, IconsubscribeToChannelIcon, IconunsubscribeFromChannelIcon, IconsendMessageIcon } = IconusePusherContextIcon();
  
  IconconstIcon [IconagentsIcon, IconsetAgentsIcon] = IconuseStateIcon<IconMCPAgentIcon[]>([]);
  IconconstIcon [IconmessagesIcon, IconsetMessagesIcon] = IconuseStateIcon<IconMCPMessageIcon[]>([]);
  IconconstIcon [IconloadingIcon, IconsetLoadingIcon] = IconuseStateIcon(IcontrueIcon);
  IconconstIcon [IconerrorIcon, IconsetErrorIcon] = IconuseStateIcon<IconstringIcon | IconnullIcon>(IconnullIcon);
  IconconstIcon [IconselectedAgentIcon, IconsetSelectedAgentIcon] = IconuseStateIcon<IconMCPAgentIcon | IconnullIcon>(IconnullIcon);
  IconconstIcon [IconisTaskDialogOpenIcon, IconsetIsTaskDialogOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IcontaskTypeIcon, IconsetTaskTypeIcon] = IconuseStateIcon<IconstringIcon>("");
  IconconstIcon [IcontaskContentIcon, IconsetTaskContentIcon] = IconuseStateIcon<IconstringIcon>("");
  IconconstIcon [IconmcpWebSocketIcon, IconsetMcpWebSocketIcon] = IconuseStateIcon<IconWebSocketIcon | IconnullIcon>(IconnullIcon);
  IconconstIcon [IconreconnectAttemptsIcon, IconsetReconnectAttemptsIcon] = IconuseStateIcon(Icon0Icon);
  IconconstIcon IconMAX_RECONNECT_ATTEMPTSIcon = Icon3Icon;
  IconconstIcon IconRECONNECT_DELAY_BASEIcon = Icon5000Icon; // IconBaseIcon IcondelayIcon IconinIcon IconmsIcon

  // IconConnectIcon IcontoIcon IconMCPIcon IconWebSocketIcon IconserverIcon IcononIcon IconportIcon Icon9876Icon IconwithIcon IconretryIcon IconlogicIcon
  IconconstIcon IconconnectToMCPIcon = IconReactIcon.IconuseCallbackIcon(IconasyncIcon () => {
    // IconCheckIcon IconifIcon Iconwe'IconveIcon IconexceededIcon IconmaxIcon IconreconnectionIcon IconattemptsIcon
    IconifIcon (IconreconnectAttemptsIcon >= IconMAX_RECONNECT_ATTEMPTSIcon) {
      IconconsoleIcon.IconlogIcon('IconMaxIcon IconreconnectionIcon IconattemptsIcon IconreachedIcon. IconUsingIcon IconmockIcon IcondataIcon.');
      IconsetErrorIcon('IconMCPIcon IconserverIcon IconunavailableIcon - IconusingIcon IconmockIcon Icondata');
      IconloadMockDataIcon();
      IconsetLoadingIcon(IconfalseIcon);
      IconreturnIcon;
    }

    // IconCloseIcon IconexistingIcon IconconnectionIcon IconifIcon IconanyIcon
    IconifIcon (IconmcpWebSocketIcon && IconmcpWebSocketIcon.IconreadyStateIcon !== IconWebSocketIcon.IconCLOSEDIcon) {
      IconmcpWebSocketIcon.IconcloseIcon();
    }

    IcontryIcon {
      IconsetLoadingIcon(IcontrueIcon);
      IconsetErrorIcon(IconnullIcon);

      // IconInitializeIcon IconWebSocketIcon IconconnectionIcon IcontoIcon IconMCPIcon IconserverIcon
      IconconstIcon IconmcpWsIcon = IconnewIcon IconWebSocketIcon('IconwsIcon://IconlocalhostIcon:Icon9876Icon/Iconmcp');
      IconsetMcpWebSocketIcon(IconmcpWsIcon);
      
      IconmcpWsIcon.IcononopenIcon = () => {
        IconconsoleIcon.IconlogIcon('IconConnectedIcon IcontoIcon IconMCPIcon Iconserver');
        IconsetReconnectAttemptsIcon(Icon0Icon); // IconResetIcon IconattemptsIcon IcononIcon IconsuccessfulIcon IconconnectionIcon
        // IconRequestIcon IconagentIcon IconstatusIcon
        IconmcpWsIcon.IconsendIcon(IconJSONIcon.IconstringifyIcon({
          IcontypeIcon: 'Iconget_agents_status',
          IcontimestampIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon(),
        }));
      };

      IconmcpWsIcon.IcononmessageIcon = (IconeventIcon) => {
        IconconstIcon IconmessageIcon = IconJSONIcon.IconparseIcon(IconeventIcon.IcondataIcon);
        IconhandleMCPMessageIcon(IconmessageIcon);
      };

      IconmcpWsIcon.IcononerrorIcon = (IconerrorIcon) => {
        IconconsoleIcon.IconerrorIcon('IconMCPIcon IconWebSocketIcon IconerrorIcon:', IconerrorIcon);
        IconsetErrorIcon('IconMCPIcon IconconnectionIcon IconerrorIcon - IconwillIcon Iconretry');
      };

      IconmcpWsIcon.IcononcloseIcon = (IconeventIcon) => {
        IconconsoleIcon.IconlogIcon('IconMCPIcon IconWebSocketIcon IconconnectionIcon IconclosedIcon:', IconeventIcon.IconcodeIcon, IconeventIcon.IconreasonIcon);
        IconsetMcpWebSocketIcon(IconnullIcon);
        
        // IconOnlyIcon IconretryIcon IconifIcon IconautoRefreshIcon IconisIcon IconenabledIcon IconandIcon IconweIcon Iconhaven'IcontIcon IconexceededIcon IconmaxIcon IconattemptsIcon
        IconifIcon (IconautoRefreshIcon && IconreconnectAttemptsIcon <IconIconIcon IconMAX_RECONNECT_ATTEMPTSIcon) {
          IconconstIcon IcondelayIcon = IconRECONNECT_DELAY_BASEIcon * IconMathIcon.IconpowIcon(Icon2Icon, IconreconnectAttemptsIcon); // IconExponentialIcon IconbackoffIcon
          IconconsoleIcon.IconlogIcon(`IconReconnectingIcon IconinIcon ${IcondelayIcon/Icon1000Icon} IconsecondsIcon... (IconattemptIcon ${IconreconnectAttemptsIcon + Icon1Icon}/${IconMAX_RECONNECT_ATTEMPTSIcon})`);
          IconsetReconnectAttemptsIcon(IconprevIcon => IconprevIcon + Icon1Icon);
          IconsetTimeoutIcon(() => {
            IconconnectToMCPIcon();
          }, IcondelayIcon);
        } IconelseIcon IconifIcon (IconreconnectAttemptsIcon >= IconMAX_RECONNECT_ATTEMPTSIcon) {
          IconsetErrorIcon('IconMCPIcon IconserverIcon IconunavailableIcon - IconusingIcon IconmockIcon Icondata');
          IconloadMockDataIcon();
        }
      };

    } IconcatchIcon (IconerrIcon: IconanyIcon) {
      IconconsoleIcon.IconerrorIcon('IconFailedIcon IcontoIcon IconcreateIcon IconWebSocketIcon IconconnectionIcon:', IconerrIcon);
      IconsetErrorIcon(IconerrIcon.IconmessageIcon || 'IconFailedIcon IcontoIcon IconconnectIcon IcontoIcon IconMCPIcon Iconserver');
      IconsetMcpWebSocketIcon(IconnullIcon);
      
      // IconUseIcon IconmockIcon IcondataIcon IconasIcon IconfallbackIcon
      IconifIcon (IconreconnectAttemptsIcon >= IconMAX_RECONNECT_ATTEMPTSIcon - Icon1Icon) {
        IconloadMockDataIcon();
      }
    } IconfinallyIcon {
      IconsetLoadingIcon(IconfalseIcon);
    }
  }, [IconautoRefreshIcon, IconreconnectAttemptsIcon, IconmcpWebSocketIcon]);

  // IconHandleIcon IconMCPIcon IconmessagesIcon
  IconconstIcon IconhandleMCPMessageIcon = (IconmessageIcon: IconanyIcon) => {
    IconswitchIcon (IconmessageIcon.IcontypeIcon) {
      IconcaseIcon 'Iconagents_status':
        IconifIcon (IconmessageIcon.IconagentsIcon) {
          IconsetAgentsIcon(IconmessageIcon.IconagentsIcon);
        }
        IconbreakIcon;
      IconcaseIcon 'Iconagent_update':
        IconsetAgentsIcon(IconprevAgentsIcon =>
          IconprevAgentsIcon.IconmapIcon(IconagentIcon =>
            IconagentIcon.IconidIcon === IconmessageIcon.IconagentIdIcon
              ? { ...IconagentIcon, ...IconmessageIcon.IconupdatesIcon }
              : IconagentIcon
          )
        );
        IconbreakIcon;
      IconcaseIcon 'Icontask_progress':
        IconsetAgentsIcon(IconprevAgentsIcon =>
          IconprevAgentsIcon.IconmapIcon(IconagentIcon =>
            IconagentIcon.IconidIcon === IconmessageIcon.IconagentIdIcon
              ? { 
                  ...IconagentIcon, 
                  IconcurrentTaskIcon: IconmessageIcon.IcontaskIcon,
                  IconstatusIcon: "Iconworking"
                }
              : IconagentIcon
          )
        );
        IconbreakIcon;
      IconcaseIcon 'Icontask_completed':
        IconsetAgentsIcon(IconprevAgentsIcon =>
          IconprevAgentsIcon.IconmapIcon(IconagentIcon =>
            IconagentIcon.IconidIcon === IconmessageIcon.IconagentIdIcon
              ? { 
                  ...IconagentIcon, 
                  IconcurrentTaskIcon: IconundefinedIcon,
                  IconstatusIcon: "Iconactive",
                  IcontasksCompletedIcon: IconagentIcon.IcontasksCompletedIcon + Icon1Icon,
                  IconlastActivityIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon(),
                }
              : IconagentIcon
          )
        );
        IconbreakIcon;
      IconcaseIcon 'Iconerror':
        IcondispatchIcon(IconaddNotificationIcon({
          IcontypeIcon: 'Iconerror',
          IconmessageIcon: `IconMCPIcon IconIconCircleXIcon: ${IconmessageIcon.IconerrorIcon}`,
        }));
        IconbreakIcon;
      IcondefaultIcon:
        // IconAddIcon IcontoIcon IconmessageIcon IconlogIcon
        IconsetMessagesIcon(IconprevMessagesIcon => [
          {
            IconidIcon: IconDateIcon.IconnowIcon().IcontoStringIcon(),
            IcontypeIcon: IconmessageIcon.IcontypeIcon,
            IconagentIdIcon: IconmessageIcon.IconagentIdIcon || 'Iconsystem',
            IconcontentIcon: IconmessageIcon.IconcontentIcon || IconJSONIcon.IconstringifyIcon(IconmessageIcon),
            IcontimestampIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon(),
            IcondataIcon: IconmessageIcon,
          },
          ...IconprevMessagesIcon.IconsliceIcon(Icon0Icon, Icon99Icon), // IconKeepIcon IconlastIcon Icon100Icon IconmessagesIcon
        ]);
        IconbreakIcon;
    }
  };

  // IconLoadIcon IconmockIcon IcondataIcon IconwhenIcon IconMCPIcon IconisIcon IconnotIcon IconavailableIcon
  IconconstIcon IconloadMockDataIcon = () => {
    IconconstIcon IconmockAgentsIcon: IconMCPAgentIcon[] = [
      {
        IconidIcon: "Iconsupervisor",
        IconnameIcon: "IconSupervisorIcon IconAgent",
        IcontypeIcon: "Iconsupervisor",
        IconstatusIcon: "Iconactive",
        IconlastActivityIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon(),
        IcontasksCompletedIcon: Icon156Icon,
        IconavgResponseTimeIcon: Icon245Icon,
        IconsuccessRateIcon: Icon98Icon.Icon5Icon,
        IconmemoryUsageIcon: Icon68Icon,
        IconcpuUsageIcon: Icon42Icon,
        IconcapabilitiesIcon: ["Iconorchestration", "Icontask_routing", "Iconerror_handling"],
        IconmetricsIcon: IconArrayIcon.IconfromIcon({ IconlengthIcon: Icon10Icon }, (Icon_Icon, IconiIcon) => ({
          IcontimestampIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - IconiIcon * Icon60000Icon).IcontoISOStringIcon(),
          IconresponseTimeIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon500Icon) + Icon200Icon,
          IconmemoryUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon20Icon) + Icon60Icon,
          IconcpuUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon30Icon) + Icon30Icon,
        })),
      },
      {
        IconidIcon: "Iconcontent",
        IconnameIcon: "IconContentIcon IconGenerator",
        IcontypeIcon: "Iconcontent",
        IconstatusIcon: "Iconworking",
        IconlastActivityIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon(),
        IcontasksCompletedIcon: Icon89Icon,
        IconavgResponseTimeIcon: Icon1200Icon,
        IconsuccessRateIcon: Icon94Icon.Icon2Icon,
        IconmemoryUsageIcon: Icon85Icon,
        IconcpuUsageIcon: Icon78Icon,
        IconcurrentTaskIcon: {
          IconidIcon: "Icontask_001",
          IcontypeIcon: "Icongenerate_lesson",
          IconprogressIcon: Icon65Icon,
          IconstartedAtIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon120000Icon).IcontoISOStringIcon(),
        },
        IconcapabilitiesIcon: ["Iconlesson_generation", "Iconcontent_creation", "Iconcurriculum_design"],
        IconmetricsIcon: IconArrayIcon.IconfromIcon({ IconlengthIcon: Icon10Icon }, (Icon_Icon, IconiIcon) => ({
          IcontimestampIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - IconiIcon * Icon60000Icon).IcontoISOStringIcon(),
          IconresponseTimeIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon1000Icon) + Icon800Icon,
          IconmemoryUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon25Icon) + Icon70Icon,
          IconcpuUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon40Icon) + Icon60Icon,
        })),
      },
      {
        IconidIcon: "Iconquiz",
        IconnameIcon: "IconIconQuizIcon IconAgent",
        IcontypeIcon: "Iconquiz",
        IconstatusIcon: "Iconidle",
        IconlastActivityIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon300000Icon).IcontoISOStringIcon(),
        IcontasksCompletedIcon: Icon234Icon,
        IconavgResponseTimeIcon: Icon180Icon,
        IconsuccessRateIcon: Icon96Icon.Icon8Icon,
        IconmemoryUsageIcon: Icon45Icon,
        IconcpuUsageIcon: Icon25Icon,
        IconcapabilitiesIcon: ["Iconquiz_generation", "Iconassessment_creation", "Icongrading"],
        IconmetricsIcon: IconArrayIcon.IconfromIcon({ IconlengthIcon: Icon10Icon }, (Icon_Icon, IconiIcon) => ({
          IcontimestampIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - IconiIcon * Icon60000Icon).IcontoISOStringIcon(),
          IconresponseTimeIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon300Icon) + Icon150Icon,
          IconmemoryUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon15Icon) + Icon40Icon,
          IconcpuUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon20Icon) + Icon20Icon,
        })),
      },
      {
        IconidIcon: "Iconterrain",
        IconnameIcon: "IconIconTerrainIcon IconBuilder",
        IcontypeIcon: "Iconterrain",
        IconstatusIcon: "Iconactive",
        IconlastActivityIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon60000Icon).IcontoISOStringIcon(),
        IcontasksCompletedIcon: Icon67Icon,
        IconavgResponseTimeIcon: Icon3400Icon,
        IconsuccessRateIcon: Icon91Icon.Icon5Icon,
        IconmemoryUsageIcon: Icon92Icon,
        IconcpuUsageIcon: Icon85Icon,
        IconcapabilitiesIcon: ["Icon3d_modeling", "Iconenvironment_design", "Iconworld_building"],
        IconmetricsIcon: IconArrayIcon.IconfromIcon({ IconlengthIcon: Icon10Icon }, (Icon_Icon, IconiIcon) => ({
          IcontimestampIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - IconiIcon * Icon60000Icon).IcontoISOStringIcon(),
          IconresponseTimeIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon2000Icon) + Icon2500Icon,
          IconmemoryUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon20Icon) + Icon80Icon,
          IconcpuUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon30Icon) + Icon70Icon,
        })),
      },
      {
        IconidIcon: "Iconscript",
        IconnameIcon: "IconScriptIcon IconAgent",
        IcontypeIcon: "Iconscript",
        IconstatusIcon: "Iconerror",
        IconlastActivityIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon180000Icon).IcontoISOStringIcon(),
        IcontasksCompletedIcon: Icon145Icon,
        IconavgResponseTimeIcon: Icon890Icon,
        IconsuccessRateIcon: Icon89Icon.Icon2Icon,
        IconmemoryUsageIcon: Icon58Icon,
        IconcpuUsageIcon: Icon35Icon,
        IconcapabilitiesIcon: ["Iconlua_scripting", "Iconcode_generation", "Icondebugging"],
        IconmetricsIcon: IconArrayIcon.IconfromIcon({ IconlengthIcon: Icon10Icon }, (Icon_Icon, IconiIcon) => ({
          IcontimestampIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - IconiIcon * Icon60000Icon).IcontoISOStringIcon(),
          IconresponseTimeIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon800Icon) + Icon600Icon,
          IconmemoryUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon20Icon) + Icon50Icon,
          IconcpuUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon25Icon) + Icon30Icon,
        })),
      },
      {
        IconidIcon: "Iconreview",
        IconnameIcon: "IconReviewIcon IconAgent",
        IcontypeIcon: "Iconreview",
        IconstatusIcon: "Iconactive",
        IconlastActivityIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon30000Icon).IcontoISOStringIcon(),
        IcontasksCompletedIcon: Icon201Icon,
        IconavgResponseTimeIcon: Icon320Icon,
        IconsuccessRateIcon: Icon97Icon.Icon1Icon,
        IconmemoryUsageIcon: Icon52Icon,
        IconcpuUsageIcon: Icon28Icon,
        IconcapabilitiesIcon: ["Iconcontent_review", "Iconquality_assurance", "Iconvalidation"],
        IconmetricsIcon: IconArrayIcon.IconfromIcon({ IconlengthIcon: Icon10Icon }, (Icon_Icon, IconiIcon) => ({
          IcontimestampIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - IconiIcon * Icon60000Icon).IcontoISOStringIcon(),
          IconresponseTimeIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon400Icon) + Icon250Icon,
          IconmemoryUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon15Icon) + Icon45Icon,
          IconcpuUsageIcon: IconMathIcon.IconfloorIcon(IconMathIcon.IconrandomIcon() * Icon20Icon) + Icon25Icon,
        })),
      },
    ];

    IconsetAgentsIcon(IconmockAgentsIcon);
  };

  // IconInitialIcon IconconnectionIcon IconwithIcon IconcleanupIcon
  IconuseEffectIcon(() => {
    IconletIcon IconmountedIcon = IcontrueIcon;
    
    // IconOnlyIcon IconconnectIcon IconifIcon IconcomponentIcon IconisIcon IconmountedIcon IconandIcon IconnoIcon IconexistingIcon IconconnectionIcon
    IconifIcon (IconmountedIcon && !IconmcpWebSocketIcon) {
      IconconnectToMCPIcon();
    }
    
    // IconCleanupIcon IcononIcon IconunmountIcon
    IconreturnIcon () => {
      IconmountedIcon = IconfalseIcon;
      IconifIcon (IconmcpWebSocketIcon && IconmcpWebSocketIcon.IconreadyStateIcon !== IconWebSocketIcon.IconCLOSEDIcon) {
        IconmcpWebSocketIcon.IconcloseIcon();
      }
    };
  }, []); // IconRemoveIcon IconconnectToMCPIcon IconfromIcon IcondependenciesIcon IcontoIcon IconavoidIcon IconreconnectionIcon IconloopsIcon

  // IconRealIcon-IcontimeIcon IconupdatesIcon IconviaIcon IconregularIcon IconWebSocketIcon
  IconuseEffectIcon(() => {
    IconifIcon (!IconisConnectedIcon || !IconautoRefreshIcon) IconreturnIcon;

    IconconstIcon IconsubscriptionIdIcon = IconsubscribeToChannelIcon('Iconmcp_agents', {
      'Iconagents_status': (IconmessageIcon: IconanyIcon) => IconhandleMCPMessageIcon({ IcontypeIcon: 'Iconagents_status', ...IconmessageIcon }),
      'Iconagent_update': (IconmessageIcon: IconanyIcon) => IconhandleMCPMessageIcon({ IcontypeIcon: 'Iconagent_update', ...IconmessageIcon }),
      'Icontask_progress': (IconmessageIcon: IconanyIcon) => IconhandleMCPMessageIcon({ IcontypeIcon: 'Icontask_progress', ...IconmessageIcon }),
      'Icontask_completed': (IconmessageIcon: IconanyIcon) => IconhandleMCPMessageIcon({ IcontypeIcon: 'Icontask_completed', ...IconmessageIcon }),
      'Iconerror': (IconmessageIcon: IconanyIcon) => IconhandleMCPMessageIcon({ IcontypeIcon: 'Iconerror', ...IconmessageIcon })
    });

    IconreturnIcon () => {
      IconunsubscribeFromChannelIcon(IconsubscriptionIdIcon);
    };
  }, [IconisConnectedIcon, IconautoRefreshIcon, IconsubscribeToChannelIcon, IconunsubscribeFromChannelIcon]);

  // IconSendIcon IcontaskIcon IcontoIcon IconagentIcon
  IconconstIcon IconhandleSendTaskIcon = IconasyncIcon () => {
    IconifIcon (!IconselectedAgentIcon || !IcontaskTypeIcon || !IcontaskContentIcon) IconreturnIcon;

    IcontryIcon {
      // IconSendIcon IcontaskIcon IconviaIcon IconWebSocketIcon IconorIcon IconMCPIcon
      IconconstIcon IconmessageIcon = {
        IcontypeIcon: 'Iconassign_task',
        IconagentIdIcon: IconselectedAgentIcon.IconidIcon,
        IcontaskIcon: {
          IcontypeIcon: IcontaskTypeIcon,
          IconcontentIcon: IcontaskContentIcon,
          IcontimestampIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon(),
        },
      };

      IconifIcon (IconsendMessageIcon) {
        (IconsendMessageIcon IconasIcon IconanyIcon)('Iconmcp_agents', IconmessageIcon);
      }

      IcondispatchIcon(IconaddNotificationIcon({
        IcontypeIcon: 'Iconsuccess',
        IconmessageIcon: `IconTaskIcon IconsentIcon IcontoIcon ${IconselectedAgentIcon.IconnameIcon}`,
      }));

      IconsetIsTaskDialogOpenIcon(IconfalseIcon);
      IconsetTaskTypeIcon("");
      IconsetTaskContentIcon("");
    } IconcatchIcon (IconerrorIcon) {
      IcondispatchIcon(IconaddNotificationIcon({
        IcontypeIcon: 'Iconerror',
        IconmessageIcon: 'IconFailedIcon IcontoIcon IconsendIcon IcontaskIcon IcontoIcon Iconagent',
      }));
    }
  };

  IconconstIcon IcongetStatusColorIcon = (IconstatusIcon: IconstringIcon) => {
    IconswitchIcon (IconstatusIcon) {
      IconcaseIcon "Iconactive":
        IconreturnIcon "Iconsuccess";
      IconcaseIcon "Iconworking":
        IconreturnIcon "Iconwarning";
      IconcaseIcon "Iconidle":
        IconreturnIcon "Icondefault";
      IconcaseIcon "Iconerror":
        IconreturnIcon "Iconerror";
      IconcaseIcon "Iconoffline":
        IconreturnIcon "Iconerror";
      IcondefaultIcon:
        IconreturnIcon "Icondefault";
    }
  };

  IconconstIcon IcongetStatusIconIcon = (IconstatusIcon: IconstringIcon) => {
    IconswitchIcon (IconstatusIcon) {
      IconcaseIcon "Iconactive":
        IconreturnIcon <IconIconCircleCheckIcon IconcolorIcon="Icongreen" />;
      IconcaseIcon "Iconworking":
        IconreturnIcon <IconIconPlayerPlayIcon IconcolorIcon="Iconyellow" />;
      IconcaseIcon "Iconidle":
        IconreturnIcon <IconIconPlayerPauseIcon IconcolorIcon="Icondisabled" />;
      IconcaseIcon "Iconerror":
        IconreturnIcon <IconIconCircleXIcon IconcolorIcon="Iconred" />;
      IconcaseIcon "Iconoffline":
        IconreturnIcon <IconIconPlayerStopIcon IconcolorIcon="Iconred" />;
      IcondefaultIcon:
        IconreturnIcon <IconIconInfoCircleIcon />;
    }
  };

  IconifIcon (IconloadingIcon) {
    IconreturnIcon (
      <IconGridIcon IconcontainerIcon IconspacingIcon={Icon3Icon}>
        {[Icon1Icon, Icon2Icon, Icon3Icon, Icon4Icon].IconmapIcon((IconitemIcon) => (
          <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconmdIcon={Icon6Icon} IconlgIcon={Icon4Icon} IconkeyIcon={IconitemIcon}>
            <IconCardIcon>
              <IconCardContentIcon>
                <IconSkeletonIcon IconvariantIcon="Icontext" IconheightIcon={Icon40Icon} />
                <IconSkeletonIcon IconvariantIcon="Iconrectangular" IconheightIcon={Icon200Icon} />
              <IconIconIcon/IconCardContentIcon>
            <IconIconIcon/IconCardIcon>
          <IconIconIcon/IconGridIcon>
        ))}
      <IconIconIcon/IconGridIcon>
    );
  }

  IconreturnIcon (
    <IconGridIcon IconcontainerIcon IconspacingIcon={Icon3Icon}>
      {/* IconHeaderIcon */}
      <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon}>
        <IconCardIcon>
          <IconCardContentIcon>
            <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconalignItemsIcon="Iconcenter" IconmbIcon={Icon2Icon}>
              <IconTypographyIcon IconorderIcon={Icon5Icon} IconstyleIcon={{ IconfontWeightIcon: Icon600Icon }}>
                IconMCPIcon IconAgentIcon IconDashboardIcon
              <IconIconIcon/IconTypographyIcon>
              <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon} IconalignItemsIcon="Iconcenter">
                {IconmcpWebSocketIcon && IconmcpWebSocketIcon.IconreadyStateIcon === IconWebSocketIcon.IconOPENIcon ? (
                  <IconChipIcon IconlabelIcon="IconMCPIcon IconConnected" IconcolorIcon="Icongreen" IconsizeIcon="Iconsmall" />
                ) : IconreconnectAttemptsIcon > Icon0Icon ? (
                  <IconChipIcon 
                    IconlabelIcon={`IconReconnectingIcon... (${IconreconnectAttemptsIcon}/${IconMAX_RECONNECT_ATTEMPTSIcon})`} 
                    IconcolorIcon="Iconyellow" 
                    IconsizeIcon="Iconsmall" 
                  />
                ) : (
                  <IconChipIcon IconlabelIcon="IconMCPIcon IconOffline" IconcolorIcon="Icondefault" IconsizeIcon="Iconsmall" />
                )}
                <IconIconButtonIcon 
                  IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
                    IconsetReconnectAttemptsIcon(Icon0Icon);
                    IconconnectToMCPIcon();
                  }}
                  IcondisabledIcon={!!(IconmcpWebSocketIcon && IconmcpWebSocketIcon.IconreadyStateIcon === IconWebSocketIcon.IconCONNECTINGIcon)}
                >
                  <IconIconRefreshIcon />
                <IconIconIcon/IconIconButtonIcon>
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconStackIcon>

            {IconerrorIcon && (
              <IconAlertIcon IconseverityIcon="Iconwarning" IconstyleIcon={{ IconmbIcon: Icon2Icon }}>
                IconMCPIcon IconConnectionIcon IconIssueIcon: {IconerrorIcon} (IconUsingIcon IconmockIcon IcondataIcon)
              <IconIconIcon/IconAlertIcon>
            )}

            {/* IconQuickIcon IconStatsIcon */}
            <IconGridIcon IconcontainerIcon IconspacingIcon={Icon2Icon}>
              <IconGridIcon IconitemIcon IconxsIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
                <IconPaperIcon IconstyleIcon={{ IconpIcon: Icon2Icon, IcontextAlignIcon: 'Iconcenter' }}>
                  <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                    IconActiveIcon IconAgentsIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconorderIcon={Icon4Icon} IconstyleIcon={{ IconfontWeightIcon: Icon700Icon, IconcolorIcon: 'IconsuccessIcon.Iconmain' }}>
                    {IconagentsIcon.IconfilterIcon(IconaIcon => IconaIcon.IconstatusIcon === "Iconactive" || IconaIcon.IconstatusIcon === "Iconworking").IconlengthIcon}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconPaperIcon>
              <IconIconIcon/IconGridIcon>
              <IconGridIcon IconitemIcon IconxsIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
                <IconPaperIcon IconstyleIcon={{ IconpIcon: Icon2Icon, IcontextAlignIcon: 'Iconcenter' }}>
                  <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                    IconTasksIcon IconCompletedIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconorderIcon={Icon4Icon} IconstyleIcon={{ IconfontWeightIcon: Icon700Icon, IconcolorIcon: 'IconprimaryIcon.Iconmain' }}>
                    {IconagentsIcon.IconreduceIcon((IconsumIcon, IconagentIcon) => IconsumIcon + IconagentIcon.IcontasksCompletedIcon, Icon0Icon)}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconPaperIcon>
              <IconIconIcon/IconGridIcon>
              <IconGridIcon IconitemIcon IconxsIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
                <IconPaperIcon IconstyleIcon={{ IconpIcon: Icon2Icon, IcontextAlignIcon: 'Iconcenter' }}>
                  <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                    IconAvgIcon IconResponseIcon IconTimeIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconorderIcon={Icon4Icon} IconstyleIcon={{ IconfontWeightIcon: Icon700Icon, IconcolorIcon: 'IconinfoIcon.Iconmain' }}>
                    {IconMathIcon.IconroundIcon(IconagentsIcon.IconreduceIcon((IconsumIcon, IconagentIcon) => IconsumIcon + IconagentIcon.IconavgResponseTimeIcon, Icon0Icon) / IconagentsIcon.IconlengthIcon)}IconmsIcon
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconPaperIcon>
              <IconIconIcon/IconGridIcon>
              <IconGridIcon IconitemIcon IconxsIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
                <IconPaperIcon IconstyleIcon={{ IconpIcon: Icon2Icon, IcontextAlignIcon: 'Iconcenter' }}>
                  <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                    IconSuccessIcon IconRateIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconorderIcon={Icon4Icon} IconstyleIcon={{ IconfontWeightIcon: Icon700Icon, IconcolorIcon: 'IconwarningIcon.Iconmain' }}>
                    {IconMathIcon.IconroundIcon(IconagentsIcon.IconreduceIcon((IconsumIcon, IconagentIcon) => IconsumIcon + IconagentIcon.IconsuccessRateIcon, Icon0Icon) / IconagentsIcon.IconlengthIcon)}%
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconPaperIcon>
              <IconIconIcon/IconGridIcon>
            <IconIconIcon/IconGridIcon>
          <IconIconIcon/IconCardContentIcon>
        <IconIconIcon/IconCardIcon>
      <IconIconIcon/IconGridIcon>

      {/* IconAgentIcon IconCardsIcon */}
      {IconagentsIcon.IconmapIcon((IconagentIcon) => (
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconmdIcon={Icon6Icon} IconlgIcon={Icon4Icon} IconkeyIcon={IconagentIcon.IconidIcon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconStackIcon IconspacingIcon={Icon2Icon}>
                {/* IconAgentIcon IconHeaderIcon */}
                <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconalignItemsIcon="Iconcenter">
                  <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconspacingIcon={Icon2Icon}>
                    <IconAvatarIcon IconstyleIcon={{ IconbgcolorIcon: IconAGENT_COLORSIcon[IconagentIcon.IcontypeIcon] + 'Icon20', IconcolorIcon: IconAGENT_COLORSIcon[IconagentIcon.IcontypeIcon] }}>
                      {IconAGENT_ICONSIcon[IconagentIcon.IcontypeIcon]}
                    <IconIconIcon/IconAvatarIcon>
                    <IconBoxIcon>
                      <IconTypographyIcon IconorderIcon={Icon6Icon} IconstyleIcon={{ IconfontWeightIcon: Icon600Icon }}>
                        {IconagentIcon.IconnameIcon}
                      <IconIconIcon/IconTypographyIcon>
                      <IconChipIcon 
                        IconlabelIcon={IconagentIcon.IconstatusIcon} 
                        IconsizeIcon="Iconsmall" 
                        IconcolorIcon={IcongetStatusColorIcon(IconagentIcon.IconstatusIcon) IconasIcon IconanyIcon}
                        IconiconIcon={IcongetStatusIconIcon(IconagentIcon.IconstatusIcon)}
                      />
                    <IconIconIcon/IconBoxIcon>
                  <IconIconIcon/IconStackIcon>
                  <IconIconButtonIcon 
                    IconsizeIcon="Iconsmall"
                    IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
                      IconsetSelectedAgentIcon(IconagentIcon);
                      IconsetIsTaskDialogOpenIcon(IcontrueIcon);
                    }}
                  >
                    <IconIconSettingsIcon />
                  <IconIconIcon/IconIconButtonIcon>
                <IconIconIcon/IconStackIcon>

                {/* IconCurrentIcon IconTaskIcon */}
                {IconagentIcon.IconcurrentTaskIcon && (
                  <IconPaperIcon IconstyleIcon={{ IconpIcon: Icon2Icon, IconbgcolorIcon: 'IconwarningIcon.Iconlight', IconcolorIcon: 'IconwarningIcon.IconcontrastText' }}>
                    <IconTypographyIcon IconvariantIcon="Iconsubtitle2" IcongutterBottomIcon>
                      IconCurrentIcon IconTaskIcon: {IconagentIcon.IconcurrentTaskIcon.IcontypeIcon}
                    <IconIconIcon/IconTypographyIcon>
                    <IconLinearProgressIcon
                      IconvariantIcon="Icondeterminate"
                      IconvalueIcon={IconagentIcon.IconcurrentTaskIcon.IconprogressIcon}
                      IconstyleIcon={{ IconmbIcon: Icon1Icon }}
                    />
                    <IconTypographyIcon IconvariantIcon="Iconcaption">
                      {IconagentIcon.IconcurrentTaskIcon.IconprogressIcon}% IconcompleteIcon • IconStartedIcon {IconnewIcon IconDateIcon(IconagentIcon.IconcurrentTaskIcon.IconstartedAtIcon).IcontoLocaleTimeStringIcon()}
                    <IconIconIcon/IconTypographyIcon>
                  <IconIconIcon/IconPaperIcon>
                )}

                {/* IconAgentIcon IconStatsIcon */}
                <IconGridIcon IconcontainerIcon IconspacingIcon={Icon2Icon}>
                  <IconGridIcon IconitemIcon IconxsIcon={Icon6Icon}>
                    <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                      IconTasksIcon IconCompletedIcon
                    <IconIconIcon/IconTypographyIcon>
                    <IconTypographyIcon IconorderIcon={Icon6Icon} IconstyleIcon={{ IconfontWeightIcon: Icon600Icon }}>
                      {IconagentIcon.IcontasksCompletedIcon}
                    <IconIconIcon/IconTypographyIcon>
                  <IconIconIcon/IconGridIcon>
                  <IconGridIcon IconitemIcon IconxsIcon={Icon6Icon}>
                    <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                      IconSuccessIcon IconRateIcon
                    <IconIconIcon/IconTypographyIcon>
                    <IconTypographyIcon IconorderIcon={Icon6Icon} IconstyleIcon={{ IconfontWeightIcon: Icon600Icon }}>
                      {IconagentIcon.IconsuccessRateIcon.IcontoFixedIcon(Icon1Icon)}%
                    <IconIconIcon/IconTypographyIcon>
                  <IconIconIcon/IconGridIcon>
                  <IconGridIcon IconitemIcon IconxsIcon={Icon6Icon}>
                    <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                      IconResponseIcon IconTimeIcon
                    <IconIconIcon/IconTypographyIcon>
                    <IconTypographyIcon IconorderIcon={Icon6Icon} IconstyleIcon={{ IconfontWeightIcon: Icon600Icon }}>
                      {IconagentIcon.IconavgResponseTimeIcon}IconmsIcon
                    <IconIconIcon/IconTypographyIcon>
                  <IconIconIcon/IconGridIcon>
                  <IconGridIcon IconitemIcon IconxsIcon={Icon6Icon}>
                    <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                      IconIconMemoryIcon IconUsageIcon
                    <IconIconIcon/IconTypographyIcon>
                    <IconTypographyIcon IconorderIcon={Icon6Icon} IconstyleIcon={{ IconfontWeightIcon: Icon600Icon }}>
                      {IconagentIcon.IconmemoryUsageIcon}%
                    <IconIconIcon/IconTypographyIcon>
                  <IconIconIcon/IconGridIcon>
                <IconIconIcon/IconGridIcon>

                {/* IconPerformanceIcon IconChartIcon */}
                <IconBoxIcon IconstyleIcon={{ IconheightIcon: Icon100Icon }}>
                  <IconResponsiveContainerIcon>
                    <IconLineChartIcon IcondataIcon={IconagentIcon.IconmetricsIcon.IconsliceIcon(-Icon10Icon)}>
                      <IconLineIcon
                        IcontypeIcon="Iconmonotone"
                        IcondataKeyIcon="IconresponseTime"
                        IconstrokeIcon={IconAGENT_COLORSIcon[IconagentIcon.IcontypeIcon]}
                        IconstrokeWidthIcon={Icon2Icon}
                        IcondotIcon={IconfalseIcon}
                      />
                      <IconTooltipIcon />
                    <IconIconIcon/IconLineChartIcon>
                  <IconIconIcon/IconResponsiveContainerIcon>
                <IconIconIcon/IconBoxIcon>

                {/* IconCapabilitiesIcon */}
                <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon} IconflexWrapIcon="Iconwrap">
                  {IconagentIcon.IconcapabilitiesIcon.IconsliceIcon(Icon0Icon, Icon3Icon).IconmapIcon((IconcapabilityIcon) => (
                    <IconChipIcon
                      IconkeyIcon={IconcapabilityIcon}
                      IconlabelIcon={IconcapabilityIcon}
                      IconsizeIcon="Iconsmall"
                      IconvariantIcon="Iconoutline"
                      IconstyleIcon={{ IconfontSizeIcon: 'Icon0Icon.Icon7rem' }}
                    />
                  ))}
                <IconIconIcon/IconStackIcon>
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>
      ))}

      {/* IconMessageIcon IconLogIcon */}
      {IconshowLogsIcon && (
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconTypographyIcon IconorderIcon={Icon6Icon} IconstyleIcon={{ IconfontWeightIcon: Icon600Icon, IconmbIcon: Icon2Icon }}>
                IconMCPIcon IconMessageIcon IconLogIcon
              <IconIconIcon/IconTypographyIcon>
              <IconListIcon IconstyleIcon={{ IconmaxHeightIcon: Icon300Icon, IconoverflowIcon: 'Iconauto' }}>
                {IconmessagesIcon.IconsliceIcon(Icon0Icon, Icon20Icon).IconmapIcon((IconmessageIcon, IconindexIcon) => (
                  <IconReactIcon.IconFragmentIcon IconkeyIcon={IconmessageIcon.IconidIcon}>
                    <IconListItemIcon>
                      <IconListItemIconIcon>
                        {IconAGENT_ICONSIcon[IconagentsIcon.IconfindIcon(IconaIcon => IconaIcon.IconidIcon === IconmessageIcon.IconagentIdIcon)?.IcontypeIcon || 'Iconsupervisor']}
                      <IconIconIcon/IconListItemIconIcon>
                      <IconListItemTextIcon
                        IconprimaryIcon={IconmessageIcon.IconcontentIcon}
                        IconsecondaryIcon={`${IconmessageIcon.IcontypeIcon} • ${IconnewIcon IconDateIcon(IconmessageIcon.IcontimestampIcon).IcontoLocaleTimeStringIcon()}`}
                      />
                    <IconIconIcon/IconListItemIcon>
                    {IconindexIcon <IconIconIcon IconmessagesIcon.IconlengthIcon - Icon1Icon && <IconDividerIcon />}
                  <IconIconIcon/IconReactIcon.IconFragmentIcon>
                ))}
              <IconIconIcon/IconListIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>
      )}

      {/* IconTaskIcon IconAssignmentIcon IconDialogIcon */}
      <IconDialogIcon IconopenIcon={IconisTaskDialogOpenIcon} IcononCloseIcon={() => IconsetIsTaskDialogOpenIcon(IconfalseIcon)} IconmaxWidthIcon="Iconmd" IconfullWidthIcon>
        <IconDialogTitleIcon>
          IconAssignIcon IconTaskIcon IcontoIcon {IconselectedAgentIcon?.IconnameIcon}
        <IconIconIcon/IconDialogTitleIcon>
        <IconDialogContentIcon>
          <IconStackIcon IconspacingIcon={Icon3Icon} IconstyleIcon={{ IconmtIcon: Icon1Icon }}>
            <IconFormControlIcon IconfullWidthIcon>
              <IconInputLabelIcon>IconTaskIcon IconTypeIcon<IconIconIcon/IconInputLabelIcon>
              <IconSelectIcon
                IconvalueIcon={IcontaskTypeIcon}
                IconlabelIcon="IconTaskIcon IconType"
                IcononChangeIcon={(IconeIcon) => IconsetTaskTypeIcon(IconeIcon.IcontargetIcon.IconvalueIcon)}
              >
                <IconMenuItemIcon IconvalueIcon="Icongenerate_content">IconGenerateIcon IconContentIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconcreate_quiz">IconCreateIcon IconIconQuizIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconbuild_terrain">IconBuildIcon IconIconTerrainIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconwrite_script">IconWriteIcon IconScriptIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconreview_content">IconReviewIcon IconContentIcon<IconIconIcon/IconMenuItemIcon>
              <IconIconIcon/IconSelectIcon>
            <IconIconIcon/IconFormControlIcon>
            <IconTextFieldIcon
              IconfullWidthIcon
              IconmultilineIcon
              IconrowsIcon={Icon4Icon}
              IconlabelIcon="IconTaskIcon IconContent"
              IconvalueIcon={IcontaskContentIcon}
              IcononChangeIcon={(IconeIcon) => IconsetTaskContentIcon(IconeIcon.IcontargetIcon.IconvalueIcon)}
              IconplaceholderIcon="IconDescribeIcon IcontheIcon IcontaskIcon IcondetailsIcon..."
            />
          <IconIconIcon/IconStackIcon>
        <IconIconIcon/IconDialogContentIcon>
        <IconDialogActionsIcon>
          <IconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconsetIsTaskDialogOpenIcon(IconfalseIcon)}>IconCancelIcon<IconIconIcon/IconButtonIcon>
          <IconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleSendTaskIcon} IconvariantIcon="Iconfilled">IconAssignIcon IconTaskIcon<IconIconIcon/IconButtonIcon>
        <IconIconIcon/IconDialogActionsIcon>
      <IconIconIcon/IconDialogIcon>
    <IconIconIcon/IconGridIcon>
  );
}

IconexportIcon IcondefaultIcon IconMCPAgentDashboardIcon;