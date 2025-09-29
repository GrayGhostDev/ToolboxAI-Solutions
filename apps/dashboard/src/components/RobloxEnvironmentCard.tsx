IconimportIcon { IconBoxIcon, IconButtonIcon, IconTypographyIcon, IconPaperIcon, IconStackIcon, IconGridIcon, IconContainerIcon, IconIconButtonIcon, IconAvatarIcon, IconCardIcon, IconCardContentIcon, IconCardActionsIcon, IconListIcon, IconListItemIcon, IconListItemTextIcon, IconDividerIcon, IconTextFieldIcon, IconSelectIcon, IconMenuItemIcon, IconChipIcon, IconBadgeIcon, IconAlertIcon, IconCircularProgressIcon, IconLinearProgressIcon, IconDialogIcon, IconDialogTitleIcon, IconDialogContentIcon, IconDialogActionsIcon, IconDrawerIcon, IconAppBarIcon, IconToolbarIcon, IconTabsIcon, IconTabIcon, IconMenuIcon, IconTooltipIcon, IconCheckboxIcon, IconRadioIcon, IconRadioGroupIcon, IconFormControlIcon, IconFormControlLabelIcon, IconInputLabelIcon, IconSwitchIcon, IconSliderIcon, IconRatingIcon, IconAutocompleteIcon, IconSkeletonIcon, IconTableIcon } IconfromIcon '../IconutilsIcon/IconmuiIcon-Iconimports';
IconimportIcon IconReactIcon IconfromIcon 'Iconreact';

IconimportIcon {
  IconPlayArrowIcon IconasIcon IconIconPlayerPlayIcon,
  IconDownloadIcon IconasIcon IconIconDownloadIcon,
  IconDeleteIcon IconasIcon IconIconTrashIcon,
  IconMoreVertIcon IconasIcon IconIconDotsVerticalIcon,
  IconCloudUploadIcon IconasIcon IconIconCloudUploadIcon,
} IconfromIcon '@IconmuiIcon/IconiconsIcon-Iconmaterial';
IconimportIcon { IconRobloxEnvironmentIcon } IconfromIcon '../IconservicesIcon/IconrobloxSync';
IconimportIcon { IconGenerationStatusIcon } IconfromIcon '../IconstoreIcon/IconslicesIcon/IconrobloxSlice';
IconimportIcon { IconIconIcon, IconIconCloudUploadIcon, IconIconDotsVerticalIcon, IconIconDownloadIcon, IconIconPlayerPlayIcon, IconIconTrashIcon } IconfromIcon '@IcontablerIcon/IconiconsIcon-Iconreact';

IconinterfaceIcon IconRobloxEnvironmentCardPropsIcon {
  IconenvironmentIcon: IconRobloxEnvironmentIcon;
  IcongenerationStatusIcon?: IconGenerationStatusIcon;
  IcononGenerateIcon: (IconidIcon: IconstringIcon) => IconvoidIcon;
  IcononDeployIcon: (IconidIcon: IconstringIcon) => IconvoidIcon;
  IcononDownloadIcon: (IconidIcon: IconstringIcon) => IconvoidIcon;
  IcononDeleteIcon: (IconidIcon: IconstringIcon) => IconvoidIcon;
  IcononPreviewIcon: (IconidIcon: IconstringIcon) => IconvoidIcon;
}

