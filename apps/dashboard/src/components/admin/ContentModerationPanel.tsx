IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../../IconutilsIcon/IconmuiIcon-Iconimports';
// @IcontsIcon-IconnocheckIcon - IconTemporaryIcon IconfixIcon IconforIcon IconPhaseIcon Icon3Icon
/**
 * IconContentModerationPanelIcon IconComponentIcon
 * IconContentIcon IconmoderationIcon IconandIcon IconreviewIcon IconinterfaceIcon IconforIcon IconadministratorsIcon
 */
IconimportIcon { IconmemoIcon, IconuseStateIcon, IconuseEffectIcon } IconfromIcon 'Iconreact';

IconimportIcon {
  IconSearchIcon IconasIcon IconIconSearchIcon,
  IconFilterListIcon IconasIcon IconIconFilterIcon,
  IconCheckIcon IconasIcon IconIconCheckIcon,
  IconCloseIcon IconasIcon IconIconXIcon,
  IconFlagIcon IconasIcon IconIconFlagIcon,
  IconVisibilityIcon IconasIcon IconIconEyeIcon,
  IconDeleteIcon IconasIcon IconIconTrashIcon,
  IconWarningIcon IconasIcon IconIconAlertTriangleIcon,
  IconInfoIcon IconasIcon IconIconInfoCircleIcon,
  IconSchoolIcon IconasIcon IconIconSchoolIcon,
  IconAssessmentIcon IconasIcon IconIconReportAnalyticsIcon,
  IconMessageIcon IconasIcon IconIconMessageCircleIcon,
  IconImageIcon IconasIcon IconIconImageIcon,
  IconVideoLibraryIcon IconasIcon IconIconVideoLibraryIcon,
  IconDescriptionIcon IconasIcon IconIconFileTextIcon,
  IconCodeIcon IconasIcon IconIconCodeIcon,
  IconReportIcon IconasIcon IconIconFlagIcon,
  IconGavelIcon IconasIcon IconIconGavelIcon,
  IconAutoAwesomeIcon IconasIcon IconIconAutoAwesomeIcon,
  IconThumbUpIcon IconasIcon IconIconThumbUpIcon,
  IconThumbDownIcon IconasIcon IconIconThumbDownIcon,
} IconfromIcon '@IconmuiIcon/IconiconsIcon-Iconmaterial';
IconimportIcon { IconformatIcon } IconfromIcon 'IcondateIcon-Iconfns';
IconimportIcon { IconusePusherIcon } IconfromIcon '@/IconhooksIcon/IconusePusher';
IconimportIcon { IconIconIcon, IconIconAlertTriangleIcon, IconIconAutoAwesomeIcon, IconIconCheckIcon, IconIconCodeIcon, IconIconEyeIcon, IconIconFileTextIcon, IconIconFilterIcon, IconIconFlagIcon, IconIconGavelIcon, IconIconImageIcon, IconIconInfoCircleIcon, IconIconMessageCircleIcon, IconIconReportAnalyticsIcon, IconIconSchoolIcon, IconIconSearchIcon, IconIconThumbDownIcon, IconIconThumbUpIcon, IconIconTrashIcon, IconIconVideoLibraryIcon, IconIconXIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';
IconexportIcon IcontypeIcon IconContentTypeIcon = 'Iconlesson' | 'Iconassessment' | 'Iconmessage' | 'Iconimage' | 'Iconvideo' | 'Icondocument' | 'Iconcode';
IconexportIcon IcontypeIcon IconContentStatusIcon = 'Iconpending' | 'Iconapproved' | 'Iconrejected' | 'Iconflagged' | 'Iconunder_review';
IconexportIcon IcontypeIcon IconModerationReasonIcon = 'Iconinappropriate' | 'Iconspam' | 'Iconcopyright' | 'Iconquality' | 'Iconpolicy_violation' | 'Iconother';
IconexportIcon IconinterfaceIcon IconContentItemIcon {
  IconidIcon: IconstringIcon;
  IcontypeIcon: IconContentTypeIcon;
  IcontitleIcon: IconstringIcon;
  IcondescriptionIcon?: IconstringIcon;
  IconcontentIcon?: IconstringIcon;
  IconauthorIcon: {
    IconidIcon: IconstringIcon;
    IconnameIcon: IconstringIcon;
    IconroleIcon: IconstringIcon;
    IconavatarIcon?: IconstringIcon;
  };
  IconstatusIcon: IconContentStatusIcon;
  IconcreatedAtIcon: IconstringIcon;
  IconreviewedAtIcon?: IconstringIcon;
  IconreviewedByIcon?: {
    IconidIcon: IconstringIcon;
    IconnameIcon: IconstringIcon;
  };
  IconflagsIcon: IconnumberIcon;
  IconreportsIcon: IconArrayIcon<{
    IconidIcon: IconstringIcon;
    IconreasonIcon: IconModerationReasonIcon;
    IcondescriptionIcon: IconstringIcon;
    IconreportedByIcon: IconstringIcon;
    IconcreatedAtIcon: IconstringIcon;
  }>;
  IconmetadataIcon?: {
    IconfileSizeIcon?: IconnumberIcon;
    IcondurationIcon?: IconnumberIcon;
    IconlanguageIcon?: IconstringIcon;
    IcontagsIcon?: IconstringIcon[];
  };
  IconaiScoreIcon?: {
    IconsafetyIcon: IconnumberIcon;
    IconqualityIcon: IconnumberIcon;
    IconrelevanceIcon: IconnumberIcon;
  };
  IconthumbnailIcon?: IconstringIcon;
}
IconexportIcon IconinterfaceIcon IconContentModerationPanelPropsIcon {
  IcononContentApproveIcon?: (IconcontentIdIcon: IconstringIcon) => IconvoidIcon;
  IcononContentRejectIcon?: (IconcontentIdIcon: IconstringIcon, IconreasonIcon: IconstringIcon) => IconvoidIcon;
  IcononContentDeleteIcon?: (IconcontentIdIcon: IconstringIcon) => IconvoidIcon;
  IcononContentViewIcon?: (IconcontentIcon: IconContentItemIcon) => IconvoidIcon;
  IconshowAIAssistIcon?: IconbooleanIcon;
  IconallowBulkActionsIcon?: IconbooleanIcon;
}
IconexportIcon IconconstIcon IconContentModerationPanelIcon = IconmemoIcon<IconContentModerationPanelPropsIcon>(({
  IcononContentApproveIcon,
  IcononContentRejectIcon,
  IcononContentDeleteIcon,
  IcononContentViewIcon,
  IconshowAIAssistIcon = IcontrueIcon,
  IconallowBulkActionsIcon = IcontrueIcon,
}) => {
  IconconstIcon IconthemeIcon = IconuseThemeIcon();
  IconconstIcon [IcontabValueIcon, IconsetTabValueIcon] = IconuseStateIcon(Icon0Icon);
  IconconstIcon [IconcontentIcon, IconsetContentIcon] = IconuseStateIcon<IconContentItemIcon[]>([]);
  IconconstIcon [IconloadingIcon, IconsetLoadingIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconerrorIcon, IconsetErrorIcon] = IconuseStateIcon<IconstringIcon | IconnullIcon>(IconnullIcon);
  // IconPaginationIcon
  IconconstIcon [IconpageIcon, IconsetPageIcon] = IconuseStateIcon(Icon0Icon);
  IconconstIcon [IconrowsPerPageIcon, IconsetRowsPerPageIcon] = IconuseStateIcon(Icon10Icon);
  // IconSearchIcon IconandIcon IconfilterIcon
  IconconstIcon [IconsearchTermIcon, IconsetSearchTermIcon] = IconuseStateIcon('');
  IconconstIcon [IconfilterTypeIcon, IconsetFilterTypeIcon] = IconuseStateIcon<IconContentTypeIcon | 'Iconall'>('Iconall');
  IconconstIcon [IconfilterStatusIcon, IconsetFilterStatusIcon] = IconuseStateIcon<IconContentStatusIcon | 'Iconall'>('Iconpending');
  // IconSelectionIcon
  IconconstIcon [IconselectedIcon, IconsetSelectedIcon] = IconuseStateIcon<IconstringIcon[]>([]);
  IconconstIcon [IconselectedContentIcon, IconsetSelectedContentIcon] = IconuseStateIcon<IconContentItemIcon | IconnullIcon>(IconnullIcon);
  // IconDialogsIcon
  IconconstIcon [IconviewDialogOpenIcon, IconsetViewDialogOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconrejectDialogOpenIcon, IconsetRejectDialogOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconrejectReasonIcon, IconsetRejectReasonIcon] = IconuseStateIcon('');
  // IconSetupIcon IconPusherIcon IconforIcon IconrealIcon-IcontimeIcon IconupdatesIcon
  IconconstIcon { IconsubscribeIcon, IconunsubscribeIcon } = IconusePusherIcon();
  IconuseEffectIcon(() => {
    IconconstIcon IconchannelIcon = 'IconcontentIcon-Iconmoderation';
    IconconstIcon IconhandleNewContentIcon = (IcondataIcon: IconContentItemIcon) => {
      IconsetContentIcon(IconprevIcon => [IcondataIcon, ...IconprevIcon]);
    };
    IconconstIcon IconhandleContentUpdateIcon = (IcondataIcon: { IconidIcon: IconstringIcon; IconstatusIcon: IconContentStatusIcon }) => {
      IconsetContentIcon(IconprevIcon =>
        IconprevIcon.IconmapIcon(IconitemIcon =>
          IconitemIcon.IconidIcon === IcondataIcon.IconidIcon ? { ...IconitemIcon, IconstatusIcon: IcondataIcon.IconstatusIcon } : IconitemIcon
        )
      );
    };
    IconsubscribeIcon(IconchannelIcon, 'IconnewIcon-Iconcontent', IconhandleNewContentIcon);
    IconsubscribeIcon(IconchannelIcon, 'IconcontentIcon-Iconupdated', IconhandleContentUpdateIcon);
    IconreturnIcon () => {
      IconunsubscribeIcon(IconchannelIcon, 'IconnewIcon-Iconcontent', IconhandleNewContentIcon);
      IconunsubscribeIcon(IconchannelIcon, 'IconcontentIcon-Iconupdated', IconhandleContentUpdateIcon);
    };
  }, [IconsubscribeIcon, IconunsubscribeIcon]);
  // IconFetchIcon IconcontentIcon
  IconuseEffectIcon(() => {
    IconfetchContentIcon();
  }, []);
  IconconstIcon IconfetchContentIcon = IconasyncIcon () => {
    IconsetLoadingIcon(IcontrueIcon);
    IcontryIcon {
      // IconMockIcon IcondataIcon IconforIcon IcondemonstrationIcon
      IconconstIcon IconmockContentIcon: IconContentItemIcon[] = [
        {
          IconidIcon: 'Icon1',
          IcontypeIcon: 'Iconlesson',
          IcontitleIcon: 'IconIntroductionIcon IcontoIcon IconAlgebra',
          IcondescriptionIcon: 'IconBasicIcon IconalgebraicIcon IconconceptsIcon IconforIcon Iconbeginners',
          IconauthorIcon: {
            IconidIcon: 'Iconteacher1',
            IconnameIcon: 'IconSarahIcon IconJohnson',
            IconroleIcon: 'Iconteacher',
          },
          IconstatusIcon: 'Iconpending',
          IconcreatedAtIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon(),
          IconflagsIcon: Icon0Icon,
          IconreportsIcon: [],
          IconaiScoreIcon: {
            IconsafetyIcon: Icon98Icon,
            IconqualityIcon: Icon85Icon,
            IconrelevanceIcon: Icon92Icon,
          },
        },
        {
          IconidIcon: 'Icon2',
          IcontypeIcon: 'Iconassessment',
          IcontitleIcon: 'IconPhysicsIcon IconQuizIcon IconChapterIcon Icon3',
          IcondescriptionIcon: 'IconAssessmentIcon IcononIcon IconforceIcon IconandIcon Iconmotion',
          IconauthorIcon: {
            IconidIcon: 'Iconteacher2',
            IconnameIcon: 'IconMichaelIcon IconBrown',
            IconroleIcon: 'Iconteacher',
          },
          IconstatusIcon: 'Iconpending',
          IconcreatedAtIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon2Icon * Icon60Icon * Icon60Icon * Icon1000Icon).IcontoISOStringIcon(),
          IconflagsIcon: Icon0Icon,
          IconreportsIcon: [],
          IconaiScoreIcon: {
            IconsafetyIcon: Icon100Icon,
            IconqualityIcon: Icon78Icon,
            IconrelevanceIcon: Icon88Icon,
          },
        },
        {
          IconidIcon: 'Icon3',
          IcontypeIcon: 'Iconmessage',
          IcontitleIcon: 'IconStudentIcon IconQuestion',
          IconcontentIcon: 'IconCanIcon IconsomeoneIcon IconhelpIcon IconwithIcon IconthisIcon IconproblemIcon?',
          IconauthorIcon: {
            IconidIcon: 'Iconstudent1',
            IconnameIcon: 'IconJohnIcon IconSmith',
            IconroleIcon: 'Iconstudent',
          },
          IconstatusIcon: 'Iconflagged',
          IconcreatedAtIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon24Icon * Icon60Icon * Icon60Icon * Icon1000Icon).IcontoISOStringIcon(),
          IconflagsIcon: Icon3Icon,
          IconreportsIcon: [
            {
              IconidIcon: 'Iconr1',
              IconreasonIcon: 'Iconspam',
              IcondescriptionIcon: 'IconRepeatedIcon Iconposting',
              IconreportedByIcon: 'Iconuser123',
              IconcreatedAtIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon(),
            },
          ],
          IconaiScoreIcon: {
            IconsafetyIcon: Icon65Icon,
            IconqualityIcon: Icon40Icon,
            IconrelevanceIcon: Icon30Icon,
          },
        },
        {
          IconidIcon: 'Icon4',
          IcontypeIcon: 'Iconvideo',
          IcontitleIcon: 'IconChemistryIcon IconLabIcon IconExperiment',
          IcondescriptionIcon: 'IconLabIcon IconsafetyIcon IconandIcon IconprocedureIcon Icondemonstration',
          IconauthorIcon: {
            IconidIcon: 'Iconteacher3',
            IconnameIcon: 'IconEmilyIcon IconDavis',
            IconroleIcon: 'Iconteacher',
          },
          IconstatusIcon: 'Iconapproved',
          IconcreatedAtIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon3Icon * Icon24Icon * Icon60Icon * Icon60Icon * Icon1000Icon).IcontoISOStringIcon(),
          IconreviewedAtIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon2Icon * Icon24Icon * Icon60Icon * Icon60Icon * Icon1000Icon).IcontoISOStringIcon(),
          IconreviewedByIcon: {
            IconidIcon: 'Iconadmin1',
            IconnameIcon: 'IconAdminIcon IconUser',
          },
          IconflagsIcon: Icon0Icon,
          IconreportsIcon: [],
          IconmetadataIcon: {
            IcondurationIcon: Icon1200Icon, // Icon20Icon IconminutesIcon
            IconfileSizeIcon: Icon250Icon * Icon1024Icon * Icon1024Icon, // Icon250MBIcon
          },
          IconaiScoreIcon: {
            IconsafetyIcon: Icon100Icon,
            IconqualityIcon: Icon95Icon,
            IconrelevanceIcon: Icon98Icon,
          },
          IconthumbnailIcon: 'IconhttpsIcon://IconviaIcon.IconplaceholderIcon.IconcomIcon/Icon150',
        },
        {
          IconidIcon: 'Icon5',
          IcontypeIcon: 'Icondocument',
          IcontitleIcon: 'IconStudyIcon IconGuideIcon - IconWorldIcon IconHistory',
          IcondescriptionIcon: 'IconComprehensiveIcon IconguideIcon IconforIcon IconfinalIcon Iconexam',
          IconauthorIcon: {
            IconidIcon: 'Iconteacher1',
            IconnameIcon: 'IconSarahIcon IconJohnson',
            IconroleIcon: 'Iconteacher',
          },
          IconstatusIcon: 'Iconunder_review',
          IconcreatedAtIcon: IconnewIcon IconDateIcon(IconDateIcon.IconnowIcon() - Icon4Icon * Icon60Icon * Icon60Icon * Icon1000Icon).IcontoISOStringIcon(),
          IconflagsIcon: Icon1Icon,
          IconreportsIcon: [
            {
              IconidIcon: 'Iconr2',
              IconreasonIcon: 'Iconcopyright',
              IcondescriptionIcon: 'IconContainsIcon IconcopyrightedIcon Iconmaterial',
              IconreportedByIcon: 'Iconuser456',
              IconcreatedAtIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon(),
            },
          ],
          IconaiScoreIcon: {
            IconsafetyIcon: Icon90Icon,
            IconqualityIcon: Icon82Icon,
            IconrelevanceIcon: Icon95Icon,
          },
        },
      ];
      IconsetContentIcon(IconmockContentIcon);
    } IconcatchIcon (IconerrIcon) {
      IconsetErrorIcon('IconFailedIcon IcontoIcon IconfetchIcon Iconcontent');
      IconconsoleIcon.IconerrorIcon(IconerrIcon);
    } IconfinallyIcon {
      IconsetLoadingIcon(IconfalseIcon);
    }
  };
  IconconstIcon IconhandleApproveIcon = IconasyncIcon (IconcontentItemIcon: IconContentItemIcon) => {
    IconsetContentIcon(IconprevIcon =>
      IconprevIcon.IconmapIcon(IconitemIcon =>
        IconitemIcon.IconidIcon === IconcontentItemIcon.IconidIcon
          ? { ...IconitemIcon, IconstatusIcon: 'Iconapproved', IconreviewedAtIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon() }
          : IconitemIcon
      )
    );
    IcononContentApproveIcon?.(IconcontentItemIcon.IconidIcon);
  };
  IconconstIcon IconhandleRejectIcon = IconasyncIcon () => {
    IconifIcon (IconselectedContentIcon && IconrejectReasonIcon) {
      IconsetContentIcon(IconprevIcon =>
        IconprevIcon.IconmapIcon(IconitemIcon =>
          IconitemIcon.IconidIcon === IconselectedContentIcon.IconidIcon
            ? { ...IconitemIcon, IconstatusIcon: 'Iconrejected', IconreviewedAtIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon() }
            : IconitemIcon
        )
      );
      IcononContentRejectIcon?.(IconselectedContentIcon.IconidIcon, IconrejectReasonIcon);
      IconsetRejectDialogOpenIcon(IconfalseIcon);
      IconsetRejectReasonIcon('');
      IconsetSelectedContentIcon(IconnullIcon);
    }
  };
  IconconstIcon IconhandleBulkActionIcon = (IconactionIcon: 'Iconapprove' | 'Iconreject' | 'Icondelete') => {
    IconselectedIcon.IconforEachIcon(IconidIcon => {
      IconconstIcon IconitemIcon = IconcontentIcon.IconfindIcon(IconcIcon => IconcIcon.IconidIcon === IconidIcon);
      IconifIcon (IconitemIcon) {
        IconswitchIcon (IconactionIcon) {
          IconcaseIcon 'Iconapprove':
            IconhandleApproveIcon(IconitemIcon);
            IconbreakIcon;
          IconcaseIcon 'Iconreject':
            // IconOpenIcon IconrejectIcon IcondialogIcon IconforIcon IconbulkIcon IconrejectIcon
            IconbreakIcon;
          IconcaseIcon 'Icondelete':
            IconhandleDeleteIcon(IconitemIcon);
            IconbreakIcon;
        }
      }
    });
    IconsetSelectedIcon([]);
  };
  IconconstIcon IconhandleDeleteIcon = IconasyncIcon (IconcontentItemIcon: IconContentItemIcon) => {
    IconsetContentIcon(IconprevIcon => IconprevIcon.IconfilterIcon(IconitemIcon => IconitemIcon.IconidIcon !== IconcontentItemIcon.IconidIcon));
    IcononContentDeleteIcon?.(IconcontentItemIcon.IconidIcon);
  };
  IconconstIcon IcongetContentIconIcon = (IcontypeIcon: IconContentTypeIcon) => {
    IconswitchIcon (IcontypeIcon) {
      IconcaseIcon 'Iconlesson':
        IconreturnIcon <IconIconSchoolIcon />;
      IconcaseIcon 'Iconassessment':
        IconreturnIcon <IconIconReportAnalyticsIcon />;
      IconcaseIcon 'Iconmessage':
        IconreturnIcon <IconIconMessageCircleIcon />;
      IconcaseIcon 'Iconimage':
        IconreturnIcon <IconIconImageIcon />;
      IconcaseIcon 'Iconvideo':
        IconreturnIcon <IconIconVideoLibraryIcon />;
      IconcaseIcon 'Icondocument':
        IconreturnIcon <IconIconFileTextIcon />;
      IconcaseIcon 'Iconcode':
        IconreturnIcon <IconIconCodeIcon />;
      IcondefaultIcon:
        IconreturnIcon <IconIconInfoCircleIcon />;
    }
  };
  IconconstIcon IcongetStatusColorIcon = (IconstatusIcon: IconContentStatusIcon) => {
    IconswitchIcon (IconstatusIcon) {
      IconcaseIcon 'Iconpending':
        IconreturnIcon 'Iconwarning';
      IconcaseIcon 'Iconapproved':
        IconreturnIcon 'Iconsuccess';
      IconcaseIcon 'Iconrejected':
        IconreturnIcon 'Iconerror';
      IconcaseIcon 'Iconflagged':
        IconreturnIcon 'Iconerror';
      IconcaseIcon 'Iconunder_review':
        IconreturnIcon 'Iconinfo';
      IcondefaultIcon:
        IconreturnIcon 'Icondefault';
    }
  };
  IconconstIcon IcongetAIScoreColorIcon = (IconscoreIcon: IconnumberIcon) => {
    IconifIcon (IconscoreIcon >= Icon80Icon) IconreturnIcon IconthemeIcon.IconpaletteIcon.IconsuccessIcon.IconmainIcon;
    IconifIcon (IconscoreIcon >= Icon60Icon) IconreturnIcon IconthemeIcon.IconpaletteIcon.IconwarningIcon.IconmainIcon;
    IconreturnIcon IconthemeIcon.IconpaletteIcon.IconerrorIcon.IconmainIcon;
  };
  IconconstIcon IconfilteredContentIcon = IconcontentIcon.IconfilterIcon(IconitemIcon => {
    IconconstIcon IconmatchesSearchIcon = IconsearchTermIcon
      ? IconitemIcon.IcontitleIcon.IcontoLowerCaseIcon().IconincludesIcon(IconsearchTermIcon.IcontoLowerCaseIcon()) ||
        IconitemIcon.IcondescriptionIcon?.IcontoLowerCaseIcon().IconincludesIcon(IconsearchTermIcon.IcontoLowerCaseIcon())
      : IcontrueIcon;
    IconconstIcon IconmatchesTypeIcon = IconfilterTypeIcon === 'Iconall' || IconitemIcon.IcontypeIcon === IconfilterTypeIcon;
    IconconstIcon IconmatchesStatusIcon = IconfilterStatusIcon === 'Iconall' || IconitemIcon.IconstatusIcon === IconfilterStatusIcon;
    IconreturnIcon IconmatchesSearchIcon && IconmatchesTypeIcon && IconmatchesStatusIcon;
  });
  IconconstIcon IcongetTabContentIcon = () => {
    IconswitchIcon (IcontabValueIcon) {
      IconcaseIcon Icon0Icon: // IconPendingIcon IconReviewIcon
        IconreturnIcon IconfilteredContentIcon.IconfilterIcon(IconcIcon => IconcIcon.IconstatusIcon === 'Iconpending');
      IconcaseIcon Icon1Icon: // IconFlaggedIcon
        IconreturnIcon IconfilteredContentIcon.IconfilterIcon(IconcIcon => IconcIcon.IconstatusIcon === 'Iconflagged');
      IconcaseIcon Icon2Icon: // IconUnderIcon IconReviewIcon
        IconreturnIcon IconfilteredContentIcon.IconfilterIcon(IconcIcon => IconcIcon.IconstatusIcon === 'Iconunder_review');
      IconcaseIcon Icon3Icon: // IconAllIcon IconContentIcon
        IconreturnIcon IconfilteredContentIcon;
      IcondefaultIcon:
        IconreturnIcon [];
    }
  };
  IconconstIcon IcontabContentIcon = IcongetTabContentIcon();
  IconconstIcon IconpaginatedContentIcon = IcontabContentIcon.IconsliceIcon(
    IconpageIcon * IconrowsPerPageIcon,
    IconpageIcon * IconrowsPerPageIcon + IconrowsPerPageIcon
  );
  IconreturnIcon (
    <IconPaperIcon IconstyleIcon={{ IconheightIcon: 'Icon100Icon%', IcondisplayIcon: 'Iconflex', IconflexDirectionIcon: 'Iconcolumn' }}>
      {/* IconHeaderIcon */}
      <IconBoxIcon IconstyleIcon={{ IconpIcon: Icon2Icon, IconborderBottomIcon: Icon1Icon, IconborderColorIcon: 'Icondivider' }}>
        <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
          <IconTypographyIcon IconorderIcon={Icon6Icon} IconfontWeightIcon="Iconbold">
            IconContentIcon IconModerationIcon
          <IconIconIcon/IconTypographyIcon>
          <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon}>
            {IconallowBulkActionsIcon && IconselectedIcon.IconlengthIcon > Icon0Icon && (
              <IconIconIcon>
                <IconButtonIcon
                  IconsizeIcon="Iconsmall"
                  IconcolorIcon="Icongreen"
                  IconstartIconIcon={<IconIconCheckIcon />}
                  IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconhandleBulkActionIcon('Iconapprove')}
                >
                  IconApproveIcon ({IconselectedIcon.IconlengthIcon})
                <IconIconIcon/IconButtonIcon>
                <IconButtonIcon
                  IconsizeIcon="Iconsmall"
                  IconcolorIcon="Iconred"
                  IconstartIconIcon={<IconIconXIcon />}
                  IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconhandleBulkActionIcon('Iconreject')}
                >
                  IconRejectIcon ({IconselectedIcon.IconlengthIcon})
                <IconIconIcon/IconButtonIcon>
              <IconIconIcon/>
            )}
            {IconshowAIAssistIcon && (
              <IconButtonIcon
                IconsizeIcon="Iconsmall"
                IconvariantIcon="Iconoutline"
                IconstartIconIcon={<IconIconAutoAwesomeIcon />}
              >
                IconAIIcon IconAssistIcon
              <IconIconIcon/IconButtonIcon>
            )}
          <IconIconIcon/IconStackIcon>
        <IconIconIcon/IconStackIcon>
        {/* IconTabsIcon */}
        <IconTabsIcon
          IconvalueIcon={IcontabValueIcon}
          IcononChangeIcon={(Icon_Icon, IconvalueIcon) => IconsetTabValueIcon(IconvalueIcon)}
          IconstyleIcon={{ IconmtIcon: Icon2Icon }}
        >
          <IconTabIcon
            IconlabelIcon={
              <IconBadgeIcon IconbadgeContentIcon={IconcontentIcon.IconfilterIcon(IconcIcon => IconcIcon.IconstatusIcon === 'Iconpending').IconlengthIcon} IconcolorIcon="Iconyellow">
                IconPendingIcon IconReviewIcon
              <IconIconIcon/IconBadgeIcon>
            }
          />
          <IconTabIcon
            IconlabelIcon={
              <IconBadgeIcon IconbadgeContentIcon={IconcontentIcon.IconfilterIcon(IconcIcon => IconcIcon.IconstatusIcon === 'Iconflagged').IconlengthIcon} IconcolorIcon="Iconred">
                IconFlaggedIcon
              <IconIconIcon/IconBadgeIcon>
            }
          />
          <IconTabIcon
            IconlabelIcon={
              <IconBadgeIcon IconbadgeContentIcon={IconcontentIcon.IconfilterIcon(IconcIcon => IconcIcon.IconstatusIcon === 'Iconunder_review').IconlengthIcon} IconcolorIcon="Iconcyan">
                IconUnderIcon IconReviewIcon
              <IconIconIcon/IconBadgeIcon>
            }
          />
          <IconTabIcon IconlabelIcon="IconAllIcon IconContent" />
        <IconIconIcon/IconTabsIcon>
        {/* IconFiltersIcon */}
        <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon} IconstyleIcon={{ IconmtIcon: Icon2Icon }}>
          <IconTextFieldIcon
            IconsizeIcon="Iconsmall"
            IconplaceholderIcon="IconSearchIcon IconcontentIcon..."
            IconvalueIcon={IconsearchTermIcon}
            IcononChangeIcon={(IconeIcon) => IconsetSearchTermIcon(IconeIcon.IcontargetIcon.IconvalueIcon)}
            IconInputPropsIcon={{
              IconstartAdornmentIcon: (
                <IconInputAdornmentIcon IconpositionIcon="Iconstart">
                  <IconIconSearchIcon />
                <IconIconIcon/IconInputAdornmentIcon>
              ),
            }}
            IconstyleIcon={{ IconflexIcon: Icon1Icon, IconmaxWidthIcon: Icon300Icon }}
          />
          <IconFormControlIcon IconsizeIcon="Iconsmall" IconstyleIcon={{ IconminWidthIcon: Icon120Icon }}>
            <IconInputLabelIcon>IconTypeIcon<IconIconIcon/IconInputLabelIcon>
            <IconSelectIcon
              IconvalueIcon={IconfilterTypeIcon}
              IconlabelIcon="IconType"
              IcononChangeIcon={(IconeIcon) => IconsetFilterTypeIcon(IconeIcon.IcontargetIcon.IconvalueIcon IconasIcon IconContentTypeIcon | 'Iconall')}
            >
              <IconMenuItemIcon IconvalueIcon="Iconall">IconAllIcon IconTypesIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Iconlesson">IconLessonIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Iconassessment">IconAssessmentIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Iconmessage">IconMessageIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Iconvideo">IconVideoIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Icondocument">IconDocumentIcon<IconIconIcon/IconMenuItemIcon>
            <IconIconIcon/IconSelectIcon>
          <IconIconIcon/IconFormControlIcon>
        <IconIconIcon/IconStackIcon>
      <IconIconIcon/IconBoxIcon>
      {/* IconLoadingIcon */}
      {IconloadingIcon && <IconLinearProgressIcon />}
      {/* IconErrorIcon */}
      {IconerrorIcon && (
        <IconAlertIcon IconseverityIcon="Iconerror" IconstyleIcon={{ IconmIcon: Icon2Icon }}>
          {IconerrorIcon}
        <IconIconIcon/IconAlertIcon>
      )}
      {/* IconContentIcon IconListIcon */}
      <IconBoxIcon IconstyleIcon={{ IconflexIcon: Icon1Icon, IconoverflowIcon: 'Iconauto', IconpIcon: Icon2Icon }}>
        <IconGridIcon IconcontainerIcon IconspacingIcon={Icon2Icon}>
          {IconpaginatedContentIcon.IconmapIcon(IconitemIcon => (
            <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconmdIcon={Icon6Icon} IconlgIcon={Icon4Icon} IconkeyIcon={IconitemIcon.IconidIcon}>
              <IconCardIcon
                IconstyleIcon={{
                  IconheightIcon: 'Icon100Icon%',
                  IcondisplayIcon: 'Iconflex',
                  IconflexDirectionIcon: 'Iconcolumn',
                  IconborderLeftIcon: `Icon4pxIcon IconsolidIcon ${IconthemeIcon.IconpaletteIcon[IcongetStatusColorIcon(IconitemIcon.IconstatusIcon)].IconmainIcon}`,
                }}
              >
                {IconitemIcon.IconthumbnailIcon && (
                  <IconCardMediaIcon
                    IconcomponentIcon="Iconimg"
                    IconheightIcon="Icon140"
                    IconimageIcon={IconitemIcon.IconthumbnailIcon}
                    IconaltIcon={IconitemIcon.IcontitleIcon}
                  />
                )}
                <IconCardContentIcon IconstyleIcon={{ IconflexIcon: Icon1Icon }}>
                  <IconStackIcon IconspacingIcon={Icon1Icon}>
                    {/* IconHeaderIcon */}
                    <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                      <IconChipIcon
                        IconiconIcon={IcongetContentIconIcon(IconitemIcon.IcontypeIcon)}
                        IconlabelIcon={IconitemIcon.IcontypeIcon}
                        IconsizeIcon="Iconsmall"
                        IconvariantIcon="Iconoutline"
                      />
                      <IconChipIcon
                        IconlabelIcon={IconitemIcon.IconstatusIcon}
                        IconsizeIcon="Iconsmall"
                        IconcolorIcon={IcongetStatusColorIcon(IconitemIcon.IconstatusIcon) IconasIcon IconanyIcon}
                      />
                    <IconIconIcon/IconStackIcon>
                    {/* IconTitleIcon IconandIcon IcondescriptionIcon */}
                    <IconTypographyIcon IconvariantIcon="Iconsubtitle1" IconfontWeightIcon="Iconbold">
                      {IconitemIcon.IcontitleIcon}
                    <IconIconIcon/IconTypographyIcon>
                    {IconitemIcon.IcondescriptionIcon && (
                      <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary" IconstyleIcon={{ IconheightIcon: Icon40Icon, IconoverflowIcon: 'Iconhidden' }}>
                        {IconitemIcon.IcondescriptionIcon}
                      <IconIconIcon/IconTypographyIcon>
                    )}
                    {/* IconAuthorIcon */}
                    <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconspacingIcon={Icon1Icon}>
                      <IconAvatarIcon IconstyleIcon={{ IconwidthIcon: Icon24Icon, IconheightIcon: Icon24Icon }}>
                        {IconitemIcon.IconauthorIcon.IconnameIcon.IconcharAtIcon(Icon0Icon)}
                      <IconIconIcon/IconAvatarIcon>
                      <IconTypographyIcon IconvariantIcon="Iconcaption">
                        {IconitemIcon.IconauthorIcon.IconnameIcon} • {IconformatIcon(IconnewIcon IconDateIcon(IconitemIcon.IconcreatedAtIcon), 'IconMMMIcon IconddIcon, IconHHIcon:Iconmm')}
                      <IconIconIcon/IconTypographyIcon>
                    <IconIconIcon/IconStackIcon>
                    {/* IconAIIcon IconScoresIcon */}
                    {IconshowAIAssistIcon && IconitemIcon.IconaiScoreIcon && (
                      <IconStackIcon IconspacingIcon={Icon0Icon.Icon5Icon}>
                        <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                          IconAIIcon IconAnalysisIcon
                        <IconIconIcon/IconTypographyIcon>
                        <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon}>
                          <IconTooltipIcon IcontitleIcon="IconSafetyIcon IconScore">
                            <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconspacingIcon={Icon0Icon.Icon5Icon}>
                              <IconIconGavelIcon IconfontSizeIcon="Iconsmall" IconstyleIcon={{ IconcolorIcon: IcongetAIScoreColorIcon(IconitemIcon.IconaiScoreIcon.IconsafetyIcon) }} />
                              <IconTypographyIcon IconvariantIcon="Iconcaption">{IconitemIcon.IconaiScoreIcon.IconsafetyIcon}%<IconIconIcon/IconTypographyIcon>
                            <IconIconIcon/IconStackIcon>
                          <IconIconIcon/IconTooltipIcon>
                          <IconTooltipIcon IcontitleIcon="IconQualityIcon IconScore">
                            <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconspacingIcon={Icon0Icon.Icon5Icon}>
                              <IconIconThumbUpIcon IconfontSizeIcon="Iconsmall" IconstyleIcon={{ IconcolorIcon: IcongetAIScoreColorIcon(IconitemIcon.IconaiScoreIcon.IconqualityIcon) }} />
                              <IconTypographyIcon IconvariantIcon="Iconcaption">{IconitemIcon.IconaiScoreIcon.IconqualityIcon}%<IconIconIcon/IconTypographyIcon>
                            <IconIconIcon/IconStackIcon>
                          <IconIconIcon/IconTooltipIcon>
                          <IconTooltipIcon IcontitleIcon="IconRelevanceIcon IconScore">
                            <IconStackIcon IcondirectionIcon="Iconrow" IconalignItemsIcon="Iconcenter" IconspacingIcon={Icon0Icon.Icon5Icon}>
                              <IconIconInfoCircleIcon IconfontSizeIcon="Iconsmall" IconstyleIcon={{ IconcolorIcon: IcongetAIScoreColorIcon(IconitemIcon.IconaiScoreIcon.IconrelevanceIcon) }} />
                              <IconTypographyIcon IconvariantIcon="Iconcaption">{IconitemIcon.IconaiScoreIcon.IconrelevanceIcon}%<IconIconIcon/IconTypographyIcon>
                            <IconIconIcon/IconStackIcon>
                          <IconIconIcon/IconTooltipIcon>
                        <IconIconIcon/IconStackIcon>
                      <IconIconIcon/IconStackIcon>
                    )}
                    {/* IconFlagsIcon IconandIcon IconreportsIcon */}
                    {(IconitemIcon.IconflagsIcon > Icon0Icon || IconitemIcon.IconreportsIcon.IconlengthIcon > Icon0Icon) && (
                      <IconAlertIcon IconseverityIcon="Iconwarning" IconstyleIcon={{ IconpyIcon: Icon0Icon.Icon5Icon }}>
                        <IconStackIcon IconspacingIcon={Icon0Icon.Icon5Icon}>
                          <IconTypographyIcon IconvariantIcon="Iconcaption">
                            {IconitemIcon.IconflagsIcon} IconflagsIcon, {IconitemIcon.IconreportsIcon.IconlengthIcon} IconreportsIcon
                          <IconIconIcon/IconTypographyIcon>
                          {IconitemIcon.IconreportsIcon[Icon0Icon] && (
                            <IconTypographyIcon IconvariantIcon="Iconcaption">
                              IconLatestIcon: {IconitemIcon.IconreportsIcon[Icon0Icon].IconreasonIcon}
                            <IconIconIcon/IconTypographyIcon>
                          )}
                        <IconIconIcon/IconStackIcon>
                      <IconIconIcon/IconAlertIcon>
                    )}
                  <IconIconIcon/IconStackIcon>
                <IconIconIcon/IconCardContentIcon>
                <IconCardActionsIcon>
                  {IconallowBulkActionsIcon && (
                    <IconCheckboxIcon
                      IconcheckedIcon={IconselectedIcon.IconincludesIcon(IconitemIcon.IconidIcon)}
                      IcononChangeIcon={() => {
                        IconifIcon (IconselectedIcon.IconincludesIcon(IconitemIcon.IconidIcon)) {
                          IconsetSelectedIcon(IconprevIcon => IconprevIcon.IconfilterIcon(IconidIcon => IconidIcon !== IconitemIcon.IconidIcon));
                        } IconelseIcon {
                          IconsetSelectedIcon(IconprevIcon => [...IconprevIcon, IconitemIcon.IconidIcon]);
                        }
                      }}
                    />
                  )}
                  <IconIconButtonIcon
                    IconsizeIcon="Iconsmall"
                    IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
                      IconsetSelectedContentIcon(IconitemIcon);
                      IconsetViewDialogOpenIcon(IcontrueIcon);
                    }}
                  >
                    <IconIconEyeIcon />
                  <IconIconIcon/IconIconButtonIcon>
                  {IconitemIcon.IconstatusIcon === 'Iconpending' && (
                    <IconIconIcon>
                      <IconIconButtonIcon
                        IconsizeIcon="Iconsmall"
                        IconcolorIcon="Icongreen"
                        IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconhandleApproveIcon(IconitemIcon)}
                      >
                        <IconIconCheckIcon />
                      <IconIconIcon/IconIconButtonIcon>
                      <IconIconButtonIcon
                        IconsizeIcon="Iconsmall"
                        IconcolorIcon="Iconred"
                        IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
                          IconsetSelectedContentIcon(IconitemIcon);
                          IconsetRejectDialogOpenIcon(IcontrueIcon);
                        }}
                      >
                        <IconIconXIcon />
                      <IconIconIcon/IconIconButtonIcon>
                    <IconIconIcon/>
                  )}
                  <IconIconButtonIcon
                    IconsizeIcon="Iconsmall"
                    IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconhandleDeleteIcon(IconitemIcon)}
                  >
                    <IconIconTrashIcon />
                  <IconIconIcon/IconIconButtonIcon>
                <IconIconIcon/IconCardActionsIcon>
              <IconIconIcon/IconCardIcon>
            <IconIconIcon/IconGridIcon>
          ))}
        <IconIconIcon/IconGridIcon>
      <IconIconIcon/IconBoxIcon>
      {/* IconPaginationIcon */}
      <IconTablePaginationIcon
        IconcomponentIcon="Icondiv"
        IconcountIcon={IcontabContentIcon.IconlengthIcon}
        IconpageIcon={IconpageIcon}
        IcononPageChangeIcon={(Icon_Icon, IconnewPageIcon) => IconsetPageIcon(IconnewPageIcon)}
        IconrowsPerPageIcon={IconrowsPerPageIcon}
        IcononRowsPerPageChangeIcon={(IconeIcon) => {
          IconsetRowsPerPageIcon(IconparseIntIcon(IconeIcon.IcontargetIcon.IconvalueIcon, Icon10Icon));
          IconsetPageIcon(Icon0Icon);
        }}
      />
      {/* IconViewIcon IconDialogIcon */}
      <IconDialogIcon
        IconopenIcon={IconviewDialogOpenIcon}
        IcononCloseIcon={() => IconsetViewDialogOpenIcon(IconfalseIcon)}
        IconmaxWidthIcon="Iconmd"
        IconfullWidthIcon
      >
        <IconDialogTitleIcon>IconContentIcon IconDetailsIcon<IconIconIcon/IconDialogTitleIcon>
        <IconDialogContentIcon>
          {IconselectedContentIcon && (
            <IconStackIcon IconspacingIcon={Icon2Icon}>
              <IconTypographyIcon IconorderIcon={Icon6Icon}>{IconselectedContentIcon.IcontitleIcon}<IconIconIcon/IconTypographyIcon>
              {IconselectedContentIcon.IcondescriptionIcon && (
                <IconTypographyIcon>{IconselectedContentIcon.IcondescriptionIcon}<IconIconIcon/IconTypographyIcon>
              )}
              {IconselectedContentIcon.IconcontentIcon && (
                <IconPaperIcon IconvariantIcon="Iconoutline" IconstyleIcon={{ IconpIcon: Icon2Icon }}>
                  <IconTypographyIcon>{IconselectedContentIcon.IconcontentIcon}<IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconPaperIcon>
              )}
              <IconDividerIcon />
              <IconTypographyIcon IconvariantIcon="Iconsubtitle2">IconMetadataIcon<IconIconIcon/IconTypographyIcon>
              <IconGridIcon IconcontainerIcon IconspacingIcon={Icon2Icon}>
                <IconGridIcon IconitemIcon IconxsIcon={Icon6Icon}>
                  <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                    IconAuthorIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon>{IconselectedContentIcon.IconauthorIcon.IconnameIcon}<IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconGridIcon>
                <IconGridIcon IconitemIcon IconxsIcon={Icon6Icon}>
                  <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
                    IconCreatedIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon>
                    {IconformatIcon(IconnewIcon IconDateIcon(IconselectedContentIcon.IconcreatedAtIcon), 'IconPPp')}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconGridIcon>
              <IconIconIcon/IconGridIcon>
            <IconIconIcon/IconStackIcon>
          )}
        <IconIconIcon/IconDialogContentIcon>
        <IconDialogActionsIcon>
          <IconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconsetViewDialogOpenIcon(IconfalseIcon)}>IconCloseIcon<IconIconIcon/IconButtonIcon>
        <IconIconIcon/IconDialogActionsIcon>
      <IconIconIcon/IconDialogIcon>
      {/* IconRejectIcon IconDialogIcon */}
      <IconDialogIcon
        IconopenIcon={IconrejectDialogOpenIcon}
        IcononCloseIcon={() => IconsetRejectDialogOpenIcon(IconfalseIcon)}
        IconmaxWidthIcon="Iconsm"
        IconfullWidthIcon
      >
        <IconDialogTitleIcon>IconRejectIcon IconContentIcon<IconIconIcon/IconDialogTitleIcon>
        <IconDialogContentIcon>
          <IconStackIcon IconspacingIcon={Icon2Icon}>
            <IconTypographyIcon>
              IconPleaseIcon IconprovideIcon IconaIcon IconreasonIcon IconforIcon IconrejectingIcon "{IconselectedContentIcon?.IcontitleIcon}"
            <IconIconIcon/IconTypographyIcon>
            <IconFormControlIcon IconfullWidthIcon>
              <IconInputLabelIcon>IconReasonIcon<IconIconIcon/IconInputLabelIcon>
              <IconSelectIcon
                IconvalueIcon={IconrejectReasonIcon}
                IconlabelIcon="IconReason"
                IcononChangeIcon={(IconeIcon) => IconsetRejectReasonIcon(IconeIcon.IcontargetIcon.IconvalueIcon)}
              >
                <IconMenuItemIcon IconvalueIcon="Iconinappropriate">IconInappropriateIcon IconContentIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconspam">IconSpamIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconcopyright">IconCopyrightIcon IconViolationIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconquality">IconLowIcon IconQualityIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconpolicy">IconPolicyIcon IconViolationIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconother">IconOtherIcon<IconIconIcon/IconMenuItemIcon>
              <IconIconIcon/IconSelectIcon>
            <IconIconIcon/IconFormControlIcon>
            <IconTextFieldIcon
              IconmultilineIcon
              IconrowsIcon={Icon3Icon}
              IconlabelIcon="IconAdditionalIcon IconComments"
              IconfullWidthIcon
            />
          <IconIconIcon/IconStackIcon>
        <IconIconIcon/IconDialogContentIcon>
        <IconDialogActionsIcon>
          <IconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconsetRejectDialogOpenIcon(IconfalseIcon)}>IconCancelIcon<IconIconIcon/IconButtonIcon>
          <IconButtonIcon
            IconvariantIcon="Iconfilled"
            IconcolorIcon="Iconred"
            IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleRejectIcon}
            IcondisabledIcon={!IconrejectReasonIcon}
          >
            IconRejectIcon
          <IconIconIcon/IconButtonIcon>
        <IconIconIcon/IconDialogActionsIcon>
      <IconIconIcon/IconDialogIcon>
    <IconIconIcon/IconPaperIcon>
  );
});
IconContentModerationPanelIcon.IcondisplayNameIcon = 'IconContentModerationPanel';
IconexportIcon IcondefaultIcon IconContentModerationPanelIcon;