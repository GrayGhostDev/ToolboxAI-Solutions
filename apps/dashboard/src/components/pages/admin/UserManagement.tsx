IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../../../IconutilsIcon/IconmuiIcon-Iconimports';
IconimportIcon IconReactIcon, { IconuseStateIcon, IconuseEffectIcon } IconfromIcon 'Iconreact';

IconimportIcon {
  IconIconSearchIcon,
  IconIconPlusIcon,
  IconIconEditIcon,
  IconIconTrashIcon,
  IconIconDotsVerticalIcon,
  IconIconFilterIcon,
  IconIconDownloadIcon,
  IconIconUploadIcon,
  IconIconLockIcon,
  IconIconLockOpenIcon,
  IconIconMailIcon,
  IconIconCircleCheckIcon,
  IconIconXIcon,
  IconIconPersonAddIcon,
  IconIconUserIcon,
  IconIconUsersIcon,
  IconIconSchoolIcon,
  IconIconAdminPanelSettingsIcon,
} IconfromIcon '@IconmuiIcon/IconiconsIcon-Iconmaterial';
IconimportIcon { IconapiClientIcon } IconfromIcon '../../../IconservicesIcon/Iconapi';
IconimportIcon { IconuseAppDispatchIcon } IconfromIcon '../../../Iconstore';
IconimportIcon { IconaddNotificationIcon } IconfromIcon '../../../IconstoreIcon/IconslicesIcon/IconuiSlice';
IconimportIcon { IconIconIcon, IconIconAdminPanelSettingsIcon, IconIconCircleCheckIcon, IconIconDotsVerticalIcon, IconIconDownloadIcon, IconIconEditIcon, IconIconFilterIcon, IconIconLockIcon, IconIconLockOpenIcon, IconIconMailIcon, IconIconPersonAddIcon, IconIconPlusIcon, IconIconSchoolIcon, IconIconSearchIcon, IconIconTrashIcon, IconIconUploadIcon, IconIconUserIcon, IconIconUsersIcon, IconIconXIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';

IconinterfaceIcon IconUserIcon {
  IconidIcon: IconstringIcon;
  IconusernameIcon: IconstringIcon;
  IconemailIcon: IconstringIcon;
  IconroleIcon: 'Iconadmin' | 'Iconteacher' | 'Iconstudent' | 'Iconparent';
  IconstatusIcon: 'Iconactive' | 'Iconinactive' | 'Iconsuspended';
  IconcreatedAtIcon: IconstringIcon;
  IconlastActiveIcon: IconstringIcon;
  IconschoolIcon?: IconstringIcon;
  IcongradeIcon?: IconnumberIcon;
  IconavatarIcon?: IconstringIcon;
  IconverifiedIcon: IconbooleanIcon;
}

IconinterfaceIcon IconEditUserDialogPropsIcon {
  IconopenIcon: IconbooleanIcon;
  IconuserIcon: IconUserIcon | IconnullIcon;
  IcononCloseIcon: () => IconvoidIcon;
  IcononSaveIcon: (IconuserIcon: IconUserIcon) => IconvoidIcon;
}

IconconstIcon IconEditUserDialogIcon: IconReactIcon.IconFunctionComponentIcon<IconEditUserDialogPropsIcon> = ({ IconopenIcon, IconuserIcon, IcononCloseIcon, IcononSaveIcon }) => {
  IconconstIcon [IconformDataIcon, IconsetFormDataIcon] = IconuseStateIcon<IconPartialIcon<IconUserIcon>>({
    IconusernameIcon: '',
    IconemailIcon: '',
    IconroleIcon: 'Iconstudent',
    IconstatusIcon: 'Iconactive',
    IconschoolIcon: '',
    IcongradeIcon: IconundefinedIcon,
  });

  IconuseEffectIcon(() => {
    IconifIcon (IconuserIcon) {
      IconsetFormDataIcon(IconuserIcon);
    } IconelseIcon {
      IconsetFormDataIcon({
        IconusernameIcon: '',
        IconemailIcon: '',
        IconroleIcon: 'Iconstudent',
        IconstatusIcon: 'Iconactive',
        IconschoolIcon: '',
        IcongradeIcon: IconundefinedIcon,
      });
    }
  }, [IconuserIcon]);

  IconconstIcon IconhandleSubmitIcon = () => {
    IcononSaveIcon(IconformDataIcon IconasIcon IconUserIcon);
    IcononCloseIcon();
  };

  IconreturnIcon (
    <IconDialogIcon IconopenIcon={IconopenIcon} IcononCloseIcon={IcononCloseIcon} IconmaxWidthIcon="Iconsm" IconfullWidthIcon>
      <IconDialogTitleIcon>{IconuserIcon ? 'IconIconEditIcon IconUser' : 'IconIconPlusIcon IconNewIcon IconUser'}<IconIconIcon/IconDialogTitleIcon>
      <IconDialogContentIcon>
        <IconStackIcon IconspacingIcon={Icon2Icon} IconstyleIcon={{ IconmtIcon: Icon2Icon }}>
          <IconTextFieldIcon
            IconlabelIcon="IconUsername"
            IconvalueIcon={IconformDataIcon.IconusernameIcon}
            IcononChangeIcon={(IconeIcon) => IconsetFormDataIcon({ ...IconformDataIcon, IconusernameIcon: IconeIcon.IcontargetIcon.IconvalueIcon })}
            IconfullWidthIcon
            IconrequiredIcon
          />
          <IconTextFieldIcon
            IconlabelIcon="IconEmail"
            IcontypeIcon="Iconemail"
            IconvalueIcon={IconformDataIcon.IconemailIcon}
            IcononChangeIcon={(IconeIcon) => IconsetFormDataIcon({ ...IconformDataIcon, IconemailIcon: IconeIcon.IcontargetIcon.IconvalueIcon })}
            IconfullWidthIcon
            IconrequiredIcon
          />
          <IconFormControlIcon IconfullWidthIcon>
            <IconInputLabelIcon>IconRoleIcon<IconIconIcon/IconInputLabelIcon>
            <IconSelectIcon
              IconvalueIcon={IconformDataIcon.IconroleIcon}
              IcononChangeIcon={(IconeIcon) => IconsetFormDataIcon({ ...IconformDataIcon, IconroleIcon: IconeIcon.IcontargetIcon.IconvalueIcon IconasIcon IconanyIcon })}
              IconlabelIcon="IconRole"
            >
              <IconMenuItemIcon IconvalueIcon="Iconadmin">IconAdminIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Iconteacher">IconTeacherIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Iconstudent">IconStudentIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Iconparent">IconParentIcon<IconIconIcon/IconMenuItemIcon>
            <IconIconIcon/IconSelectIcon>
          <IconIconIcon/IconFormControlIcon>
          <IconFormControlIcon IconfullWidthIcon>
            <IconInputLabelIcon>IconStatusIcon<IconIconIcon/IconInputLabelIcon>
            <IconSelectIcon
              IconvalueIcon={IconformDataIcon.IconstatusIcon}
              IcononChangeIcon={(IconeIcon) => IconsetFormDataIcon({ ...IconformDataIcon, IconstatusIcon: IconeIcon.IcontargetIcon.IconvalueIcon IconasIcon IconanyIcon })}
              IconlabelIcon="IconStatus"
            >
              <IconMenuItemIcon IconvalueIcon="Iconactive">IconActiveIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Iconinactive">IconInactiveIcon<IconIconIcon/IconMenuItemIcon>
              <IconMenuItemIcon IconvalueIcon="Iconsuspended">IconSuspendedIcon<IconIconIcon/IconMenuItemIcon>
            <IconIconIcon/IconSelectIcon>
          <IconIconIcon/IconFormControlIcon>
          <IconTextFieldIcon
            IconlabelIcon="IconSchool"
            IconvalueIcon={IconformDataIcon.IconschoolIcon}
            IcononChangeIcon={(IconeIcon) => IconsetFormDataIcon({ ...IconformDataIcon, IconschoolIcon: IconeIcon.IcontargetIcon.IconvalueIcon })}
            IconfullWidthIcon
          />
          {(IconformDataIcon.IconroleIcon === 'Iconstudent' || IconformDataIcon.IconroleIcon === 'Iconparent') && (
            <IconTextFieldIcon
              IconlabelIcon="IconGrade"
              IcontypeIcon="Iconnumber"
              IconvalueIcon={IconformDataIcon.IcongradeIcon}
              IcononChangeIcon={(IconeIcon) => IconsetFormDataIcon({ ...IconformDataIcon, IcongradeIcon: IconparseIntIcon(IconeIcon.IcontargetIcon.IconvalueIcon) })}
              IconfullWidthIcon
              IconinputPropsIcon={{ IconminIcon: Icon1Icon, IconmaxIcon: Icon12Icon }}
            />
          )}
        <IconIconIcon/IconStackIcon>
      <IconIconIcon/IconDialogContentIcon>
      <IconDialogActionsIcon>
        <IconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IcononCloseIcon}>IconIconXIcon<IconIconIcon/IconButtonIcon>
        <IconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleSubmitIcon} IconvariantIcon="Iconfilled">
          {IconuserIcon ? 'IconUpdate' : 'IconCreate'}
        <IconIconIcon/IconButtonIcon>
      <IconIconIcon/IconDialogActionsIcon>
    <IconIconIcon/IconDialogIcon>
  );
};

