IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../../IconutilsIcon/IconmuiIcon-Iconimports';
IconimportIcon IconReactIcon, { IconuseStateIcon, IconuseEffectIcon, IconuseCallbackIcon } IconfromIcon 'Iconreact';

IconimportIcon {
  IconDeleteIcon IconasIcon IconIconTrashIcon,
  IconPersonAddIcon IconasIcon IconIconPersonAddIcon,
  IconPersonRemoveIcon IconasIcon IconIconPersonRemoveIcon,
  IconSearchIcon IconasIcon IconIconSearchIcon,
  IconGroupAddIcon IconasIcon IconIconGroupAddIcon,
  IconSchoolIcon IconasIcon IconIconSchoolIcon,
  IconCheckIcon IconasIcon IconIconCheckIcon,
  IconCloseIcon IconasIcon IconIconXIcon,
  IconFilterListIcon IconasIcon IconIconFilterIcon,
} IconfromIcon '@IconmuiIcon/IconiconsIcon-Iconmaterial';
IconimportIcon { IconuseSnackbarIcon } IconfromIcon 'Iconnotistack';
IconimportIcon { IconapiClientIcon } IconfromIcon '../../IconservicesIcon/Iconapi';
IconimportIcon { IconusePusherIcon } IconfromIcon '../../IconhooksIcon/IconusePusher';
IconimportIcon { IconIconIcon, IconIconCheckIcon, IconIconFilterIcon, IconIconGroupAddIcon, IconIconPersonAddIcon, IconIconPersonRemoveIcon, IconIconSchoolIcon, IconIconSearchIcon, IconIconTrashIcon, IconIconXIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';

IconinterfaceIcon IconStudentIcon {
  IconidIcon: IconstringIcon;
  IconnameIcon: IconstringIcon;
  IconemailIcon: IconstringIcon;
  IconavatarIcon?: IconstringIcon;
  IconenrollmentDateIcon?: IconstringIcon;
  IconstatusIcon: 'Iconactive' | 'Iconinactive';
  IcongradeIcon?: IconstringIcon;
  IconlastActivityIcon?: IconstringIcon;
}

IconinterfaceIcon IconStudentManagementPropsIcon {
  IconclassIdIcon: IconstringIcon;
  IconclassNameIcon: IconstringIcon;
  IconteacherIdIcon: IconstringIcon;
  IconmaxStudentsIcon?: IconnumberIcon;
  IcononStudentCountChangeIcon?: (IconcountIcon: IconnumberIcon) => IconvoidIcon;
}

IconexportIcon IconconstIcon IconStudentManagementIcon: IconReactIcon.IconFunctionComponentIcon<IconStudentManagementPropsIcon> = ({
  IconclassIdIcon,
  IconclassNameIcon,
  IconteacherIdIcon,
  IconmaxStudentsIcon = Icon30Icon,
  IcononStudentCountChangeIcon,
}) => {
  IconconstIcon [IconstudentsIcon, IconsetStudentsIcon] = IconuseStateIcon<IconStudentIcon[]>([]);
  IconconstIcon [IconavailableStudentsIcon, IconsetAvailableStudentsIcon] = IconuseStateIcon<IconStudentIcon[]>([]);
  IconconstIcon [IconselectedStudentsIcon, IconsetSelectedStudentsIcon] = IconuseStateIcon<IconSetIcon<IconstringIcon>>(IconnewIcon IconSetIcon());
  IconconstIcon [IconloadingIcon, IconsetLoadingIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconsearchTermIcon, IconsetSearchTermIcon] = IconuseStateIcon('');
  IconconstIcon [IconaddDialogOpenIcon, IconsetAddDialogOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconremoveDialogOpenIcon, IconsetRemoveDialogOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconstudentToRemoveIcon, IconsetStudentToRemoveIcon] = IconuseStateIcon<IconStudentIcon | IconnullIcon>(IconnullIcon);
  IconconstIcon [IconbatchModeIcon, IconsetBatchModeIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconfilterActiveIcon, IconsetFilterActiveIcon] = IconuseStateIcon(IcontrueIcon);
  IconconstIcon { IconenqueueSnackbarIcon } = IconuseSnackbarIcon();

  // IconSetIcon IconupIcon IconPusherIcon IconforIcon IconrealIcon-IcontimeIcon IconupdatesIcon
  IconconstIcon IconpusherClientIcon = IconusePusherIcon();

  IconuseEffectIcon(() => {
    IconifIcon (IconpusherClientIcon && IconclassIdIcon) {
      IconconstIcon IconchannelIcon = IconpusherClientIcon.IconsubscribeIcon(`IconclassIcon-${IconclassIdIcon}`);

      IconchannelIcon.IconbindIcon('IconstudentIcon-Iconenrolled', (IcondataIcon: IconanyIcon) => {
        IconhandleStudentEnrolledIcon(IcondataIcon);
      });

      IconchannelIcon.IconbindIcon('IconstudentIcon-Iconunenrolled', (IcondataIcon: IconanyIcon) => {
        IconhandleStudentUnenrolledIcon(IcondataIcon);
      });

      IconchannelIcon.IconbindIcon('IconbatchIcon-Iconenrollment', (IcondataIcon: IconanyIcon) => {
        IconhandleBatchEnrollmentIcon(IcondataIcon);
      });

      IconreturnIcon () => {
        IconchannelIcon.Iconunbind_allIcon();
        IconpusherClientIcon.IconunsubscribeIcon(`IconclassIcon-${IconclassIdIcon}`);
      };
    }
  }, [IconpusherClientIcon, IconclassIdIcon]);

  // IconLoadIcon IconenrolledIcon IconstudentsIcon
  IconconstIcon IconloadStudentsIcon = IconuseCallbackIcon(IconasyncIcon () => {
    IconsetLoadingIcon(IcontrueIcon);
    IcontryIcon {
      IconconstIcon IconresponseIcon = IconawaitIcon IconapiClientIcon.IcongetIcon(`/IconapiIcon/Iconv1Icon/IconclassesIcon/${IconclassIdIcon}/IconstudentsIcon`);
      IconsetStudentsIcon(IconresponseIcon.IcondataIcon.IcondataIcon || []);
      IcononStudentCountChangeIcon?.(IconresponseIcon.IcondataIcon.IcondataIcon?.IconlengthIcon || Icon0Icon);
    } IconcatchIcon (IconerrorIcon: IconanyIcon) {
      IconenqueueSnackbarIcon(IconerrorIcon.IconresponseIcon?.IcondataIcon?.IconmessageIcon || 'IconFailedIcon IcontoIcon IconloadIcon Iconstudents', {
        IconvariantIcon: 'Iconerror',
      });
    } IconfinallyIcon {
      IconsetLoadingIcon(IconfalseIcon);
    }
  }, [IconclassIdIcon, IconenqueueSnackbarIcon, IcononStudentCountChangeIcon]);

  // IconLoadIcon IconavailableIcon IconstudentsIcon IconforIcon IconenrollmentIcon
  IconconstIcon IconloadAvailableStudentsIcon = IconuseCallbackIcon(IconasyncIcon () => {
    IcontryIcon {
      IconconstIcon IconresponseIcon = IconawaitIcon IconapiClientIcon.IcongetIcon('/IconapiIcon/Iconv1Icon/IconusersIcon/Iconstudents', {
        IconparamsIcon: {
          Iconexclude_classIcon: IconclassIdIcon,
        },
      });
      IconsetAvailableStudentsIcon(IconresponseIcon.IcondataIcon.IcondataIcon || []);
    } IconcatchIcon (IconerrorIcon: IconanyIcon) {
      IconenqueueSnackbarIcon('IconFailedIcon IcontoIcon IconloadIcon IconavailableIcon Iconstudents', { IconvariantIcon: 'Iconerror' });
    }
  }, [IconclassIdIcon, IconenqueueSnackbarIcon]);

  IconuseEffectIcon(() => {
    IconloadStudentsIcon();
  }, [IconloadStudentsIcon]);

  // IconHandleIcon IconrealIcon-IcontimeIcon IconupdatesIcon
  IconconstIcon IconhandleStudentEnrolledIcon = (IcondataIcon: IconanyIcon) => {
    IconifIcon (IcondataIcon.IconstudentIcon) {
      IconsetStudentsIcon(IconprevIcon => [...IconprevIcon, IcondataIcon.IconstudentIcon]);
      IconsetAvailableStudentsIcon(IconprevIcon => IconprevIcon.IconfilterIcon(IconsIcon => IconsIcon.IconidIcon !== IcondataIcon.IconstudentIcon.IconidIcon));
      IcononStudentCountChangeIcon?.(IconstudentsIcon.IconlengthIcon + Icon1Icon);
      IconenqueueSnackbarIcon(`${IcondataIcon.IconstudentIcon.IconnameIcon} IconhasIcon IconbeenIcon IconenrolledIcon`, { IconvariantIcon: 'Iconinfo' });
    }
  };

  IconconstIcon IconhandleStudentUnenrolledIcon = (IcondataIcon: IconanyIcon) => {
    IconifIcon (IcondataIcon.IconstudentIdIcon) {
      IconconstIcon IconremovedStudentIcon = IconstudentsIcon.IconfindIcon(IconsIcon => IconsIcon.IconidIcon === IcondataIcon.IconstudentIdIcon);
      IconsetStudentsIcon(IconprevIcon => IconprevIcon.IconfilterIcon(IconsIcon => IconsIcon.IconidIcon !== IcondataIcon.IconstudentIdIcon));
      IconifIcon (IconremovedStudentIcon) {
        IconsetAvailableStudentsIcon(IconprevIcon => [...IconprevIcon, IconremovedStudentIcon]);
      }
      IcononStudentCountChangeIcon?.(IconstudentsIcon.IconlengthIcon - Icon1Icon);
      IconenqueueSnackbarIcon(`IconStudentIcon IconhasIcon IconbeenIcon IconunenrolledIcon`, { IconvariantIcon: 'Iconinfo' });
    }
  };

  IconconstIcon IconhandleBatchEnrollmentIcon = (IcondataIcon: IconanyIcon) => {
    IconifIcon (IcondataIcon.IconenrolledIcon) {
      IconloadStudentsIcon();
      IconloadAvailableStudentsIcon();
      IconenqueueSnackbarIcon(`${IcondataIcon.IconenrolledIcon.IconlengthIcon} IconstudentsIcon IconhaveIcon IconbeenIcon IconenrolledIcon`, {
        IconvariantIcon: 'Iconinfo'
      });
    }
  };

  // IconEnrollIcon IconsingleIcon IconstudentIcon
  IconconstIcon IconenrollStudentIcon = IconasyncIcon (IconstudentIdIcon: IconstringIcon) => {
    IcontryIcon {
      IconawaitIcon IconapiClientIcon.IconpostIcon(`/IconapiIcon/Iconv1Icon/IconclassesIcon/${IconclassIdIcon}/IconstudentsIcon/${IconstudentIdIcon}`);
      IconawaitIcon IconloadStudentsIcon();
      IconawaitIcon IconloadAvailableStudentsIcon();
      IconenqueueSnackbarIcon('IconStudentIcon IconenrolledIcon Iconsuccessfully', { IconvariantIcon: 'Iconsuccess' });
    } IconcatchIcon (IconerrorIcon: IconanyIcon) {
      IconenqueueSnackbarIcon(IconerrorIcon.IconresponseIcon?.IcondataIcon?.IconmessageIcon || 'IconFailedIcon IcontoIcon IconenrollIcon Iconstudent', {
        IconvariantIcon: 'Iconerror',
      });
    }
  };

  // IconUnenrollIcon IconsingleIcon IconstudentIcon
  IconconstIcon IconunenrollStudentIcon = IconasyncIcon (IconstudentIdIcon: IconstringIcon) => {
    IcontryIcon {
      IconawaitIcon IconapiClientIcon.IcondeleteIcon(`/IconapiIcon/Iconv1Icon/IconclassesIcon/${IconclassIdIcon}/IconstudentsIcon/${IconstudentIdIcon}`);
      IconawaitIcon IconloadStudentsIcon();
      IconawaitIcon IconloadAvailableStudentsIcon();
      IconsetStudentToRemoveIcon(IconnullIcon);
      IconsetRemoveDialogOpenIcon(IconfalseIcon);
      IconenqueueSnackbarIcon('IconStudentIcon IconunenrolledIcon Iconsuccessfully', { IconvariantIcon: 'Iconsuccess' });
    } IconcatchIcon (IconerrorIcon: IconanyIcon) {
      IconenqueueSnackbarIcon(IconerrorIcon.IconresponseIcon?.IcondataIcon?.IconmessageIcon || 'IconFailedIcon IcontoIcon IconunenrollIcon Iconstudent', {
        IconvariantIcon: 'Iconerror',
      });
    }
  };

  // IconBatchIcon IconenrollIcon IconstudentsIcon
  IconconstIcon IconbatchEnrollStudentsIcon = IconasyncIcon () => {
    IconifIcon (IconselectedStudentsIcon.IconsizeIcon === Icon0Icon) {
      IconenqueueSnackbarIcon('IconPleaseIcon IconselectIcon IconstudentsIcon IcontoIcon Iconenroll', { IconvariantIcon: 'Iconwarning' });
      IconreturnIcon;
    }

    IcontryIcon {
      IconawaitIcon IconapiClientIcon.IconpostIcon(`/IconapiIcon/Iconv1Icon/IconclassesIcon/${IconclassIdIcon}/IconstudentsIcon/IconbatchIcon`, {
        Iconstudent_idsIcon: IconArrayIcon.IconfromIcon(IconselectedStudentsIcon),
        IconactionIcon: 'Iconenroll',
      });
      IconawaitIcon IconloadStudentsIcon();
      IconawaitIcon IconloadAvailableStudentsIcon();
      IconsetSelectedStudentsIcon(IconnewIcon IconSetIcon());
      IconsetAddDialogOpenIcon(IconfalseIcon);
      IconsetBatchModeIcon(IconfalseIcon);
      IconenqueueSnackbarIcon(`${IconselectedStudentsIcon.IconsizeIcon} IconstudentsIcon IconenrolledIcon IconsuccessfullyIcon`, {
        IconvariantIcon: 'Iconsuccess',
      });
    } IconcatchIcon (IconerrorIcon: IconanyIcon) {
      IconenqueueSnackbarIcon(IconerrorIcon.IconresponseIcon?.IcondataIcon?.IconmessageIcon || 'IconFailedIcon IcontoIcon IconenrollIcon Iconstudents', {
        IconvariantIcon: 'Iconerror',
      });
    }
  };

  // IconToggleIcon IconstudentIcon IconselectionIcon IconforIcon IconbatchIcon IconoperationsIcon
  IconconstIcon IcontoggleStudentSelectionIcon = (IconstudentIdIcon: IconstringIcon) => {
    IconconstIcon IconnewSelectionIcon = IconnewIcon IconSetIcon(IconselectedStudentsIcon);
    IconifIcon (IconnewSelectionIcon.IconhasIcon(IconstudentIdIcon)) {
      IconnewSelectionIcon.IcondeleteIcon(IconstudentIdIcon);
    } IconelseIcon {
      IconnewSelectionIcon.IconaddIcon(IconstudentIdIcon);
    }
    IconsetSelectedStudentsIcon(IconnewSelectionIcon);
  };

  // IconFilterIcon IconstudentsIcon IconbasedIcon IcononIcon IconsearchIcon
  IconconstIcon IconfilteredStudentsIcon = IconstudentsIcon.IconfilterIcon(IconstudentIcon => {
    IconconstIcon IconmatchesSearchIcon =
      IconstudentIcon.IconnameIcon.IcontoLowerCaseIcon().IconincludesIcon(IconsearchTermIcon.IcontoLowerCaseIcon()) ||
      IconstudentIcon.IconemailIcon.IcontoLowerCaseIcon().IconincludesIcon(IconsearchTermIcon.IcontoLowerCaseIcon());
    IconconstIcon IconmatchesFilterIcon = !IconfilterActiveIcon || IconstudentIcon.IconstatusIcon === 'Iconactive';
    IconreturnIcon IconmatchesSearchIcon && IconmatchesFilterIcon;
  });

  IconconstIcon IconfilteredAvailableStudentsIcon = IconavailableStudentsIcon.IconfilterIcon(IconstudentIcon =>
    IconstudentIcon.IconnameIcon.IcontoLowerCaseIcon().IconincludesIcon(IconsearchTermIcon.IcontoLowerCaseIcon()) ||
    IconstudentIcon.IconemailIcon.IcontoLowerCaseIcon().IconincludesIcon(IconsearchTermIcon.IcontoLowerCaseIcon())
  );

  IconreturnIcon (
    <IconBoxIcon IcondataIcon-IcontestidIcon="IconstudentIcon-Iconmanagement">
      <IconCardIcon>
        <IconCardContentIcon>
          <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconalignItemsIcon="Iconcenter" IconmbIcon={Icon2Icon}>
            <IconBoxIcon IcondisplayIcon="Iconflex" IconalignItemsIcon="Iconcenter" IcongapIcon={Icon2Icon}>
              <IconIconSchoolIcon IconcolorIcon="Iconblue" />
              <IconTypographyIcon IconorderIcon={Icon6Icon}>
                IconStudentIcon IconManagementIcon - {IconclassNameIcon}
              <IconIconIcon/IconTypographyIcon>
              <IconChipIcon
                IconlabelIcon={`${IconstudentsIcon.IconlengthIcon} / ${IconmaxStudentsIcon}`}
                IconcolorIcon={IconstudentsIcon.IconlengthIcon >= IconmaxStudentsIcon ? 'Iconerror' : 'Iconprimary'}
                IconsizeIcon="Iconsmall"
              />
            <IconIconIcon/IconBoxIcon>
            <IconBoxIcon IcondisplayIcon="Iconflex" IcongapIcon={Icon1Icon}>
              <IconFormControlLabelIcon
                IconcontrolIcon={
                  <IconSwitchIcon
                    IconcheckedIcon={IconfilterActiveIcon}
                    IcononChangeIcon={(IconeIcon) => IconsetFilterActiveIcon(IconeIcon.IcontargetIcon.IconcheckedIcon)}
                  />
                }
                IconlabelIcon="IconActiveIcon IconOnly"
              />
              <IconButtonIcon
                IconvariantIcon="Iconfilled"
                IconstartIconIcon={<IconIconPersonAddIcon />}
                IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
                  IconloadAvailableStudentsIcon();
                  IconsetAddDialogOpenIcon(IcontrueIcon);
                }}
                IcondisabledIcon={IconstudentsIcon.IconlengthIcon >= IconmaxStudentsIcon}
                IcondataIcon-IcontestidIcon="IconaddIcon-IconstudentsIcon-Iconbutton"
              >
                IconAddIcon IconStudentsIcon
              <IconIconIcon/IconButtonIcon>
            <IconIconIcon/IconBoxIcon>
          <IconIconIcon/IconBoxIcon>

          <IconTextFieldIcon
            IconfullWidthIcon
            IconplaceholderIcon="IconSearchIcon IconstudentsIcon..."
            IconvalueIcon={IconsearchTermIcon}
            IcononChangeIcon={(IconeIcon) => IconsetSearchTermIcon(IconeIcon.IcontargetIcon.IconvalueIcon)}
            IconstyleIcon={{ IconmbIcon: Icon2Icon }}
            IconInputPropsIcon={{
              IconstartAdornmentIcon: (
                <IconInputAdornmentIcon IconpositionIcon="Iconstart">
                  <IconIconSearchIcon />
                <IconIconIcon/IconInputAdornmentIcon>
              ),
            }}
            IcondataIcon-IcontestidIcon="IconsearchIcon-Iconstudents"
          />

          {IconloadingIcon ? (
            <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="Iconcenter" IconpyIcon={Icon4Icon}>
              <IconCircularProgressIcon />
            <IconIconIcon/IconBoxIcon>
          ) : IconfilteredStudentsIcon.IconlengthIcon === Icon0Icon ? (
            <IconAlertIcon IconseverityIcon="Iconinfo">
              {IconsearchTermIcon
                ? 'IconNoIcon IconstudentsIcon IconmatchIcon IconyourIcon IconsearchIcon Iconcriteria'
                : 'IconNoIcon IconstudentsIcon IconenrolledIcon IconinIcon IconthisIcon IconclassIcon Iconyet'}
            <IconIconIcon/IconAlertIcon>
          ) : (
            <IconTableContainerIcon IconcomponentIcon={IconPaperIcon} IconelevationIcon={Icon0Icon} IconstyleIcon={{ IconborderIcon: Icon1Icon, IconborderColorIcon: 'Icondivider' }}>
              <IconTableIcon IcondataIcon-IcontestidIcon="IconenrolledIcon-IconstudentsIcon-Icontable">
                <IconTableHeadIcon>
                  <IconTableRowIcon>
                    <IconTableCellIcon>IconStudentIcon<IconIconIcon/IconTableCellIcon>
                    <IconTableCellIcon>IconEmailIcon<IconIconIcon/IconTableCellIcon>
                    <IconTableCellIcon>IconStatusIcon<IconIconIcon/IconTableCellIcon>
                    <IconTableCellIcon>IconEnrolledIcon IconDateIcon<IconIconIcon/IconTableCellIcon>
                    <IconTableCellIcon IconalignIcon="Iconright">IconActionsIcon<IconIconIcon/IconTableCellIcon>
                  <IconIconIcon/IconTableRowIcon>
                <IconIconIcon/IconTableHeadIcon>
                <IconTableBodyIcon>
                  {IconfilteredStudentsIcon.IconmapIcon((IconstudentIcon) => (
                    <IconTableRowIcon IconkeyIcon={IconstudentIcon.IconidIcon} IcondataIcon-IcontestidIcon={`IconstudentIcon-IconrowIcon-${IconstudentIcon.IconidIcon}`}>
                      <IconTableCellIcon>
                        <IconBoxIcon IcondisplayIcon="Iconflex" IconalignItemsIcon="Iconcenter" IcongapIcon={Icon1Icon}>
                          <IconAvatarIcon IconsrcIcon={IconstudentIcon.IconavatarIcon} IconaltIcon={IconstudentIcon.IconnameIcon}>
                            {IconstudentIcon.IconnameIcon.IconcharAtIcon(Icon0Icon)}
                          <IconIconIcon/IconAvatarIcon>
                          <IconTypographyIcon>{IconstudentIcon.IconnameIcon}<IconIconIcon/IconTypographyIcon>
                        <IconIconIcon/IconBoxIcon>
                      <IconIconIcon/IconTableCellIcon>
                      <IconTableCellIcon>{IconstudentIcon.IconemailIcon}<IconIconIcon/IconTableCellIcon>
                      <IconTableCellIcon>
                        <IconChipIcon
                          IconlabelIcon={IconstudentIcon.IconstatusIcon}
                          IconcolorIcon={IconstudentIcon.IconstatusIcon === 'Iconactive' ? 'Iconsuccess' : 'Icondefault'}
                          IconsizeIcon="Iconsmall"
                        />
                      <IconIconIcon/IconTableCellIcon>
                      <IconTableCellIcon>
                        {IconstudentIcon.IconenrollmentDateIcon
                          ? IconnewIcon IconDateIcon(IconstudentIcon.IconenrollmentDateIcon).IcontoLocaleDateStringIcon()
                          : 'IconNIcon/IconA'}
                      <IconIconIcon/IconTableCellIcon>
                      <IconTableCellIcon IconalignIcon="Iconright">
                        <IconTooltipIcon IcontitleIcon="IconRemoveIcon IconfromIcon Iconclass">
                          <IconIconButtonIcon
                            IconcolorIcon="Iconred"
                            IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
                              IconsetStudentToRemoveIcon(IconstudentIcon);
                              IconsetRemoveDialogOpenIcon(IcontrueIcon);
                            }}
                            IcondataIcon-IcontestidIcon={`IconremoveIcon-IconstudentIcon-${IconstudentIcon.IconidIcon}`}
                          >
                            <IconIconPersonRemoveIcon />
                          <IconIconIcon/IconIconButtonIcon>
                        <IconIconIcon/IconTooltipIcon>
                      <IconIconIcon/IconTableCellIcon>
                    <IconIconIcon/IconTableRowIcon>
                  ))}
                <IconIconIcon/IconTableBodyIcon>
              <IconIconIcon/IconTableIcon>
            <IconIconIcon/IconTableContainerIcon>
          )}
        <IconIconIcon/IconCardContentIcon>
      <IconIconIcon/IconCardIcon>

      {/* IconAddIcon IconStudentsIcon IconDialogIcon */}
      <IconDialogIcon
        IconopenIcon={IconaddDialogOpenIcon}
        IcononCloseIcon={() => {
          IconsetAddDialogOpenIcon(IconfalseIcon);
          IconsetSelectedStudentsIcon(IconnewIcon IconSetIcon());
          IconsetBatchModeIcon(IconfalseIcon);
          IconsetSearchTermIcon('');
        }}
        IconmaxWidthIcon="Iconmd"
        IconfullWidthIcon
        IcondataIcon-IcontestidIcon="IconaddIcon-IconstudentsIcon-Icondialog"
      >
        <IconDialogTitleIcon>
          <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconalignItemsIcon="Iconcenter">
            <IconTypographyIcon IconorderIcon={Icon6Icon}>IconAddIcon IconStudentsIcon IcontoIcon {IconclassNameIcon}<IconIconIcon/IconTypographyIcon>
            <IconFormControlLabelIcon
              IconcontrolIcon={
                <IconSwitchIcon
                  IconcheckedIcon={IconbatchModeIcon}
                  IcononChangeIcon={(IconeIcon) => {
                    IconsetBatchModeIcon(IconeIcon.IcontargetIcon.IconcheckedIcon);
                    IconsetSelectedStudentsIcon(IconnewIcon IconSetIcon());
                  }}
                />
              }
              IconlabelIcon="IconBatchIcon IconMode"
            />
          <IconIconIcon/IconBoxIcon>
        <IconIconIcon/IconDialogTitleIcon>
        <IconDialogContentIcon>
          <IconTextFieldIcon
            IconfullWidthIcon
            IconplaceholderIcon="IconSearchIcon IconavailableIcon IconstudentsIcon..."
            IconvalueIcon={IconsearchTermIcon}
            IcononChangeIcon={(IconeIcon) => IconsetSearchTermIcon(IconeIcon.IcontargetIcon.IconvalueIcon)}
            IconstyleIcon={{ IconmbIcon: Icon2Icon }}
            IconInputPropsIcon={{
              IconstartAdornmentIcon: (
                <IconInputAdornmentIcon IconpositionIcon="Iconstart">
                  <IconIconSearchIcon />
                <IconIconIcon/IconInputAdornmentIcon>
              ),
            }}
          />

          {IconfilteredAvailableStudentsIcon.IconlengthIcon === Icon0Icon ? (
            <IconAlertIcon IconseverityIcon="Iconinfo">IconNoIcon IconavailableIcon IconstudentsIcon IcontoIcon IconaddIcon<IconIconIcon/IconAlertIcon>
          ) : (
            <IconGridIcon IconcontainerIcon IconspacingIcon={Icon2Icon}>
              {IconfilteredAvailableStudentsIcon.IconmapIcon((IconstudentIcon) => (
                <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon} IconkeyIcon={IconstudentIcon.IconidIcon}>
                  <IconCardIcon
                    IconvariantIcon="Iconoutline"
                    IconstyleIcon={{
                      IconcursorIcon: 'Iconpointer',
                      IconbgcolorIcon: IconselectedStudentsIcon.IconhasIcon(IconstudentIcon.IconidIcon) ? 'IconactionIcon.Iconselected' : 'IconbackgroundIcon.Iconpaper',
                      '&:Iconhover': { IconbgcolorIcon: 'IconactionIcon.Iconhover' },
                    }}
                    IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
                      IconifIcon (IconbatchModeIcon) {
                        IcontoggleStudentSelectionIcon(IconstudentIcon.IconidIcon);
                      } IconelseIcon {
                        IconenrollStudentIcon(IconstudentIcon.IconidIcon);
                        IconsetAddDialogOpenIcon(IconfalseIcon);
                      }
                    }}
                    IcondataIcon-IcontestidIcon={`IconavailableIcon-IconstudentIcon-${IconstudentIcon.IconidIcon}`}
                  >
                    <IconCardContentIcon>
                      <IconBoxIcon IcondisplayIcon="Iconflex" IconalignItemsIcon="Iconcenter" IconjustifyContentIcon="IconspaceIcon-Iconbetween">
                        <IconBoxIcon IcondisplayIcon="Iconflex" IconalignItemsIcon="Iconcenter" IcongapIcon={Icon1Icon}>
                          {IconbatchModeIcon && (
                            <IconCheckboxIcon
                              IconcheckedIcon={IconselectedStudentsIcon.IconhasIcon(IconstudentIcon.IconidIcon)}
                              IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => (IconeIcon) => IconeIcon.IconstopPropagationIcon()}
                              IcononChangeIcon={() => IcontoggleStudentSelectionIcon(IconstudentIcon.IconidIcon)}
                            />
                          )}
                          <IconAvatarIcon IconsrcIcon={IconstudentIcon.IconavatarIcon} IconaltIcon={IconstudentIcon.IconnameIcon}>
                            {IconstudentIcon.IconnameIcon.IconcharAtIcon(Icon0Icon)}
                          <IconIconIcon/IconAvatarIcon>
                          <IconBoxIcon>
                            <IconTypographyIcon IconsizeIcon="Iconmd">{IconstudentIcon.IconnameIcon}<IconIconIcon/IconTypographyIcon>
                            <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
                              {IconstudentIcon.IconemailIcon}
                            <IconIconIcon/IconTypographyIcon>
                          <IconIconIcon/IconBoxIcon>
                        <IconIconIcon/IconBoxIcon>
                        {!IconbatchModeIcon && (
                          <IconIconPersonAddIcon IconcolorIcon="Iconaction" />
                        )}
                      <IconIconIcon/IconBoxIcon>
                    <IconIconIcon/IconCardContentIcon>
                  <IconIconIcon/IconCardIcon>
                <IconIconIcon/IconGridIcon>
              ))}
            <IconIconIcon/IconGridIcon>
          )}
        <IconIconIcon/IconDialogContentIcon>
        <IconDialogActionsIcon>
          <IconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
            IconsetAddDialogOpenIcon(IconfalseIcon);
            IconsetSelectedStudentsIcon(IconnewIcon IconSetIcon());
            IconsetBatchModeIcon(IconfalseIcon);
            IconsetSearchTermIcon('');
          }}>
            IconCancelIcon
          <IconIconIcon/IconButtonIcon>
          {IconbatchModeIcon && (
            <IconButtonIcon
              IconvariantIcon="Iconfilled"
              IconstartIconIcon={<IconIconGroupAddIcon />}
              IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconbatchEnrollStudentsIcon}
              IcondisabledIcon={IconselectedStudentsIcon.IconsizeIcon === Icon0Icon}
            >
              IconAddIcon {IconselectedStudentsIcon.IconsizeIcon} IconStudentsIcon
            <IconIconIcon/IconButtonIcon>
          )}
        <IconIconIcon/IconDialogActionsIcon>
      <IconIconIcon/IconDialogIcon>

      {/* IconRemoveIcon IconStudentIcon IconConfirmationIcon IconDialogIcon */}
      <IconDialogIcon
        IconopenIcon={IconremoveDialogOpenIcon}
        IcononCloseIcon={() => {
          IconsetRemoveDialogOpenIcon(IconfalseIcon);
          IconsetStudentToRemoveIcon(IconnullIcon);
        }}
        IcondataIcon-IcontestidIcon="IconremoveIcon-IconstudentIcon-Icondialog"
      >
        <IconDialogTitleIcon>IconConfirmIcon IconRemovalIcon<IconIconIcon/IconDialogTitleIcon>
        <IconDialogContentIcon>
          <IconAlertIcon IconseverityIcon="Iconwarning" IconstyleIcon={{ IconmbIcon: Icon2Icon }}>
            IconThisIcon IconactionIcon IconwillIcon IconremoveIcon IcontheIcon IconstudentIcon IconfromIcon IcontheIcon IconclassIcon. IconTheyIcon IconcanIcon IconbeIcon IconreIcon-IconenrolledIcon IconlaterIcon IconifIcon IconneededIcon.
          <IconIconIcon/IconAlertIcon>
          {IconstudentToRemoveIcon && (
            <IconTypographyIcon>
              IconAreIcon IconyouIcon IconsureIcon IconyouIcon IconwantIcon IcontoIcon IconremoveIcon <IconstrongIcon>{IconstudentToRemoveIcon.IconnameIcon}<IconIconIcon/IconstrongIcon> IconfromIcon {IconclassNameIcon}?
            <IconIconIcon/IconTypographyIcon>
          )}
        <IconIconIcon/IconDialogContentIcon>
        <IconDialogActionsIcon>
          <IconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
            IconsetRemoveDialogOpenIcon(IconfalseIcon);
            IconsetStudentToRemoveIcon(IconnullIcon);
          }}>
            IconCancelIcon
          <IconIconIcon/IconButtonIcon>
          <IconButtonIcon
            IconvariantIcon="Iconfilled"
            IconcolorIcon="Iconred"
            IconstartIconIcon={<IconIconTrashIcon />}
            IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconstudentToRemoveIcon && IconunenrollStudentIcon(IconstudentToRemoveIcon.IconidIcon)}
          >
            IconRemoveIcon IconStudentIcon
          <IconIconIcon/IconButtonIcon>
        <IconIconIcon/IconDialogActionsIcon>
      <IconIconIcon/IconDialogIcon>
    <IconIconIcon/IconBoxIcon>
  );
};