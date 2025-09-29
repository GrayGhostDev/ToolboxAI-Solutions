IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../../IconutilsIcon/IconmuiIcon-Iconimports';
IconimportIcon * IconasIcon IconReactIcon IconfromIcon "Iconreact";

IconimportIcon { IconuseStateIcon, IconuseEffectIcon } IconfromIcon "Iconreact";
IconimportIcon {
  IconIconPlayerPlayIcon,
  IconIconPlayerPauseIcon,
  IconIconSkipNextIcon,
  IconIconSkipPreviousIcon,
  IconIconReplayIcon,
  IconIconVolumeIcon,
  IconIconFullscreenIcon,
  IconIconSpeedIcon,
  IconIconEmojiEventsIcon,
  IconIconStarsIcon,
  IconIconTrendingUpIcon,
  IconIconSchoolIcon,
  IconIconClockIcon,
  IconIconCircleCheckIcon,
  IconIconAlertTriangleIcon,
  IconIconSportsEsportsIcon,
  IconIconTimelineIcon,
  IconIconInsightsIcon,
  IconIconDownloadIcon,
  IconIconShareIcon,
  IconIconCalendarIcon,
} IconfromIcon "@IconmuiIcon/IconiconsIcon-Iconmaterial";
IconimportIcon { IconDatePickerIcon } IconfromIcon "@IconmuiIcon/IconxIcon-IcondateIcon-IconpickersIcon/IconDatePicker";
IconimportIcon { IconLocalizationProviderIcon } IconfromIcon "@IconmuiIcon/IconxIcon-IcondateIcon-IconpickersIcon/IconLocalizationProvider";
IconimportIcon { IconAdapterDateFnsIcon } IconfromIcon "@IconmuiIcon/IconxIcon-IcondateIcon-IconpickersIcon/IconAdapterDateFns";
IconimportIcon { IconuseAppSelectorIcon } IconfromIcon "../../Iconstore";
IconimportIcon { IconIconIcon, IconIconAlertTriangleIcon, IconIconCalendarIcon, IconIconCircleCheckIcon, IconIconClockIcon, IconIconDownloadIcon, IconIconEmojiEventsIcon, IconIconFullscreenIcon, IconIconInsightsIcon, IconIconPlayerPauseIcon, IconIconPlayerPlayIcon, IconIconReplayIcon, IconIconSchoolIcon, IconIconShareIcon, IconIconSkipNextIcon, IconIconSkipPreviousIcon, IconIconSpeedIcon, IconIconSportsEsportsIcon, IconIconStarsIcon, IconIconTimelineIcon, IconIconTrendingUpIcon, IconIconVolumeIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';

IconinterfaceIcon IconGameplaySessionIcon {
  IconidIcon: IconstringIcon;
  IconstudentNameIcon: IconstringIcon;
  IconstudentAvatarIcon: IconstringIcon;
  IconworldNameIcon: IconstringIcon;
  IconworldThumbnailIcon: IconstringIcon;
  IcondateIcon: IconDateIcon;
  IcondurationIcon: IconnumberIcon; // IconinIcon IconsecondsIcon
  IconhighlightsIcon: IconHighlightIcon[];
  IconachievementsIcon: IconAchievementIcon[];
  IconinteractionsIcon: IconInteractionIcon[];
  IconprogressIcon: IconProgressPointIcon[];
  IconoverallScoreIcon: IconnumberIcon;
  IconxpEarnedIcon: IconnumberIcon;
  IconmasteryConceptsIcon: IconstringIcon[];
}

IconinterfaceIcon IconHighlightIcon {
  IconidIcon: IconstringIcon;
  IcontimestampIcon: IconnumberIcon; // IconsecondsIcon IconfromIcon IconstartIcon
  IcontypeIcon: "Iconachievement" | "Iconmilestone" | "Iconstruggle" | "Iconbreakthrough" | "Iconcollaboration";
  IcontitleIcon: IconstringIcon;
  IcondescriptionIcon: IconstringIcon;
  IconthumbnailUrlIcon?: IconstringIcon;
  IconimportanceIcon: "Iconlow" | "Iconmedium" | "Iconhigh";
}

IconinterfaceIcon IconAchievementIcon {
  IconidIcon: IconstringIcon;
  IconnameIcon: IconstringIcon;
  IconiconIcon: IconstringIcon;
  IcontimestampIcon: IconnumberIcon;
  IconxpRewardIcon: IconnumberIcon;
}

IconinterfaceIcon IconInteractionIcon {
  IconidIcon: IconstringIcon;
  IcontypeIcon: "Iconnpc_dialogue" | "Iconpuzzle_solve" | "Iconquiz_complete" | "Iconpeer_help";
  IcontimestampIcon: IconnumberIcon;
  IcondetailsIcon: IconstringIcon;
  IconoutcomeIcon: "Iconsuccess" | "Iconpartial" | "Iconretry";
}

IconinterfaceIcon IconProgressPointIcon {
  IcontimestampIcon: IconnumberIcon;
  IconconceptIcon: IconstringIcon;
  IconmasteryIcon: IconnumberIcon; // Icon0Icon-Icon100Icon
}

IconexportIcon IcondefaultIcon IconfunctionIcon IconGameplayReplayIcon() {
  IconconstIcon IconuserIcon = IconuseAppSelectorIcon((IconsIcon) => IconsIcon.IconuserIcon);
  IconconstIcon [IconselectedChildIcon, IconsetSelectedChildIcon] = IconuseStateIcon<IconstringIcon>("");
  IconconstIcon [IconselectedDateIcon, IconsetSelectedDateIcon] = IconuseStateIcon<IconDateIcon>(IconnewIcon IconDateIcon());
  IconconstIcon [IconsessionsIcon, IconsetSessionsIcon] = IconuseStateIcon<IconGameplaySessionIcon[]>([]);
  IconconstIcon [IconcurrentSessionIcon, IconsetCurrentSessionIcon] = IconuseStateIcon<IconGameplaySessionIcon | IconnullIcon>(IconnullIcon);
  IconconstIcon [IconisPlayingIcon, IconsetIsPlayingIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconcurrentTimeIcon, IconsetCurrentTimeIcon] = IconuseStateIcon(Icon0Icon);
  IconconstIcon [IconplaybackSpeedIcon, IconsetPlaybackSpeedIcon] = IconuseStateIcon(Icon1Icon);
  IconconstIcon [IconactiveTabIcon, IconsetActiveTabIcon] = IconuseStateIcon(Icon0Icon);
  IconconstIcon [IconselectedHighlightIcon, IconsetSelectedHighlightIcon] = IconuseStateIcon<IconstringIcon | IconnullIcon>(IconnullIcon);

  // IconMockIcon IcondataIcon IconforIcon IconchildrenIcon (IconinIcon IconrealIcon IconappIcon, IconfetchIcon IconfromIcon IconAPIIcon)
  IconconstIcon IconchildrenIcon = [
    { IconidIcon: "Icon1", IconnameIcon: "IconEmmaIcon IconJohnson", IconavatarIcon: "", IcongradeIcon: Icon5Icon },
    { IconidIcon: "Icon2", IconnameIcon: "IconAlexIcon IconJohnson", IconavatarIcon: "", IcongradeIcon: Icon3Icon },
  ];

  // IconLoadIcon IconmockIcon IconsessionsIcon
  IconuseEffectIcon(() => {
    // IconMockIcon IcongameplayIcon IconsessionsIcon
    IconconstIcon IconmockSessionsIcon: IconGameplaySessionIcon[] = [
      {
        IconidIcon: "Icon1",
        IconstudentNameIcon: "IconEmmaIcon IconJohnson",
        IconstudentAvatarIcon: "",
        IconworldNameIcon: "IconMathIcon IconAdventureIcon IconIsland",
        IconworldThumbnailIcon: "",
        IcondateIcon: IconnewIcon IconDateIcon(),
        IcondurationIcon: Icon1800Icon, // Icon30Icon IconminutesIcon
        IconhighlightsIcon: [
          {
            IconidIcon: "Iconh1",
            IcontimestampIcon: Icon120Icon,
            IcontypeIcon: "Iconachievement",
            IcontitleIcon: "IconFirstIcon IconPuzzleIcon IconSolvedIcon!",
            IcondescriptionIcon: "IconEmmaIcon IconsolvedIcon IcontheIcon IconfractionIcon IconpuzzleIcon IcononIcon IconherIcon IconfirstIcon Icontry",
            IconimportanceIcon: "Iconhigh",
          },
          {
            IconidIcon: "Iconh2",
            IcontimestampIcon: Icon450Icon,
            IcontypeIcon: "Iconbreakthrough",
            IcontitleIcon: "IconMasteredIcon IconMultiplication",
            IcondescriptionIcon: "IconCompletedIcon IconallIcon IconmultiplicationIcon IconchallengesIcon IconwithIcon Icon100Icon% Iconaccuracy",
            IconimportanceIcon: "Iconhigh",
          },
          {
            IconidIcon: "Iconh3",
            IcontimestampIcon: Icon780Icon,
            IcontypeIcon: "Iconcollaboration",
            IcontitleIcon: "IconHelpedIcon IconaIcon IconClassmate",
            IcondescriptionIcon: "IconEmmaIcon IconassistedIcon IconanotherIcon IconstudentIcon IconwithIcon IconaIcon IcondifficultIcon Iconproblem",
            IconimportanceIcon: "Iconmedium",
          },
          {
            IconidIcon: "Iconh4",
            IcontimestampIcon: Icon1200Icon,
            IcontypeIcon: "Iconstruggle",
            IcontitleIcon: "IconDivisionIcon IconChallenge",
            IcondescriptionIcon: "IconTookIcon Icon3Icon IconattemptsIcon IconbutIcon IconperseveredIcon IconthroughIcon IcontheIcon IcondivisionIcon Iconsection",
            IconimportanceIcon: "Iconmedium",
          },
          {
            IconidIcon: "Iconh5",
            IcontimestampIcon: Icon1650Icon,
            IcontypeIcon: "Iconmilestone",
            IcontitleIcon: "IconLevelIcon IconCompleteIcon!",
            IcondescriptionIcon: "IconFinishedIcon IconLevelIcon Icon3Icon IconwithIcon IconaIcon IconscoreIcon IconofIcon Icon95Icon%",
            IconimportanceIcon: "Iconhigh",
          },
        ],
        IconachievementsIcon: [
          { IconidIcon: "Icona1", IconnameIcon: "IconProblemIcon IconSolver", IconiconIcon: "🧩", IcontimestampIcon: Icon120Icon, IconxpRewardIcon: Icon50Icon },
          { IconidIcon: "Icona2", IconnameIcon: "IconMathIcon IconMaster", IconiconIcon: "🎓", IcontimestampIcon: Icon450Icon, IconxpRewardIcon: Icon100Icon },
          { IconidIcon: "Icona3", IconnameIcon: "IconTeamIcon IconPlayer", IconiconIcon: "🤝", IcontimestampIcon: Icon780Icon, IconxpRewardIcon: Icon75Icon },
        ],
        IconinteractionsIcon: [
          {
            IconidIcon: "Iconi1",
            IcontypeIcon: "Iconnpc_dialogue",
            IcontimestampIcon: Icon60Icon,
            IcondetailsIcon: "IconSpokeIcon IconwithIcon IconProfessorIcon IconMathIcon IconaboutIcon Iconfractions",
            IconoutcomeIcon: "Iconsuccess",
          },
          {
            IconidIcon: "Iconi2",
            IcontypeIcon: "Iconpuzzle_solve",
            IcontimestampIcon: Icon120Icon,
            IcondetailsIcon: "IconFractionIcon IconpuzzleIcon Iconcompleted",
            IconoutcomeIcon: "Iconsuccess",
          },
          {
            IconidIcon: "Iconi3",
            IcontypeIcon: "Iconquiz_complete",
            IcontimestampIcon: Icon900Icon,
            IcondetailsIcon: "IconMidIcon-IconlevelIcon IconquizIcon: Icon9Icon/Icon10Icon Iconcorrect",
            IconoutcomeIcon: "Iconsuccess",
          },
          {
            IconidIcon: "Iconi4",
            IcontypeIcon: "Iconpeer_help",
            IcontimestampIcon: Icon780Icon,
            IcondetailsIcon: "IconHelpedIcon IconAlexIcon IconwithIcon Iconmultiplication",
            IconoutcomeIcon: "Iconsuccess",
          },
        ],
        IconprogressIcon: [
          { IcontimestampIcon: Icon0Icon, IconconceptIcon: "IconFractions", IconmasteryIcon: Icon60Icon },
          { IcontimestampIcon: Icon300Icon, IconconceptIcon: "IconFractions", IconmasteryIcon: Icon75Icon },
          { IcontimestampIcon: Icon600Icon, IconconceptIcon: "IconMultiplication", IconmasteryIcon: Icon80Icon },
          { IcontimestampIcon: Icon900Icon, IconconceptIcon: "IconMultiplication", IconmasteryIcon: Icon95Icon },
          { IcontimestampIcon: Icon1200Icon, IconconceptIcon: "IconDivision", IconmasteryIcon: Icon70Icon },
          { IcontimestampIcon: Icon1500Icon, IconconceptIcon: "IconDivision", IconmasteryIcon: Icon85Icon },
        ],
        IconoverallScoreIcon: Icon95Icon,
        IconxpEarnedIcon: Icon225Icon,
        IconmasteryConceptsIcon: ["IconFractions", "IconMultiplication", "IconProblemIcon IconSolving"],
      },
      {
        IconidIcon: "Icon2",
        IconstudentNameIcon: "IconEmmaIcon IconJohnson",
        IconstudentAvatarIcon: "",
        IconworldNameIcon: "IconScienceIcon IconLaboratory",
        IconworldThumbnailIcon: "",
        IcondateIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon86400000Icon), // IconYesterdayIcon
        IcondurationIcon: Icon2400Icon, // Icon40Icon IconminutesIcon
        IconhighlightsIcon: [
          {
            IconidIcon: "Iconh6",
            IcontimestampIcon: Icon180Icon,
            IcontypeIcon: "Iconachievement",
            IcontitleIcon: "IconExperimentIcon IconSuccessIcon!",
            IcondescriptionIcon: "IconCompletedIcon IcontheIcon IconchemicalIcon IconreactionIcon IconexperimentIcon Iconperfectly",
            IconimportanceIcon: "Iconhigh",
          },
        ],
        IconachievementsIcon: [
          { IconidIcon: "Icona4", IconnameIcon: "IconScientist", IconiconIcon: "🔬", IcontimestampIcon: Icon180Icon, IconxpRewardIcon: Icon75Icon },
        ],
        IconinteractionsIcon: [
          {
            IconidIcon: "Iconi5",
            IcontypeIcon: "Iconnpc_dialogue",
            IcontimestampIcon: Icon100Icon,
            IcondetailsIcon: "IconLearnedIcon IconaboutIcon IconchemicalIcon IconreactionsIcon IconfromIcon IconDrIcon. IconScience",
            IconoutcomeIcon: "Iconsuccess",
          },
        ],
        IconprogressIcon: [
          { IcontimestampIcon: Icon0Icon, IconconceptIcon: "IconChemistry", IconmasteryIcon: Icon50Icon },
          { IcontimestampIcon: Icon1200Icon, IconconceptIcon: "IconChemistry", IconmasteryIcon: Icon85Icon },
        ],
        IconoverallScoreIcon: Icon88Icon,
        IconxpEarnedIcon: Icon175Icon,
        IconmasteryConceptsIcon: ["IconChemistry", "IconScientificIcon IconMethod"],
      },
    ];

    IconsetSessionsIcon(IconmockSessionsIcon);
    IconifIcon (IconmockSessionsIcon.IconlengthIcon > Icon0Icon) {
      IconsetCurrentSessionIcon(IconmockSessionsIcon[Icon0Icon]);
    }
  }, [IconselectedChildIcon, IconselectedDateIcon]);

  IconconstIcon IconformatTimeIcon = (IconsecondsIcon: IconnumberIcon): IconstringIcon => {
    IconconstIcon IconminsIcon = IconMathIcon.IconfloorIcon(IconsecondsIcon / Icon60Icon);
    IconconstIcon IconsecsIcon = IconMathIcon.IconfloorIcon(IconsecondsIcon % Icon60Icon);
    IconreturnIcon `${IconminsIcon}:${IconsecsIcon.IcontoStringIcon().IconpadStartIcon(Icon2Icon, "Icon0")}`;
  };

  IconconstIcon IconhandlePlayPauseIcon = () => {
    IconsetIsPlayingIcon(!IconisPlayingIcon);
  };

  IconconstIcon IconhandleSeekIcon = (IconnewTimeIcon: IconnumberIcon) => {
    IconsetCurrentTimeIcon(IconnewTimeIcon);
  };

  IconconstIcon IconjumpToHighlightIcon = (IcontimestampIcon: IconnumberIcon) => {
    IconsetCurrentTimeIcon(IcontimestampIcon);
    IconsetIsPlayingIcon(IcontrueIcon);
  };

  IconconstIcon IcongetHighlightIconIcon = (IcontypeIcon: IconHighlightIcon["Icontype"]) => {
    IconswitchIcon (IcontypeIcon) {
      IconcaseIcon "Iconachievement":
        IconreturnIcon <IconIconEmojiEventsIcon IconcolorIcon="Iconyellow" />;
      IconcaseIcon "Iconmilestone":
        IconreturnIcon <IconIconStarsIcon IconcolorIcon="Iconblue" />;
      IconcaseIcon "Iconbreakthrough":
        IconreturnIcon <IconIconTrendingUpIcon IconcolorIcon="Icongreen" />;
      IconcaseIcon "Iconstruggle":
        IconreturnIcon <IconIconAlertTriangleIcon IconcolorIcon="Iconred" />;
      IconcaseIcon "Iconcollaboration":
        IconreturnIcon <IconIconSchoolIcon IconcolorIcon="Icongray" />;
      IcondefaultIcon:
        IconreturnIcon <IconIconCircleCheckIcon />;
    }
  };

  // IconSimulateIcon IconplaybackIcon
  IconuseEffectIcon(() => {
    IconifIcon (IconisPlayingIcon && IconcurrentSessionIcon && IconcurrentTimeIcon <IconIconIcon IconcurrentSessionIcon.IcondurationIcon) {
      IconconstIcon IcontimerIcon = IconsetTimeoutIcon(() => {
        IconsetCurrentTimeIcon((IconprevIcon) => IconMathIcon.IconminIcon(IconprevIcon + IconplaybackSpeedIcon, IconcurrentSessionIcon.IcondurationIcon));
      }, Icon1000Icon / IconplaybackSpeedIcon);
      IconreturnIcon () => IconclearTimeoutIcon(IcontimerIcon);
    } IconelseIcon IconifIcon (IconcurrentTimeIcon >= (IconcurrentSessionIcon?.IcondurationIcon || Icon0Icon)) {
      IconsetIsPlayingIcon(IconfalseIcon);
    }
  }, [IconisPlayingIcon, IconcurrentTimeIcon, IconplaybackSpeedIcon, IconcurrentSessionIcon]);

  IconifIcon (!IconcurrentSessionIcon) {
    IconreturnIcon (
      <IconBoxIcon>
        <IconTypographyIcon IconorderIcon={Icon4Icon} IconstyleIcon={{ IconmbIcon: Icon3Icon }}>
          IconGameplayIcon IconIconReplayIcon
        <IconIconIcon/IconTypographyIcon>
        <IconAlertIcon IconseverityIcon="Iconinfo">
          IconSelectIcon IconaIcon IconchildIcon IconandIcon IcondateIcon IcontoIcon IconviewIcon IcontheirIcon IcongameplayIcon IconsessionsIcon
        <IconIconIcon/IconAlertIcon>
      <IconIconIcon/IconBoxIcon>
    );
  }

  IconreturnIcon (
    <IconBoxIcon>
      <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconalignItemsIcon="Iconcenter" IconmbIcon={Icon3Icon}>
        <IconTypographyIcon IconorderIcon={Icon4Icon} IconstyleIcon={{ IconfontWeightIcon: Icon600Icon }}>
          IconGameplayIcon IconIconReplayIcon
        <IconIconIcon/IconTypographyIcon>
        <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon}>
          <IconFormControlIcon IconsizeIcon="Iconsmall" IconstyleIcon={{ IconminWidthIcon: Icon150Icon }}>
            <IconInputLabelIcon>IconSelectIcon IconChildIcon<IconIconIcon/IconInputLabelIcon>
            <IconSelectIcon
              IconvalueIcon={IconselectedChildIcon}
              IcononChangeIcon={(IconeIcon) => IconsetSelectedChildIcon(IconeIcon.IcontargetIcon.IconvalueIcon)}
              IconlabelIcon="IconSelectIcon IconChild"
            >
              {IconchildrenIcon.IconmapIcon((IconchildIcon) => (
                <IconMenuItemIcon IconkeyIcon={IconchildIcon.IconidIcon} IconvalueIcon={IconchildIcon.IconidIcon}>
                  {IconchildIcon.IconnameIcon}
                <IconIconIcon/IconMenuItemIcon>
              ))}
            <IconIconIcon/IconSelectIcon>
          <IconIconIcon/IconFormControlIcon>
          <IconLocalizationProviderIcon IcondateAdapterIcon={IconAdapterDateFnsIcon}>
            <IconDatePickerIcon
              IconlabelIcon="IconSelectIcon IconDate"
              IconvalueIcon={IconselectedDateIcon}
              IcononChangeIcon={(IconnewDateIcon) => IconnewDateIcon && IconsetSelectedDateIcon(IconnewDateIcon)}
              IconslotPropsIcon={{ IcontextFieldIcon: { IconsizeIcon: "Iconsmall" } }}
            />
          <IconIconIcon/IconLocalizationProviderIcon>
        <IconIconIcon/IconStackIcon>
      <IconIconIcon/IconStackIcon>

      <IconGrid2Icon IconcontainerIcon IconspacingIcon={Icon3Icon}>
        {/* IconVideoIcon IconPlayerIcon IconAreaIcon */}
        <IconGrid2Icon IconxsIcon={Icon12Icon} IconlgIcon={Icon8Icon}>
          <IconCardIcon>
            <IconBoxIcon
              IconstyleIcon={{
                IconpositionIcon: "Iconrelative",
                IconpaddingTopIcon: "Icon56Icon.Icon25Icon%", // Icon16Icon:Icon9Icon IconaspectIcon IconratioIcon
                IconbgcolorIcon: "Iconblack",
                IconborderRadiusIcon: Icon1Icon,
                IconoverflowIcon: "Iconhidden",
              }}
            >
              {/* IconIconReplayIcon IconVisualizationIcon */}
              <IconBoxIcon
                IconstyleIcon={{
                  IconpositionIcon: "Iconabsolute",
                  IcontopIcon: Icon0Icon,
                  IconleftIcon: Icon0Icon,
                  IconrightIcon: Icon0Icon,
                  IconbottomIcon: Icon0Icon,
                  IcondisplayIcon: "Iconflex",
                  IconalignItemsIcon: "Iconcenter",
                  IconjustifyContentIcon: "Iconcenter",
                  IconbackgroundIcon: `IconlinearIcon-IcongradientIcon(Icon135degIcon, #Icon667eeaIcon Icon0Icon%, #Icon764ba2Icon Icon100Icon%)`,
                }}
              >
                <IconStackIcon IconalignItemsIcon="Iconcenter" IconspacingIcon={Icon2Icon}>
                  <IconIconSportsEsportsIcon IconstyleIcon={{ IconfontSizeIcon: Icon80Icon, IconcolorIcon: "Iconwhite", IconopacityIcon: Icon0Icon.Icon8Icon }} />
                  <IconTypographyIcon IconorderIcon={Icon5Icon} IconcolorIcon="Iconwhite">
                    {IconcurrentSessionIcon.IconworldNameIcon}
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconsizeIcon="Iconmd" IconcolorIcon="Iconwhite" IconstyleIcon={{ IconopacityIcon: Icon0Icon.Icon9Icon }}>
                    {IconformatTimeIcon(IconcurrentTimeIcon)} / {IconformatTimeIcon(IconcurrentSessionIcon.IcondurationIcon)}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconStackIcon>
              <IconIconIcon/IconBoxIcon>

              {/* IconHighlightIcon IconMarkersIcon IcononIcon IconIconTimelineIcon */}
              <IconBoxIcon
                IconstyleIcon={{
                  IconpositionIcon: "Iconabsolute",
                  IconbottomIcon: Icon80Icon,
                  IconleftIcon: Icon0Icon,
                  IconrightIcon: Icon0Icon,
                  IconheightIcon: Icon4Icon,
                  IconbgcolorIcon: "IconrgbaIcon(Icon255Icon,Icon255Icon,Icon255Icon,Icon0Icon.Icon3Icon)",
                }}
              >
                {IconcurrentSessionIcon.IconhighlightsIcon.IconmapIcon((IconhighlightIcon) => (
                  <IconBoxIcon
                    IconkeyIcon={IconhighlightIcon.IconidIcon}
                    IconstyleIcon={{
                      IconpositionIcon: "Iconabsolute",
                      IconleftIcon: `${(IconhighlightIcon.IcontimestampIcon / IconcurrentSessionIcon.IcondurationIcon) * Icon100Icon}%`,
                      IcontopIcon: -Icon6Icon,
                      IconwidthIcon: Icon16Icon,
                      IconheightIcon: Icon16Icon,
                      IconborderRadiusIcon: "Icon50Icon%",
                      IconbgcolorIcon:
                        IconhighlightIcon.IconimportanceIcon === "Iconhigh"
                          ? "IconwarningIcon.Iconmain"
                          : IconhighlightIcon.IconimportanceIcon === "Iconmedium"
                          ? "IconinfoIcon.Iconmain"
                          : "IcongreyIcon.Icon500",
                      IconcursorIcon: "Iconpointer",
                      "&:Iconhover": {
                        IcontransformIcon: "IconscaleIcon(Icon1Icon.Icon3Icon)",
                      },
                    }}
                    IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconjumpToHighlightIcon(IconhighlightIcon.IcontimestampIcon)}
                  />
                ))}
              <IconIconIcon/IconBoxIcon>
            <IconIconIcon/IconBoxIcon>

            {/* IconPlayerIcon IconControlsIcon */}
            <IconCardContentIcon>
              <IconStackIcon IconspacingIcon={Icon2Icon}>
                <IconSliderIcon
                  IconvalueIcon={IconcurrentTimeIcon}
                  IconmaxIcon={IconcurrentSessionIcon.IcondurationIcon}
                  IcononChangeIcon={(Icon_Icon, IconvalueIcon) => IconhandleSeekIcon(IconvalueIcon IconasIcon IconnumberIcon)}
                  IconstyleIcon={{ IconwidthIcon: "Icon100Icon%" }}
                />
                <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconjustifyContentIcon="Iconcenter" IconspacingIcon={Icon2Icon}>
                  <IconIconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconhandleSeekIcon(IconMathIcon.IconmaxIcon(Icon0Icon, IconcurrentTimeIcon - Icon30Icon))}>
                    <IconIconSkipPreviousIcon />
                  <IconIconIcon/IconIconButtonIcon>
                  <IconIconButtonIcon
                    IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandlePlayPauseIcon}
                    IconstyleIcon={{
                      IconbgcolorIcon: "IconprimaryIcon.Iconmain",
                      IconcolorIcon: "Iconwhite",
                      "&:Iconhover": { IconbgcolorIcon: "IconprimaryIcon.Icondark" },
                    }}
                  >
                    {IconisPlayingIcon ? <IconIconPlayerPauseIcon /> : <IconIconPlayerPlayIcon />}
                  <IconIconIcon/IconIconButtonIcon>
                  <IconIconButtonIcon
                    IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconhandleSeekIcon(IconMathIcon.IconminIcon(IconcurrentSessionIcon.IcondurationIcon, IconcurrentTimeIcon + Icon30Icon))}
                  >
                    <IconIconSkipNextIcon />
                  <IconIconIcon/IconIconButtonIcon>
                  <IconIconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconhandleSeekIcon(Icon0Icon)}>
                    <IconIconReplayIcon />
                  <IconIconIcon/IconIconButtonIcon>
                  <IconFormControlIcon IconsizeIcon="Iconsmall" IconstyleIcon={{ IconmlIcon: Icon2Icon, IconminWidthIcon: Icon80Icon }}>
                    <IconSelectIcon
                      IconvalueIcon={IconplaybackSpeedIcon}
                      IcononChangeIcon={(IconeIcon) => IconsetPlaybackSpeedIcon(IconNumberIcon(IconeIcon.IcontargetIcon.IconvalueIcon))}
                      IconsizeIcon="Iconsmall"
                    >
                      <IconMenuItemIcon IconvalueIcon={Icon0Icon.Icon5Icon}>Icon0Icon.Icon5xIcon<IconIconIcon/IconMenuItemIcon>
                      <IconMenuItemIcon IconvalueIcon={Icon1Icon}>Icon1xIcon<IconIconIcon/IconMenuItemIcon>
                      <IconMenuItemIcon IconvalueIcon={Icon1Icon.Icon5Icon}>Icon1Icon.Icon5xIcon<IconIconIcon/IconMenuItemIcon>
                      <IconMenuItemIcon IconvalueIcon={Icon2Icon}>Icon2xIcon<IconIconIcon/IconMenuItemIcon>
                    <IconIconIcon/IconSelectIcon>
                  <IconIconIcon/IconFormControlIcon>
                  <IconIconButtonIcon IconstyleIcon={{ IconmlIcon: "Iconauto" }}>
                    <IconIconDownloadIcon />
                  <IconIconIcon/IconIconButtonIcon>
                  <IconIconButtonIcon>
                    <IconIconShareIcon />
                  <IconIconIcon/IconIconButtonIcon>
                  <IconIconButtonIcon>
                    <IconIconFullscreenIcon />
                  <IconIconIcon/IconIconButtonIcon>
                <IconIconIcon/IconStackIcon>
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>

          {/* IconSessionIcon IconTabsIcon */}
          <IconCardIcon IconstyleIcon={{ IconmtIcon: Icon3Icon }}>
            <IconTabsIcon IconvalueIcon={IconactiveTabIcon} IcononChangeIcon={(Icon_Icon, IconvIcon) => IconsetActiveTabIcon(IconvIcon)}>
              <IconTabIcon IconlabelIcon="IconHighlights" />
              <IconTabIcon IconlabelIcon="IconProgress" />
              <IconTabIcon IconlabelIcon="IconInteractions" />
              <IconTabIcon IconlabelIcon="IconAchievements" />
            <IconIconIcon/IconTabsIcon>
            <IconCardContentIcon>
              {IconactiveTabIcon === Icon0Icon && (
                <IconListIcon>
                  {IconcurrentSessionIcon.IconhighlightsIcon.IconmapIcon((IconhighlightIcon) => (
                    <IconReactIcon.IconFragmentIcon IconkeyIcon={IconhighlightIcon.IconidIcon}>
                      <IconListItemButtonIcon
                        IconselectedIcon={IconselectedHighlightIcon === IconhighlightIcon.IconidIcon}
                        IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
                          IconsetSelectedHighlightIcon(IconhighlightIcon.IconidIcon);
                          IconjumpToHighlightIcon(IconhighlightIcon.IcontimestampIcon);
                        }}
                      >
                        <IconListItemIconIcon>{IcongetHighlightIconIcon(IconhighlightIcon.IcontypeIcon)}<IconIconIcon/IconListItemIconIcon>
                        <IconListItemTextIcon
                          IconprimaryIcon={IconhighlightIcon.IcontitleIcon}
                          IconsecondaryIcon={
                            <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon} IconalignItemsIcon="Iconcenter">
                              <IconTypographyIcon IconvariantIcon="Iconcaption">
                                {IconformatTimeIcon(IconhighlightIcon.IcontimestampIcon)}
                              <IconIconIcon/IconTypographyIcon>
                              <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                                • {IconhighlightIcon.IcondescriptionIcon}
                              <IconIconIcon/IconTypographyIcon>
                            <IconIconIcon/IconStackIcon>
                          }
                        />
                        <IconChipIcon
                          IconlabelIcon={IconhighlightIcon.IconimportanceIcon}
                          IconsizeIcon="Iconsmall"
                          IconcolorIcon={
                            IconhighlightIcon.IconimportanceIcon === "Iconhigh"
                              ? "Iconerror"
                              : IconhighlightIcon.IconimportanceIcon === "Iconmedium"
                              ? "Iconwarning"
                              : "Icondefault"
                          }
                        />
                      <IconIconIcon/IconListItemButtonIcon>
                      <IconDividerIcon />
                    <IconIconIcon/IconReactIcon.IconFragmentIcon>
                  ))}
                <IconIconIcon/IconListIcon>
              )}

              {IconactiveTabIcon === Icon1Icon && (
                <IconBoxIcon>
                  <IconTypographyIcon IconorderIcon={Icon6Icon} IconstyleIcon={{ IconmbIcon: Icon2Icon }}>
                    IconConceptIcon IconMasteryIcon IconProgressIcon
                  <IconIconIcon/IconTypographyIcon>
                  {IconArrayIcon.IconfromIcon(IconnewIcon IconSetIcon(IconcurrentSessionIcon.IconprogressIcon.IconmapIcon((IconpIcon) => IconpIcon.IconconceptIcon))).IconmapIcon(
                    (IconconceptIcon) => {
                      IconconstIcon IconconceptProgressIcon = IconcurrentSessionIcon.IconprogressIcon.IconfilterIcon(
                        (IconpIcon) => IconpIcon.IconconceptIcon === IconconceptIcon
                      );
                      IconconstIcon IconinitialIcon = IconconceptProgressIcon[Icon0Icon]?.IconmasteryIcon || Icon0Icon;
                      IconconstIcon IconfinalIcon = IconconceptProgressIcon[IconconceptProgressIcon.IconlengthIcon - Icon1Icon]?.IconmasteryIcon || Icon0Icon;
                      IconconstIcon IconimprovementIcon = IconfinalIcon - IconinitialIcon;

                      IconreturnIcon (
                        <IconBoxIcon IconkeyIcon={IconconceptIcon} IconstyleIcon={{ IconmbIcon: Icon2Icon }}>
                          <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconmbIcon={Icon1Icon}>
                            <IconTypographyIcon IconsizeIcon="Iconsm">{IconconceptIcon}<IconIconIcon/IconTypographyIcon>
                            <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon}>
                              <IconChipIcon
                                IconlabelIcon={`${IconfinalIcon}%`}
                                IconsizeIcon="Iconsmall"
                                IconcolorIcon={IconfinalIcon >= Icon80Icon ? "Iconsuccess" : "Icondefault"}
                              />
                              {IconimprovementIcon > Icon0Icon && (
                                <IconChipIcon
                                  IconlabelIcon={`+${IconimprovementIcon}%`}
                                  IconsizeIcon="Iconsmall"
                                  IconcolorIcon="Icongreen"
                                  IconvariantIcon="Iconoutline"
                                />
                              )}
                            <IconIconIcon/IconStackIcon>
                          <IconIconIcon/IconStackIcon>
                          <IconLinearProgressIcon IconvariantIcon="Icondeterminate" IconvalueIcon={IconfinalIcon} />
                        <IconIconIcon/IconBoxIcon>
                      );
                    }
                  )}
                <IconIconIcon/IconBoxIcon>
              )}

              {IconactiveTabIcon === Icon2Icon && (
                <IconListIcon>
                  {IconcurrentSessionIcon.IconinteractionsIcon.IconmapIcon((IconinteractionIcon) => (
                    <IconReactIcon.IconFragmentIcon IconkeyIcon={IconinteractionIcon.IconidIcon}>
                      <IconListItemIcon>
                        <IconListItemTextIcon
                          IconprimaryIcon={IconinteractionIcon.IcondetailsIcon}
                          IconsecondaryIcon={
                            <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon} IconalignItemsIcon="Iconcenter">
                              <IconTypographyIcon IconvariantIcon="Iconcaption">
                                {IconformatTimeIcon(IconinteractionIcon.IcontimestampIcon)}
                              <IconIconIcon/IconTypographyIcon>
                              <IconChipIcon
                                IconlabelIcon={IconinteractionIcon.IconoutcomeIcon}
                                IconsizeIcon="Iconsmall"
                                IconcolorIcon={IconinteractionIcon.IconoutcomeIcon === "Iconsuccess" ? "Iconsuccess" : "Iconwarning"}
                              />
                            <IconIconIcon/IconStackIcon>
                          }
                        />
                      <IconIconIcon/IconListItemIcon>
                      <IconDividerIcon />
                    <IconIconIcon/IconReactIcon.IconFragmentIcon>
                  ))}
                <IconIconIcon/IconListIcon>
              )}

              {IconactiveTabIcon === Icon3Icon && (
                <IconListIcon>
                  {IconcurrentSessionIcon.IconachievementsIcon.IconmapIcon((IconachievementIcon) => (
                    <IconReactIcon.IconFragmentIcon IconkeyIcon={IconachievementIcon.IconidIcon}>
                      <IconListItemIcon>
                        <IconListItemIconIcon>
                          <IconTypographyIcon IconorderIcon={Icon5Icon}>{IconachievementIcon.IconiconIcon}<IconIconIcon/IconTypographyIcon>
                        <IconIconIcon/IconListItemIconIcon>
                        <IconListItemTextIcon
                          IconprimaryIcon={IconachievementIcon.IconnameIcon}
                          IconsecondaryIcon={IconformatTimeIcon(IconachievementIcon.IcontimestampIcon)}
                        />
                        <IconChipIcon IconlabelIcon={`+${IconachievementIcon.IconxpRewardIcon} IconXPIcon`} IconcolorIcon="Iconblue" />
                      <IconIconIcon/IconListItemIcon>
                      <IconDividerIcon />
                    <IconIconIcon/IconReactIcon.IconFragmentIcon>
                  ))}
                <IconIconIcon/IconListIcon>
              )}
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGrid2Icon>

        {/* IconSessionIcon IconInfoIcon IconSidebarIcon */}
        <IconGrid2Icon IconxsIcon={Icon12Icon} IconlgIcon={Icon4Icon}>
          {/* IconSessionIcon IconOverviewIcon */}
          <IconCardIcon>
            <IconCardContentIcon>
              <IconTypographyIcon IconorderIcon={Icon6Icon} IconstyleIcon={{ IconmbIcon: Icon2Icon }}>
                IconSessionIcon IconOverviewIcon
              <IconIconIcon/IconTypographyIcon>
              <IconStackIcon IconspacingIcon={Icon2Icon}>
                <IconPaperIcon IconstyleIcon={{ IconpIcon: Icon2Icon, IconbgcolorIcon: "IconprimaryIcon.Icon50" }}>
                  <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconspacingIcon={Icon2Icon}>
                    <IconAvatarIcon IconsrcIcon={IconcurrentSessionIcon.IconstudentAvatarIcon}>
                      {IconcurrentSessionIcon.IconstudentNameIcon[Icon0Icon]}
                    <IconIconIcon/IconAvatarIcon>
                    <IconBoxIcon>
                      <IconTypographyIcon IconvariantIcon="Iconsubtitle2">
                        {IconcurrentSessionIcon.IconstudentNameIcon}
                      <IconIconIcon/IconTypographyIcon>
                      <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                        {IconcurrentSessionIcon.IcondateIcon.IcontoLocaleDateStringIcon()}
                      <IconIconIcon/IconTypographyIcon>
                    <IconIconIcon/IconBoxIcon>
                  <IconIconIcon/IconStackIcon>
                <IconIconIcon/IconPaperIcon>

                <IconStackIcon IconspacingIcon={Icon1Icon}>
                  <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                    <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
                      IconDurationIcon
                    <IconIconIcon/IconTypographyIcon>
                    <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon={Icon600Icon}>
                      {IconformatTimeIcon(IconcurrentSessionIcon.IcondurationIcon)}
                    <IconIconIcon/IconTypographyIcon>
                  <IconIconIcon/IconStackIcon>
                  <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                    <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
                      IconOverallIcon IconScoreIcon
                    <IconIconIcon/IconTypographyIcon>
                    <IconChipIcon
                      IconlabelIcon={`${IconcurrentSessionIcon.IconoverallScoreIcon}%`}
                      IconsizeIcon="Iconsmall"
                      IconcolorIcon={IconcurrentSessionIcon.IconoverallScoreIcon >= Icon90Icon ? "Iconsuccess" : "Iconprimary"}
                    />
                  <IconIconIcon/IconStackIcon>
                  <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                    <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
                      IconXPIcon IconEarnedIcon
                    <IconIconIcon/IconTypographyIcon>
                    <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon={Icon600Icon} IconcolorIcon="IconprimaryIcon.Iconmain">
                      +{IconcurrentSessionIcon.IconxpEarnedIcon} IconXPIcon
                    <IconIconIcon/IconTypographyIcon>
                  <IconIconIcon/IconStackIcon>
                  <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                    <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
                      IconAchievementsIcon
                    <IconIconIcon/IconTypographyIcon>
                    <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon={Icon600Icon}>
                      {IconcurrentSessionIcon.IconachievementsIcon.IconlengthIcon}
                    <IconIconIcon/IconTypographyIcon>
                  <IconIconIcon/IconStackIcon>
                <IconIconIcon/IconStackIcon>

                <IconDividerIcon />

                <IconBoxIcon>
                  <IconTypographyIcon IconvariantIcon="Iconsubtitle2" IconstyleIcon={{ IconmbIcon: Icon1Icon }}>
                    IconMasteredIcon IconConceptsIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon0Icon.Icon5Icon} IconflexWrapIcon="Iconwrap">
                    {IconcurrentSessionIcon.IconmasteryConceptsIcon.IconmapIcon((IconconceptIcon) => (
                      <IconChipIcon IconkeyIcon={IconconceptIcon} IconlabelIcon={IconconceptIcon} IconsizeIcon="Iconsmall" IconvariantIcon="Iconoutline" />
                    ))}
                  <IconIconIcon/IconStackIcon>
                <IconIconIcon/IconBoxIcon>
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>

          {/* IconOtherIcon IconSessionsIcon */}
          <IconCardIcon IconstyleIcon={{ IconmtIcon: Icon3Icon }}>
            <IconCardContentIcon>
              <IconTypographyIcon IconorderIcon={Icon6Icon} IconstyleIcon={{ IconmbIcon: Icon2Icon }}>
                IconOtherIcon IconSessionsIcon IconTodayIcon
              <IconIconIcon/IconTypographyIcon>
              <IconListIcon>
                {IconsessionsIcon.IconsliceIcon(Icon0Icon, Icon3Icon).IconmapIcon((IconsessionIcon) => (
                  <IconListItemButtonIcon
                    IconkeyIcon={IconsessionIcon.IconidIcon}
                    IconselectedIcon={IconsessionIcon.IconidIcon === IconcurrentSessionIcon.IconidIcon}
                    IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconsetCurrentSessionIcon(IconsessionIcon)}
                  >
                    <IconListItemIconIcon>
                      <IconIconSportsEsportsIcon />
                    <IconIconIcon/IconListItemIconIcon>
                    <IconListItemTextIcon
                      IconprimaryIcon={IconsessionIcon.IconworldNameIcon}
                      IconsecondaryIcon={`${IconformatTimeIcon(IconsessionIcon.IcondurationIcon)} • ${IconsessionIcon.IconxpEarnedIcon} IconXPIcon`}
                    />
                  <IconIconIcon/IconListItemButtonIcon>
                ))}
              <IconIconIcon/IconListIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>

          {/* IconIconInsightsIcon */}
          <IconCardIcon IconstyleIcon={{ IconmtIcon: Icon3Icon }}>
            <IconCardContentIcon>
              <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconspacingIcon={Icon1Icon} IconmbIcon={Icon2Icon}>
                <IconIconInsightsIcon />
                <IconTypographyIcon IconorderIcon={Icon6Icon}>IconAIIcon IconIconInsightsIcon<IconIconIcon/IconTypographyIcon>
              <IconIconIcon/IconStackIcon>
              <IconStackIcon IconspacingIcon={Icon2Icon}>
                <IconAlertIcon IconseverityIcon="Iconsuccess">
                  IconEmmaIcon IconshowedIcon IconexcellentIcon IconproblemIcon-IconsolvingIcon IconskillsIcon, IconparticularlyIcon IconinIcon IcontheIcon IconmultiplicationIcon
                  IconsectionIcon.
                <IconIconIcon/IconAlertIcon>
                <IconAlertIcon IconseverityIcon="Iconinfo">
                  IconConsiderIcon IconmoreIcon IcondivisionIcon IconpracticeIcon. IconEmmaIcon IconneededIcon IconmultipleIcon IconattemptsIcon IconbutIcon IconshowedIcon IcongoodIcon
                  IconperseveranceIcon.
                <IconIconIcon/IconAlertIcon>
                <IconAlertIcon IconseverityIcon="Iconwarning">
                  IconEmmaIcon IconspentIcon Icon5Icon IconminutesIcon IcononIcon IcononeIcon IconproblemIcon. IconThisIcon IconmightIcon IconindicateIcon IcontheIcon IconneedIcon IconforIcon IconadditionalIcon
                  IconsupportIcon IconinIcon IconthisIcon IconareaIcon.
                <IconIconIcon/IconAlertIcon>
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGrid2Icon>
      <IconIconIcon/IconGrid2Icon>
    <IconIconIcon/IconBoxIcon>
  );
}