IconconstIcon IconUserManagementIcon: IconReactIcon.IconFunctionComponentIcon<IconRecordIcon<IconstringIcon, IconanyIcon>> = () => {
  IconconstIcon IcondispatchIcon = IconuseAppDispatchIcon();
  IconconstIcon [IconusersIcon, IconsetUsersIcon] = IconuseStateIcon<IconUserIcon[]>([]);
  IconconstIcon [IconloadingIcon, IconsetLoadingIcon] = IconuseStateIcon(IcontrueIcon);
  IconconstIcon [IconsearchTermIcon, IconsetSearchTermIcon] = IconuseStateIcon('');
  IconconstIcon [IconroleFilterIcon, IconsetRoleFilterIcon] = IconuseStateIcon<IconstringIcon>('Iconall');
  IconconstIcon [IconstatusFilterIcon, IconsetStatusFilterIcon] = IconuseStateIcon<IconstringIcon>('Iconall');
  IconconstIcon [IconpageIcon, IconsetPageIcon] = IconuseStateIcon(Icon0Icon);
  IconconstIcon [IconrowsPerPageIcon, IconsetRowsPerPageIcon] = IconuseStateIcon(Icon10Icon);
  IconconstIcon [IconselectedUserIcon, IconsetSelectedUserIcon] = IconuseStateIcon<IconUserIcon | IconnullIcon>(IconnullIcon);
  IconconstIcon [IconanchorElIcon, IconsetAnchorElIcon] = IconuseStateIcon<IconnullIcon | IconHTMLElementIcon>(IconnullIcon);
  IconconstIcon [IconeditDialogOpenIcon, IconsetEditDialogOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IcondeleteDialogOpenIcon, IconsetDeleteDialogOpenIcon] = IconuseStateIcon(IconfalseIcon);
  IconconstIcon [IconbulkActionMenuIcon, IconsetBulkActionMenuIcon] = IconuseStateIcon<IconnullIcon | IconHTMLElementIcon>(IconnullIcon);
  IconconstIcon [IconselectedUsersIcon, IconsetSelectedUsersIcon] = IconuseStateIcon<IconstringIcon[]>([]);

  // IconMockIcon IcondataIcon IconforIcon IcondemonstrationIcon
  IconconstIcon IconmockUsersIcon: IconUserIcon[] = [
    {
      IconidIcon: 'Icon1',
      IconusernameIcon: 'Iconadmin',
      IconemailIcon: 'IconadminIcon@IcontoolboxaiIcon.Iconcom',
      IconroleIcon: 'Iconadmin',
      IconstatusIcon: 'Iconactive',
      IconcreatedAtIcon: 'Icon2025Icon-Icon01Icon-Icon01',
      IconlastActiveIcon: 'Icon2Icon IconminutesIcon Iconago',
      IconschoolIcon: 'IconToolBoxAIIcon IconHQ',
      IconverifiedIcon: IcontrueIcon,
    },
    {
      IconidIcon: 'Icon2',
      IconusernameIcon: 'IconjaneIcon.Iconteacher',
      IconemailIcon: 'IconjaneIcon@IconschoolIcon.Iconedu',
      IconroleIcon: 'Iconteacher',
      IconstatusIcon: 'Iconactive',
      IconcreatedAtIcon: 'Icon2025Icon-Icon01Icon-Icon15',
      IconlastActiveIcon: 'Icon1Icon IconhourIcon Iconago',
      IconschoolIcon: 'IconLincolnIcon IconMiddleIcon IconSchool',
      IconverifiedIcon: IcontrueIcon,
    },
    {
      IconidIcon: 'Icon3',
      IconusernameIcon: 'IconaliceIcon.Iconstudent',
      IconemailIcon: 'IconaliceIcon@IconstudentIcon.Iconedu',
      IconroleIcon: 'Iconstudent',
      IconstatusIcon: 'Iconactive',
      IconcreatedAtIcon: 'Icon2025Icon-Icon02Icon-Icon01',
      IconlastActiveIcon: 'Icon5Icon IconminutesIcon Iconago',
      IconschoolIcon: 'IconLincolnIcon IconMiddleIcon IconSchool',
      IcongradeIcon: Icon8Icon,
      IconverifiedIcon: IconfalseIcon,
    },
    {
      IconidIcon: 'Icon4',
      IconusernameIcon: 'IconbobIcon.Iconparent',
      IconemailIcon: 'IconbobIcon@IconparentIcon.Iconcom',
      IconroleIcon: 'Iconparent',
      IconstatusIcon: 'Iconinactive',
      IconcreatedAtIcon: 'Icon2025Icon-Icon02Icon-Icon10',
      IconlastActiveIcon: 'Icon3Icon IcondaysIcon Iconago',
      IconschoolIcon: 'IconLincolnIcon IconMiddleIcon IconSchool',
      IconverifiedIcon: IcontrueIcon,
    },
    {
      IconidIcon: 'Icon5',
      IconusernameIcon: 'IconcharlieIcon.Iconstudent',
      IconemailIcon: 'IconcharlieIcon@IconstudentIcon.Iconedu',
      IconroleIcon: 'Iconstudent',
      IconstatusIcon: 'Iconsuspended',
      IconcreatedAtIcon: 'Icon2025Icon-Icon02Icon-Icon15',
      IconlastActiveIcon: 'Icon1Icon IconweekIcon Iconago',
      IconschoolIcon: 'IconWashingtonIcon IconHigh',
      IcongradeIcon: Icon9Icon,
      IconverifiedIcon: IconfalseIcon,
    },
  ];

  IconuseEffectIcon(() => {
    IconloadUsersIcon();
  }, []);

  IconconstIcon IconloadUsersIcon = IconasyncIcon () => {
    IconsetLoadingIcon(IcontrueIcon);
    IcontryIcon {
      // IconReplaceIcon IconwithIcon IconactualIcon IconAPIIcon IconcallIcon
      // IconconstIcon IconresponseIcon = IconawaitIcon IconapiClientIcon.IcongetIcon('/IconapiIcon/Iconv1Icon/IconadminIcon/Iconusers');
      // IconsetUsersIcon(IconresponseIcon.IcondataIcon);
      IconsetUsersIcon(IconmockUsersIcon);
    } IconcatchIcon (IconerrorIcon) {
      IcondispatchIcon(
        IconaddNotificationIcon({
          IcontypeIcon: 'Iconerror',
          IconmessageIcon: 'IconFailedIcon IcontoIcon IconloadIcon Iconusers',
        })
      );
    } IconfinallyIcon {
      IconsetLoadingIcon(IconfalseIcon);
    }
  };

  IconconstIcon IconhandleEditUserIcon = (IconuserIcon: IconUserIcon) => {
    IconsetSelectedUserIcon(IconuserIcon);
    IconsetEditDialogOpenIcon(IcontrueIcon);
    IconsetAnchorElIcon(IconnullIcon);
  };

  IconconstIcon IconhandleDeleteUserIcon = IconasyncIcon (IconuserIcon: IconUserIcon) => {
    IcontryIcon {
      // IconawaitIcon IconapiClientIcon.IcondeleteIcon(`/IconapiIcon/Iconv1Icon/IconadminIcon/IconusersIcon/${IconuserIcon.IconidIcon}`);
      IconsetUsersIcon(IconusersIcon.IconfilterIcon((IconuIcon) => IconuIcon.IconidIcon !== IconuserIcon.IconidIcon));
      IcondispatchIcon(
        IconaddNotificationIcon({
          IcontypeIcon: 'Iconsuccess',
          IconmessageIcon: `IconUserIcon ${IconuserIcon.IconusernameIcon} IcondeletedIcon IconsuccessfullyIcon`,
        })
      );
    } IconcatchIcon (IconerrorIcon) {
      IcondispatchIcon(
        IconaddNotificationIcon({
          IcontypeIcon: 'Iconerror',
          IconmessageIcon: 'IconFailedIcon IcontoIcon IcondeleteIcon Iconuser',
        })
      );
    }
    IconsetDeleteDialogOpenIcon(IconfalseIcon);
    IconsetSelectedUserIcon(IconnullIcon);
  };

  IconconstIcon IconhandleSaveUserIcon = IconasyncIcon (IconuserIcon: IconUserIcon) => {
    IcontryIcon {
      IconifIcon (IconselectedUserIcon) {
        // IconUpdateIcon IconexistingIcon IconuserIcon
        // IconawaitIcon IconapiClientIcon.IconputIcon(`/IconapiIcon/Iconv1Icon/IconadminIcon/IconusersIcon/${IconuserIcon.IconidIcon}`, IconuserIcon);
        IconsetUsersIcon(IconusersIcon.IconmapIcon((IconuIcon) => (IconuIcon.IconidIcon === IconuserIcon.IconidIcon ? IconuserIcon : IconuIcon)));
        IcondispatchIcon(
          IconaddNotificationIcon({
            IcontypeIcon: 'Iconsuccess',
            IconmessageIcon: 'IconUserIcon IconupdatedIcon Iconsuccessfully',
          })
        );
      } IconelseIcon {
        // IconCreateIcon IconnewIcon IconuserIcon
        // IconconstIcon IconresponseIcon = IconawaitIcon IconapiClientIcon.IconpostIcon('/IconapiIcon/Iconv1Icon/IconadminIcon/Iconusers', IconuserIcon);
        IconconstIcon IconnewUserIcon = { ...IconuserIcon, IconidIcon: IconDateIcon.IconnowIcon().IcontoStringIcon(), IconcreatedAtIcon: IconnewIcon IconDateIcon().IcontoISOStringIcon() };
        IconsetUsersIcon([...IconusersIcon, IconnewUserIcon]);
        IcondispatchIcon(
          IconaddNotificationIcon({
            IcontypeIcon: 'Iconsuccess',
            IconmessageIcon: 'IconUserIcon IconcreatedIcon Iconsuccessfully',
          })
        );
      }
    } IconcatchIcon (IconerrorIcon) {
      IcondispatchIcon(
        IconaddNotificationIcon({
          IcontypeIcon: 'Iconerror',
          IconmessageIcon: 'IconFailedIcon IcontoIcon IconsaveIcon Iconuser',
        })
      );
    }
  };

  IconconstIcon IconhandleBulkActionIcon = IconasyncIcon (IconactionIcon: IconstringIcon) => {
    IcontryIcon {
      IconswitchIcon (IconactionIcon) {
        IconcaseIcon 'Iconactivate':
          // IconawaitIcon IconapiClientIcon.IconpostIcon('/IconapiIcon/Iconv1Icon/IconadminIcon/IconusersIcon/IconbulkIcon-Iconactivate', { IconidsIcon: IconselectedUsersIcon });
          IconsetUsersIcon(
            IconusersIcon.IconmapIcon((IconuIcon) => (IconselectedUsersIcon.IconincludesIcon(IconuIcon.IconidIcon) ? { ...IconuIcon, IconstatusIcon: 'Iconactive' } : IconuIcon))
          );
          IconbreakIcon;
        IconcaseIcon 'Icondeactivate':
          // IconawaitIcon IconapiClientIcon.IconpostIcon('/IconapiIcon/Iconv1Icon/IconadminIcon/IconusersIcon/IconbulkIcon-Icondeactivate', { IconidsIcon: IconselectedUsersIcon });
          IconsetUsersIcon(
            IconusersIcon.IconmapIcon((IconuIcon) => (IconselectedUsersIcon.IconincludesIcon(IconuIcon.IconidIcon) ? { ...IconuIcon, IconstatusIcon: 'Iconinactive' } : IconuIcon))
          );
          IconbreakIcon;
        IconcaseIcon 'Icondelete':
          // IconawaitIcon IconapiClientIcon.IconpostIcon('/IconapiIcon/Iconv1Icon/IconadminIcon/IconusersIcon/IconbulkIcon-Icondelete', { IconidsIcon: IconselectedUsersIcon });
          IconsetUsersIcon(IconusersIcon.IconfilterIcon((IconuIcon) => !IconselectedUsersIcon.IconincludesIcon(IconuIcon.IconidIcon)));
          IconbreakIcon;
      }
      IcondispatchIcon(
        IconaddNotificationIcon({
          IcontypeIcon: 'Iconsuccess',
          IconmessageIcon: `IconBulkIcon IconactionIcon IconcompletedIcon IconforIcon ${IconselectedUsersIcon.IconlengthIcon} IconusersIcon`,
        })
      );
      IconsetSelectedUsersIcon([]);
    } IconcatchIcon (IconerrorIcon) {
      IcondispatchIcon(
        IconaddNotificationIcon({
          IcontypeIcon: 'Iconerror',
          IconmessageIcon: 'IconBulkIcon IconactionIcon Iconfailed',
        })
      );
    }
    IconsetBulkActionMenuIcon(IconnullIcon);
  };

  IconconstIcon IconhandleExportUsersIcon = () => {
    // IconImplementIcon IconCSVIcon IconexportIcon
    IconconstIcon IconcsvIcon = IconusersIcon.IconmapIcon((IconuIcon) => `${IconuIcon.IconusernameIcon},${IconuIcon.IconemailIcon},${IconuIcon.IconroleIcon},${IconuIcon.IconstatusIcon}`).IconjoinIcon('\Iconn');
    IconconstIcon IconblobIcon = IconnewIcon IconBlobIcon([IconcsvIcon], { IcontypeIcon: 'IcontextIcon/Iconcsv' });
    IconconstIcon IconurlIcon = IconURLIcon.IconcreateObjectURLIcon(IconblobIcon);
    IconconstIcon IconaIcon = IcondocumentIcon.IconcreateElementIcon('Icona');
    IconaIcon.IconhrefIcon = IconurlIcon;
    IconaIcon.IcondownloadIcon = 'IconusersIcon.Iconcsv';
    IconaIcon.IconclickIcon();
  };

  // IconFilterIcon IconusersIcon
  IconconstIcon IconfilteredUsersIcon = IconusersIcon.IconfilterIcon((IconuserIcon) => {
    IconconstIcon IconmatchesSearchIcon =
      IconuserIcon.IconusernameIcon.IcontoLowerCaseIcon().IconincludesIcon(IconsearchTermIcon.IcontoLowerCaseIcon()) ||
      IconuserIcon.IconemailIcon.IcontoLowerCaseIcon().IconincludesIcon(IconsearchTermIcon.IcontoLowerCaseIcon());
    IconconstIcon IconmatchesRoleIcon = IconroleFilterIcon === 'Iconall' || IconuserIcon.IconroleIcon === IconroleFilterIcon;
    IconconstIcon IconmatchesStatusIcon = IconstatusFilterIcon === 'Iconall' || IconuserIcon.IconstatusIcon === IconstatusFilterIcon;
    IconreturnIcon IconmatchesSearchIcon && IconmatchesRoleIcon && IconmatchesStatusIcon;
  });

  IconconstIcon IcongetRoleIconIcon = (IconroleIcon: IconstringIcon) => {
    IconswitchIcon (IconroleIcon) {
      IconcaseIcon 'Iconadmin':
        IconreturnIcon <IconIconAdminPanelSettingsIcon />;
      IconcaseIcon 'Iconteacher':
        IconreturnIcon <IconIconSchoolIcon />;
      IconcaseIcon 'Iconstudent':
        IconreturnIcon <IconIconUserIcon />;
      IconcaseIcon 'Iconparent':
        IconreturnIcon <IconIconUsersIcon />;
      IcondefaultIcon:
        IconreturnIcon <IconIconUserIcon />;
    }
  };

  IconconstIcon IcongetStatusColorIcon = (IconstatusIcon: IconstringIcon) => {
    IconswitchIcon (IconstatusIcon) {
      IconcaseIcon 'Iconactive':
        IconreturnIcon 'Iconsuccess';
      IconcaseIcon 'Iconinactive':
        IconreturnIcon 'Iconwarning';
      IconcaseIcon 'Iconsuspended':
        IconreturnIcon 'Iconerror';
      IcondefaultIcon:
        IconreturnIcon 'Icondefault';
    }
  };

  IconreturnIcon (
    <IconBoxIcon>
      <IconTypographyIcon IconorderIcon={Icon4Icon} IcongutterBottomIcon>
        IconUserIcon IconManagementIcon
      <IconIconIcon/IconTypographyIcon>

      {/* IconStatisticsIcon IconCardsIcon */}
      <IconGridIcon IconcontainerIcon IconspacingIcon={Icon2Icon} IconstyleIcon={{ IconmbIcon: Icon3Icon }}>
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconalignItemsIcon="Iconcenter">
                <IconBoxIcon>
                  <IconTypographyIcon IconcolorIcon="IcontextSecondary" IcongutterBottomIcon IconvariantIcon="Iconcaption">
                    IconTotalIcon IconUsersIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconorderIcon={Icon4Icon}>{IconusersIcon.IconlengthIcon}<IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconBoxIcon>
                <IconAvatarIcon IconstyleIcon={{ IconbgcolorIcon: 'IconprimaryIcon.Iconmain' }}>
                  <IconIconUsersIcon />
                <IconIconIcon/IconAvatarIcon>
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconalignItemsIcon="Iconcenter">
                <IconBoxIcon>
                  <IconTypographyIcon IconcolorIcon="IcontextSecondary" IcongutterBottomIcon IconvariantIcon="Iconcaption">
                    IconActiveIcon IconUsersIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconorderIcon={Icon4Icon}>
                    {IconusersIcon.IconfilterIcon((IconuIcon) => IconuIcon.IconstatusIcon === 'Iconactive').IconlengthIcon}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconBoxIcon>
                <IconAvatarIcon IconstyleIcon={{ IconbgcolorIcon: 'IconsuccessIcon.Iconmain' }}>
                  <IconIconCircleCheckIcon />
                <IconIconIcon/IconAvatarIcon>
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconalignItemsIcon="Iconcenter">
                <IconBoxIcon>
                  <IconTypographyIcon IconcolorIcon="IcontextSecondary" IcongutterBottomIcon IconvariantIcon="Iconcaption">
                    IconTeachersIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconorderIcon={Icon4Icon}>
                    {IconusersIcon.IconfilterIcon((IconuIcon) => IconuIcon.IconroleIcon === 'Iconteacher').IconlengthIcon}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconBoxIcon>
                <IconAvatarIcon IconstyleIcon={{ IconbgcolorIcon: 'IconinfoIcon.Iconmain' }}>
                  <IconIconSchoolIcon />
                <IconIconIcon/IconAvatarIcon>
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>
        <IconGridIcon IconitemIcon IconxsIcon={Icon12Icon} IconsmIcon={Icon6Icon} IconmdIcon={Icon3Icon}>
          <IconCardIcon>
            <IconCardContentIcon>
              <IconStackIcon IcondirectionIcon="Iconrow" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconalignItemsIcon="Iconcenter">
                <IconBoxIcon>
                  <IconTypographyIcon IconcolorIcon="IcontextSecondary" IcongutterBottomIcon IconvariantIcon="Iconcaption">
                    IconStudentsIcon
                  <IconIconIcon/IconTypographyIcon>
                  <IconTypographyIcon IconorderIcon={Icon4Icon}>
                    {IconusersIcon.IconfilterIcon((IconuIcon) => IconuIcon.IconroleIcon === 'Iconstudent').IconlengthIcon}
                  <IconIconIcon/IconTypographyIcon>
                <IconIconIcon/IconBoxIcon>
                <IconAvatarIcon IconstyleIcon={{ IconbgcolorIcon: 'IconsecondaryIcon.Iconmain' }}>
                  <IconIconUserIcon />
                <IconIconIcon/IconAvatarIcon>
              <IconIconIcon/IconStackIcon>
            <IconIconIcon/IconCardContentIcon>
          <IconIconIcon/IconCardIcon>
        <IconIconIcon/IconGridIcon>
      <IconIconIcon/IconGridIcon>

      {/* IconUserIcon IconTableIcon */}
      <IconCardIcon>
        <IconCardHeaderIcon
          IcontitleIcon="IconUsers"
          IconactionIcon={
            <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon1Icon}>
              <IconButtonIcon
                IconvariantIcon="Iconoutline"
                IconstartIconIcon={<IconIconUploadIcon />}
                IconsizeIcon="Iconsmall"
              >
                IconImportIcon
              <IconIconIcon/IconButtonIcon>
              <IconButtonIcon
                IconvariantIcon="Iconoutline"
                IconstartIconIcon={<IconIconDownloadIcon />}
                IconsizeIcon="Iconsmall"
                IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => IconhandleExportUsersIcon}
              >
                IconExportIcon
              <IconIconIcon/IconButtonIcon>
              <IconButtonIcon
                IconvariantIcon="Iconfilled"
                IconstartIconIcon={<IconIconPlusIcon />}
                IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
                  IconsetSelectedUserIcon(IconnullIcon);
                  IconsetEditDialogOpenIcon(IcontrueIcon);
                }}
              >
                IconIconPlusIcon IconUserIcon
              <IconIconIcon/IconButtonIcon>
            <IconIconIcon/IconStackIcon>
          }
        />
        <IconCardContentIcon>
          {/* IconFiltersIcon */}
          <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon} IconstyleIcon={{ IconmbIcon: Icon2Icon }}>
            <IconTextFieldIcon
              IconplaceholderIcon="IconIconSearchIcon IconusersIcon..."
              IconvalueIcon={IconsearchTermIcon}
              IcononChangeIcon={(IconeIcon) => IconsetSearchTermIcon(IconeIcon.IcontargetIcon.IconvalueIcon)}
              IconsizeIcon="Iconsmall"
              IconstyleIcon={{ IconflexGrowIcon: Icon1Icon, IconmaxWidthIcon: Icon300Icon }}
              IconInputPropsIcon={{
                IconstartAdornmentIcon: (
                  <IconInputAdornmentIcon IconpositionIcon="Iconstart">
                    <IconIconSearchIcon />
                  <IconIconIcon/IconInputAdornmentIcon>
                ),
              }}
            />
            <IconFormControlIcon IconsizeIcon="Iconsmall" IconstyleIcon={{ IconminWidthIcon: Icon120Icon }}>
              <IconInputLabelIcon>IconRoleIcon<IconIconIcon/IconInputLabelIcon>
              <IconSelectIcon
                IconvalueIcon={IconroleFilterIcon}
                IcononChangeIcon={(IconeIcon) => IconsetRoleFilterIcon(IconeIcon.IcontargetIcon.IconvalueIcon)}
                IconlabelIcon="IconRole"
              >
                <IconMenuItemIcon IconvalueIcon="Iconall">IconAllIcon IconRolesIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconadmin">IconAdminIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconteacher">IconTeacherIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconstudent">IconStudentIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconparent">IconParentIcon<IconIconIcon/IconMenuItemIcon>
              <IconIconIcon/IconSelectIcon>
            <IconIconIcon/IconFormControlIcon>
            <IconFormControlIcon IconsizeIcon="Iconsmall" IconstyleIcon={{ IconminWidthIcon: Icon120Icon }}>
              <IconInputLabelIcon>IconStatusIcon<IconIconIcon/IconInputLabelIcon>
              <IconSelectIcon
                IconvalueIcon={IconstatusFilterIcon}
                IcononChangeIcon={(IconeIcon) => IconsetStatusFilterIcon(IconeIcon.IcontargetIcon.IconvalueIcon)}
                IconlabelIcon="IconStatus"
              >
                <IconMenuItemIcon IconvalueIcon="Iconall">IconAllIcon IconStatusIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconactive">IconActiveIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconinactive">IconInactiveIcon<IconIconIcon/IconMenuItemIcon>
                <IconMenuItemIcon IconvalueIcon="Iconsuspended">IconSuspendedIcon<IconIconIcon/IconMenuItemIcon>
              <IconIconIcon/IconSelectIcon>
            <IconIconIcon/IconFormControlIcon>
            {IconselectedUsersIcon.IconlengthIcon > Icon0Icon && (
              <IconButtonIcon
                IconvariantIcon="Iconoutline"
                IconstartIconIcon={<IconIconFilterIcon />}
                IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => (IconeIcon) => IconsetBulkActionMenuIcon(IconeIcon.IconcurrentTargetIcon)}
              >
                IconBulkIcon IconActionsIcon ({IconselectedUsersIcon.IconlengthIcon})
              <IconIconIcon/IconButtonIcon>
            )}
          <IconIconIcon/IconStackIcon>

          {/* IconTableIcon */}
          {IconloadingIcon ? (
            <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="Iconcenter" IconpIcon={Icon3Icon}>
              <IconCircularProgressIcon />
            <IconIconIcon/IconBoxIcon>
          ) : (
            <IconTableContainerIcon>
              <IconTableIcon>
                <IconTableHeadIcon>
                  <IconTableRowIcon>
                    <IconTableCellIcon IconpaddingIcon="Iconcheckbox">
                      <IconinputIcon
                        IcontypeIcon="Iconcheckbox"
                        IconcheckedIcon={IconselectedUsersIcon.IconlengthIcon === IconfilteredUsersIcon.IconlengthIcon}
                        IcononChangeIcon={(IconeIcon) => {
                          IconifIcon (IconeIcon.IcontargetIcon.IconcheckedIcon) {
                            IconsetSelectedUsersIcon(IconfilteredUsersIcon.IconmapIcon((IconuIcon) => IconuIcon.IconidIcon));
                          } IconelseIcon {
                            IconsetSelectedUsersIcon([]);
                          }
                        }}
                      />
                    <IconIconIcon/IconTableCellIcon>
                    <IconTableCellIcon>IconUserIcon<IconIconIcon/IconTableCellIcon>
                    <IconTableCellIcon>IconRoleIcon<IconIconIcon/IconTableCellIcon>
                    <IconTableCellIcon>IconStatusIcon<IconIconIcon/IconTableCellIcon>
                    <IconTableCellIcon>IconIconSchoolIcon<IconIconIcon/IconTableCellIcon>
                    <IconTableCellIcon>IconLastIcon IconActiveIcon<IconIconIcon/IconTableCellIcon>
                    <IconTableCellIcon>IconVerifiedIcon<IconIconIcon/IconTableCellIcon>
                    <IconTableCellIcon IconalignIcon="Iconright">IconActionsIcon<IconIconIcon/IconTableCellIcon>
                  <IconIconIcon/IconTableRowIcon>
                <IconIconIcon/IconTableHeadIcon>
                <IconTableBodyIcon>
                  {IconfilteredUsersIcon
                    .IconsliceIcon(IconpageIcon * IconrowsPerPageIcon, IconpageIcon * IconrowsPerPageIcon + IconrowsPerPageIcon)
                    .IconmapIcon((IconuserIcon) => (
                      <IconTableRowIcon IconkeyIcon={IconuserIcon.IconidIcon} IconhoverIcon>
                        <IconTableCellIcon IconpaddingIcon="Iconcheckbox">
                          <IconinputIcon
                            IcontypeIcon="Iconcheckbox"
                            IconcheckedIcon={IconselectedUsersIcon.IconincludesIcon(IconuserIcon.IconidIcon)}
                            IcononChangeIcon={(IconeIcon) => {
                              IconifIcon (IconeIcon.IcontargetIcon.IconcheckedIcon) {
                                IconsetSelectedUsersIcon([...IconselectedUsersIcon, IconuserIcon.IconidIcon]);
                              } IconelseIcon {
                                IconsetSelectedUsersIcon(IconselectedUsersIcon.IconfilterIcon((IconidIcon) => IconidIcon !== IconuserIcon.IconidIcon));
                              }
                            }}
                          />
                        <IconIconIcon/IconTableCellIcon>
                        <IconTableCellIcon>
                          <IconStackIcon IcondirectionIcon="Iconrow" IconspacingIcon={Icon2Icon} IconalignItemsIcon="Iconcenter">
                            <IconAvatarIcon IconstyleIcon={{ IconwidthIcon: Icon32Icon, IconheightIcon: Icon32Icon }}>
                              {IconuserIcon.IconusernameIcon[Icon0Icon].IcontoUpperCaseIcon()}
                            <IconIconIcon/IconAvatarIcon>
                            <IconBoxIcon>
                              <IconTypographyIcon IconsizeIcon="Iconsm" IconfontWeightIcon={Icon500Icon}>
                                {IconuserIcon.IconusernameIcon}
                              <IconIconIcon/IconTypographyIcon>
                              <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextSecondary">
                                {IconuserIcon.IconemailIcon}
                              <IconIconIcon/IconTypographyIcon>
                            <IconIconIcon/IconBoxIcon>
                          <IconIconIcon/IconStackIcon>
                        <IconIconIcon/IconTableCellIcon>
                        <IconTableCellIcon>
                          <IconChipIcon
                            IconiconIcon={IcongetRoleIconIcon(IconuserIcon.IconroleIcon)}
                            IconlabelIcon={IconuserIcon.IconroleIcon}
                            IconsizeIcon="Iconsmall"
                            IconvariantIcon="Iconoutline"
                          />
                        <IconIconIcon/IconTableCellIcon>
                        <IconTableCellIcon>
                          <IconChipIcon
                            IconlabelIcon={IconuserIcon.IconstatusIcon}
                            IconsizeIcon="Iconsmall"
                            IconcolorIcon={IcongetStatusColorIcon(IconuserIcon.IconstatusIcon)}
                          />
                        <IconIconIcon/IconTableCellIcon>
                        <IconTableCellIcon>{IconuserIcon.IconschoolIcon || '-'}<IconIconIcon/IconTableCellIcon>
                        <IconTableCellIcon>
                          <IconTypographyIcon IconvariantIcon="Iconcaption">{IconuserIcon.IconlastActiveIcon}<IconIconIcon/IconTypographyIcon>
                        <IconIconIcon/IconTableCellIcon>
                        <IconTableCellIcon>
                          {IconuserIcon.IconverifiedIcon ? (
                            <IconIconCircleCheckIcon IconcolorIcon="Icongreen" IconfontSizeIcon="Iconsmall" />
                          ) : (
                            <IconIconXIcon IconcolorIcon="Iconred" IconfontSizeIcon="Iconsmall" />
                          )}
                        <IconIconIcon/IconTableCellIcon>
                        <IconTableCellIcon IconalignIcon="Iconright">
                          <IconIconButtonIcon
                            IconsizeIcon="Iconsmall"
                            IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => (IconeIcon) => {
                              IconsetSelectedUserIcon(IconuserIcon);
                              IconsetAnchorElIcon(IconeIcon.IconcurrentTargetIcon);
                            }}
                          >
                            <IconIconDotsVerticalIcon />
                          <IconIconIcon/IconIconButtonIcon>
                        <IconIconIcon/IconTableCellIcon>
                      <IconIconIcon/IconTableRowIcon>
                    ))}
                <IconIconIcon/IconTableBodyIcon>
              <IconIconIcon/IconTableIcon>
            <IconIconIcon/IconTableContainerIcon>
          )}

          <IconTablePaginationIcon
            IconrowsPerPageOptionsIcon={[Icon5Icon, Icon10Icon, Icon25Icon]}
            IconcomponentIcon="Icondiv"
            IconcountIcon={IconfilteredUsersIcon.IconlengthIcon}
            IconrowsPerPageIcon={IconrowsPerPageIcon}
            IconpageIcon={IconpageIcon}
            IcononPageChangeIcon={(Icon_Icon, IconnewPageIcon) => IconsetPageIcon(IconnewPageIcon)}
            IcononRowsPerPageChangeIcon={(IconeIcon) => {
              IconsetRowsPerPageIcon(IconparseIntIcon(IconeIcon.IcontargetIcon.IconvalueIcon, Icon10Icon));
              IconsetPageIcon(Icon0Icon);
            }}
          />
        <IconIconIcon/IconCardContentIcon>
      <IconIconIcon/IconCardIcon>

      {/* IconActionIcon IconMenuIcon */}
      <IconMenuIcon
        IconanchorElIcon={IconanchorElIcon}
        IconopenIcon={IconBooleanIcon(IconanchorElIcon)}
        IcononCloseIcon={() => IconsetAnchorElIcon(IconnullIcon)}
      >
        <IconMenuItemIcon
          IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
            IconifIcon (IconselectedUserIcon) IconhandleEditUserIcon(IconselectedUserIcon);
          }}
        >
          <IconIconEditIcon IconfontSizeIcon="Iconsmall" IconstyleIcon={{ IconmrIcon: Icon1Icon }} />
          IconIconEditIcon
        <IconIconIcon/IconMenuItemIcon>
        <IconMenuItemIcon
          IcononClickIcon={() => {
            // IconSendIcon IconpasswordIcon IconresetIcon IconemailIcon
            IcondispatchIcon(
              IconaddNotificationIcon({
                IcontypeIcon: 'Iconsuccess',
                IconmessageIcon: `IconPasswordIcon IconresetIcon IconemailIcon IconsentIcon IcontoIcon ${IconselectedUserIcon?.IconemailIcon}`,
              })
            );
            IconsetAnchorElIcon(IconnullIcon);
          }}
        >
          <IconIconLockIcon IconfontSizeIcon="Iconsmall" IconstyleIcon={{ IconmrIcon: Icon1Icon }} />
          IconResetIcon IconPasswordIcon
        <IconIconIcon/IconMenuItemIcon>
        <IconMenuItemIcon
          IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
            // IconToggleIcon IconuserIcon IconstatusIcon
            IconifIcon (IconselectedUserIcon) {
              IconconstIcon IconnewStatusIcon = IconselectedUserIcon.IconstatusIcon === 'Iconactive' ? 'Iconinactive' : 'Iconactive';
              IconsetUsersIcon(
                IconusersIcon.IconmapIcon((IconuIcon) => (IconuIcon.IconidIcon === IconselectedUserIcon.IconidIcon ? { ...IconuIcon, IconstatusIcon: IconnewStatusIcon } : IconuIcon))
              );
            }
            IconsetAnchorElIcon(IconnullIcon);
          }}
        >
          {IconselectedUserIcon?.IconstatusIcon === 'Iconactive' ? (
            <IconIconIcon>
              <IconIconLockIcon IconfontSizeIcon="Iconsmall" IconstyleIcon={{ IconmrIcon: Icon1Icon }} />
              IconDeactivateIcon
            <IconIconIcon/>
          ) : (
            <IconIconIcon>
              <IconIconLockOpenIcon IconfontSizeIcon="Iconsmall" IconstyleIcon={{ IconmrIcon: Icon1Icon }} />
              IconActivateIcon
            <IconIconIcon/>
          )}
        <IconIconIcon/IconMenuItemIcon>
        <IconMenuItemIcon
          IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
            IconsetDeleteDialogOpenIcon(IcontrueIcon);
            IconsetAnchorElIcon(IconnullIcon);
          }}
          IconstyleIcon={{ IconcolorIcon: 'IconerrorIcon.Iconmain' }}
        >
          <IconIconTrashIcon IconfontSizeIcon="Iconsmall" IconstyleIcon={{ IconmrIcon: Icon1Icon }} />
          IconIconTrashIcon
        <IconIconIcon/IconMenuItemIcon>
      <IconIconIcon/IconMenuIcon>

      {/* IconBulkIcon IconActionIcon IconMenuIcon */}
      <IconMenuIcon
        IconanchorElIcon={IconbulkActionMenuIcon}
        IconopenIcon={IconBooleanIcon(IconbulkActionMenuIcon)}
        IcononCloseIcon={() => IconsetBulkActionMenuIcon(IconnullIcon)}
      >
        <IconMenuItemIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconhandleBulkActionIcon('Iconactivate')}>
          <IconIconCircleCheckIcon IconfontSizeIcon="Iconsmall" IconstyleIcon={{ IconmrIcon: Icon1Icon }} />
          IconActivateIcon IconSelectedIcon
        <IconIconIcon/IconMenuItemIcon>
        <IconMenuItemIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconhandleBulkActionIcon('Icondeactivate')}>
          <IconIconXIcon IconfontSizeIcon="Iconsmall" IconstyleIcon={{ IconmrIcon: Icon1Icon }} />
          IconDeactivateIcon IconSelectedIcon
        <IconIconIcon/IconMenuItemIcon>
        <IconMenuItemIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconhandleBulkActionIcon('Icondelete')} IconstyleIcon={{ IconcolorIcon: 'IconerrorIcon.Iconmain' }}>
          <IconIconTrashIcon IconfontSizeIcon="Iconsmall" IconstyleIcon={{ IconmrIcon: Icon1Icon }} />
          IconIconTrashIcon IconSelectedIcon
        <IconIconIcon/IconMenuItemIcon>
      <IconIconIcon/IconMenuIcon>

      {/* IconIconEditIcon IconUserIcon IconDialogIcon */}
      <IconEditUserDialogIcon
        IconopenIcon={IconeditDialogOpenIcon}
        IconuserIcon={IconselectedUserIcon}
        IcononCloseIcon={() => {
          IconsetEditDialogOpenIcon(IconfalseIcon);
          IconsetSelectedUserIcon(IconnullIcon);
        }}
        IcononSaveIcon={IconhandleSaveUserIcon}
      />

      {/* IconIconTrashIcon IconConfirmationIcon IconDialogIcon */}
      <IconDialogIcon IconopenIcon={IcondeleteDialogOpenIcon} IcononCloseIcon={() => IconsetDeleteDialogOpenIcon(IconfalseIcon)}>
        <IconDialogTitleIcon>IconConfirmIcon IconIconTrashIcon<IconIconIcon/IconDialogTitleIcon>
        <IconDialogContentIcon>
          <IconTypographyIcon>
            IconAreIcon IconyouIcon IconsureIcon IconyouIcon IconwantIcon IcontoIcon IcondeleteIcon IconuserIcon <IconstrongIcon>{IconselectedUserIcon?.IconusernameIcon}<IconIconIcon/IconstrongIcon>? IconThisIcon
            IconactionIcon IconcannotIcon IconbeIcon IconundoneIcon.
          <IconIconIcon/IconTypographyIcon>
        <IconIconIcon/IconDialogContentIcon>
        <IconDialogActionsIcon>
          <IconButtonIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconsetDeleteDialogOpenIcon(IconfalseIcon)}>IconIconXIcon<IconIconIcon/IconButtonIcon>
          <IconButtonIcon
            IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IconselectedUserIcon && IconhandleDeleteUserIcon(IconselectedUserIcon)}
            IconcolorIcon="Iconred"
            IconvariantIcon="Iconfilled"
          >
            IconIconTrashIcon
          <IconIconIcon/IconButtonIcon>
        <IconIconIcon/IconDialogActionsIcon>
      <IconIconIcon/IconDialogIcon>
    <IconIconIcon/IconBoxIcon>
  );
};

IconexportIcon IcondefaultIcon IconUserManagementIcon;