IconexportIcon IconconstIcon IconRobloxEnvironmentCardIcon: IconReactIcon.IconFunctionComponentIcon<IconRobloxEnvironmentCardPropsIcon> = ({
  IconenvironmentIcon,
  IcongenerationStatusIcon,
  IcononGenerateIcon,
  IcononDeployIcon,
  IcononDownloadIcon,
  IcononDeleteIcon,
  IcononPreviewIcon,
}) => {
  IconconstIcon [IconmenuAnchorIcon, IconsetMenuAnchorIcon] = IconReactIcon.IconuseStateIcon<IconnullIcon | IconHTMLElementIcon>(IconnullIcon);

  IconconstIcon IcongetStatusColorIcon = (IconstatusIcon: IconstringIcon) => {
    IconswitchIcon (IconstatusIcon) {
      IconcaseIcon 'Iconready': IconreturnIcon 'Iconsuccess';
      IconcaseIcon 'Icongenerating': IconreturnIcon 'Iconwarning';
      IconcaseIcon 'Icondeployed': IconreturnIcon 'Iconinfo';
      IconcaseIcon 'Iconerror': IconreturnIcon 'Iconerror';
      IcondefaultIcon: IconreturnIcon 'Icondefault';
    }
  };

  IconconstIcon IcongetStatusTextIcon = (IconstatusIcon: IconstringIcon) => {
    IconswitchIcon (IconstatusIcon) {
      IconcaseIcon 'Icondraft': IconreturnIcon 'IconDraft';
      IconcaseIcon 'Icongenerating': IconreturnIcon 'IconGenerating';
      IconcaseIcon 'Iconready': IconreturnIcon 'IconReady';
      IconcaseIcon 'Icondeployed': IconreturnIcon 'IconDeployed';
      IconcaseIcon 'Iconerror': IconreturnIcon 'IconError';
      IcondefaultIcon: IconreturnIcon 'IconUnknown';
    }
  };

  IconconstIcon IconisGeneratingIcon = IcongenerationStatusIcon?.IconstatusIcon === 'Icongenerating';
  IconconstIcon IconcanGenerateIcon = IconenvironmentIcon.IconstatusIcon === 'Icondraft';
  IconconstIcon IconcanDeployIcon = IconenvironmentIcon.IconstatusIcon === 'Iconready' && IconenvironmentIcon.IcondownloadUrlIcon;
  IconconstIcon IconcanDownloadIcon = IconenvironmentIcon.IconstatusIcon === 'Iconready' && IconenvironmentIcon.IcondownloadUrlIcon;

  IconreturnIcon (
    <IconCardIcon IconstyleIcon={{ IconheightIcon: 'Icon100Icon%', IcondisplayIcon: 'Iconflex', IconflexDirectionIcon: 'Iconcolumn' }}>
      <IconCardContentIcon IconstyleIcon={{ IconflexGrowIcon: Icon1Icon }}>
        <IconBoxIcon IcondisplayIcon="Iconflex" IconjustifyContentIcon="IconspaceIcon-Iconbetween" IconalignItemsIcon="IconflexIcon-Iconstart" IconmbIcon={Icon1Icon}>
          <IconTypographyIcon IconorderIcon={Icon6Icon} IconcomponentIcon="Iconh3" IconnoWrapIcon>
            {IconenvironmentIcon.IconnameIcon}
          <IconIconIcon/IconTypographyIcon>
          <IconIconButtonIcon
            IconsizeIcon="Iconsmall"
            IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => (IconeIcon) => IconsetMenuAnchorIcon(IconeIcon.IconcurrentTargetIcon)}
          >
            <IconIconDotsVerticalIcon />
          <IconIconIcon/IconIconButtonIcon>
        <IconIconIcon/IconBoxIcon>

        <IconTypographyIcon IconcolorIcon="IcontextIcon.Iconsecondary" IcongutterBottomIcon>
          {IconenvironmentIcon.IconthemeIcon} • {IconenvironmentIcon.IconmapTypeIcon.IconreplaceIcon('Icon_', ' ')}
        <IconIconIcon/IconTypographyIcon>

        <IconBoxIcon IconmbIcon={Icon2Icon}>
          <IconChipIcon
            IconlabelIcon={IcongetStatusTextIcon(IconenvironmentIcon.IconstatusIcon)}
            IconcolorIcon={IcongetStatusColorIcon(IconenvironmentIcon.IconstatusIcon)}
            IconsizeIcon="Iconsmall"
          />
        <IconIconIcon/IconBoxIcon>

        {IconenvironmentIcon.IconspecIcon.Iconlearning_objectivesIcon && (
          <IconBoxIcon IconmbIcon={Icon2Icon}>
            <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary">
              IconLearningIcon IconObjectivesIcon:
            <IconIconIcon/IconTypographyIcon>
            <IconTypographyIcon IconsizeIcon="Iconsm">
              {IconenvironmentIcon.IconspecIcon.Iconlearning_objectivesIcon.IconjoinIcon(', ')}
            <IconIconIcon/IconTypographyIcon>
          <IconIconIcon/IconBoxIcon>
        )}

        {IconisGeneratingIcon && IcongenerationStatusIcon && (
          <IconBoxIcon IconmbIcon={Icon2Icon}>
            <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="IcontextIcon.Iconsecondary" IcongutterBottomIcon>
              {IcongenerationStatusIcon.IconmessageIcon}
            <IconIconIcon/IconTypographyIcon>
            <IconLinearProgressIcon 
              IconvariantIcon="Icondeterminate" 
              IconvalueIcon={IcongenerationStatusIcon.IconprogressIcon || Icon0Icon} 
            />
            <IconTypographyIcon IconvariantIcon="Iconcaption" IconcolorIcon="IcontextIcon.Iconsecondary">
              {IcongenerationStatusIcon.IconprogressIcon}% • {IcongenerationStatusIcon.IconstageIcon}
            <IconIconIcon/IconTypographyIcon>
          <IconIconIcon/IconBoxIcon>
        )}

        {IconenvironmentIcon.IconstatusIcon === 'Iconerror' && IcongenerationStatusIcon?.IconerrorIcon && (
          <IconTypographyIcon IconsizeIcon="Iconsm" IconcolorIcon="Iconred">
            IconErrorIcon: {IcongenerationStatusIcon.IconerrorIcon}
          <IconIconIcon/IconTypographyIcon>
        )}
      <IconIconIcon/IconCardContentIcon>

      <IconCardActionsIcon>
        {IconcanGenerateIcon && (
          <IconButtonIcon
            IconstartIconIcon={<IconIconPlayerPlayIcon />}
            IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IcononGenerateIcon(IconenvironmentIcon.IconidIcon)}
            IconvariantIcon="Iconfilled"
            IconcolorIcon="Iconblue"
          >
            IconGenerateIcon
          <IconIconIcon/IconButtonIcon>
        )}

        {IconcanDownloadIcon && (
          <IconButtonIcon
            IconstartIconIcon={<IconIconDownloadIcon />}
            IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IcononDownloadIcon(IconenvironmentIcon.IconidIcon)}
            IconsizeIcon="Iconsmall"
          >
            IconDownloadIcon
          <IconIconIcon/IconButtonIcon>
        )}

        {IconcanDeployIcon && (
          <IconButtonIcon
            IconstartIconIcon={<IconIconCloudUploadIcon />}
            IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IcononDeployIcon(IconenvironmentIcon.IconidIcon)}
            IconsizeIcon="Iconsmall"
            IconvariantIcon="Iconoutline"
          >
            IconDeployIcon
          <IconIconIcon/IconButtonIcon>
        )}

        {IconenvironmentIcon.IconpreviewUrlIcon && (
          <IconButtonIcon
            IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => IcononPreviewIcon(IconenvironmentIcon.IconidIcon)}
            IconsizeIcon="Iconsmall"
          >
            IconPreviewIcon
          <IconIconIcon/IconButtonIcon>
        )}
      <IconIconIcon/IconCardActionsIcon>

      <IconMenuIcon
        IconanchorElIcon={IconmenuAnchorIcon}
        IconopenIcon={IconBooleanIcon(IconmenuAnchorIcon)}
        IcononCloseIcon={() => IconsetMenuAnchorIcon(IconnullIcon)}
      >
        <IconMenuItemIcon IcononClickIcon={(IconeIcon: IconReactIcon.IconMouseEventIcon) => () => {
          IcononDeleteIcon(IconenvironmentIcon.IconidIcon);
          IconsetMenuAnchorIcon(IconnullIcon);
        }}>
          <IconIconTrashIcon IconstyleIcon={{ IconmrIcon: Icon1Icon }} />
          IconDeleteIcon
        <IconIconIcon/IconMenuItemIcon>
      <IconIconIcon/IconMenuIcon>
    <IconIconIcon/IconCardIcon>
  );
};

IconexportIcon IcondefaultIcon IconRobloxEnvironmentCardIcon;
