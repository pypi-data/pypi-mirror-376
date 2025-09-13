# Evolis SDK for Python
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF
# ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
# PARTICULAR PURPOSE.

from enum import Enum

class SettingKey(Enum):

    @staticmethod
    def from_int(v: int):
        try:
            return SettingKey(v)
        except ValueError:
            return SettingKey.Unknown

    Unknown = 0

    BBlackManagement = 1
    """
    BBlackManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NOBLACKPOINT, ALLBLACKPOINT, TEXTINBLACK, BMPBLACK
    """

    BColorBrightness = 2
    """
    BColorBrightness
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    BColorContrast = 3
    """
    BColorContrast
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    BDualDeposite = 4
    """
    BDualDeposite
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    BHalftoning = 5
    """
    BHalftoning
    Usable in PrintSessions: true
    Type: LIST
    Possible values: THRESHOLD, FLOYD, DITHERING, CLUSTERED_DITHERING
    """

    BMonochromeContrast = 6
    """
    BMonochromeContrast
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    BOverlayContrast = 7
    """
    BOverlayContrast
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    BOverlayManagement = 8
    """
    BOverlayManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NOVARNISH, FULLVARNISH, BMPVARNISH
    """

    BOverlaySecondManagement = 9
    """
    BOverlaySecondManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NOVARNISH, FULLVARNISH, BMPVARNISH
    """

    BPageRotate180 = 10
    """
    BPageRotate180
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    BRwErasingSpeed = 11
    """
    BRwErasingSpeed
    Usable in PrintSessions: true
    Type: INT
    Range: 1-10
    """

    BRwErasingTemperature = 12
    """
    BRwErasingTemperature
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    BRwManagement = 13
    """
    BRwManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: WRITEONLY, FULLREWRITE, BMPREWRITE
    """

    BRwPrintingSpeed = 14
    """
    BRwPrintingSpeed
    Usable in PrintSessions: true
    Type: INT
    Range: 1-10
    """

    BRwPrintingTemperature = 15
    """
    BRwPrintingTemperature
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    BUvBrightness = 16
    """
    BUvBrightness
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    BUvContrast = 17
    """
    BUvContrast
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    BUvManagement = 18
    """
    BUvManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NOUV, BMPUV
    """

    Duplex = 19
    """
    Duplex
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NONE, HORIZONTAL
    """

    FBlackManagement = 20
    """
    FBlackManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NOBLACKPOINT, ALLBLACKPOINT, TEXTINBLACK, BMPBLACK
    """

    FColorBrightness = 21
    """
    FColorBrightness
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    FColorContrast = 22
    """
    FColorContrast
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    FDualDeposite = 23
    """
    FDualDeposite
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    FHalftoning = 24
    """
    FHalftoning
    Usable in PrintSessions: true
    Type: LIST
    Possible values: THRESHOLD, FLOYD, DITHERING, CLUSTERED_DITHERING
    """

    FMonochromeContrast = 25
    """
    FMonochromeContrast
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    FOverlayContrast = 26
    """
    FOverlayContrast
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    FOverlayManagement = 27
    """
    FOverlayManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NOVARNISH, FULLVARNISH, BMPVARNISH
    """

    FOverlaySecondManagement = 28
    """
    FOverlaySecondManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NOVARNISH, FULLVARNISH, BMPVARNISH
    """

    FPageRotate180 = 29
    """
    FPageRotate180
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    FRwErasingSpeed = 30
    """
    FRwErasingSpeed
    Usable in PrintSessions: true
    Type: INT
    Range: 1-10
    """

    FRwErasingTemperature = 31
    """
    FRwErasingTemperature
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    FRwManagement = 32
    """
    FRwManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: WRITEONLY, FULLREWRITE, BMPREWRITE
    """

    FRwPrintingSpeed = 33
    """
    FRwPrintingSpeed
    Usable in PrintSessions: true
    Type: INT
    Range: 1-10
    """

    FRwPrintingTemperature = 34
    """
    FRwPrintingTemperature
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    FUvBrightness = 35
    """
    FUvBrightness
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    FUvContrast = 36
    """
    FUvContrast
    Usable in PrintSessions: true
    Type: INT
    Range: 1-20
    """

    FUvManagement = 37
    """
    FUvManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NOUV, BMPUV
    """

    GCardPreloading = 38
    """
    GCardPreloading
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    GDigitalScrambling = 39
    """
    GDigitalScrambling
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    GDuplexType = 40
    """
    GDuplexType
    Usable in PrintSessions: true
    Type: LIST
    Possible values: DUPLEX_CC, DUPLEX_CM, DUPLEX_MC, DUPLEX_MM
    """

    GFeederCfg = 41
    """
    GFeederCfg
    Usable in PrintSessions: true
    Type: LIST
    Possible values: PRINTER, AUTO, FEEDERA, FEEDERB, FEEDERC, FEEDERD, ALTERNATE, FEEDER1, FEEDER2, FEEDER3, FEEDER4, NONE
    """

    GFeederPos = 42
    """
    GFeederPos
    Usable in PrintSessions: true
    Type: LIST
    Possible values: PRINTER, FEEDERA, FEEDERB, FEEDERC, FEEDERD, MIDDLE, OFF
    """

    GHighQualityMode = 43
    """
    GHighQualityMode
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    GInputTray = 44
    """
    GInputTray
    Usable in PrintSessions: true
    Type: LIST
    Possible values: PRINTER, FEEDER, AUTO, MANUAL, HOPPER, BEZEL
    """

    GMagCoercivity = 45
    """
    GMagCoercivity
    Usable in PrintSessions: true
    Type: LIST
    Possible values: OFF, LOCO, HICO
    """

    GMagT1Encoding = 46
    """
    GMagT1Encoding
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ISO1, ISO2, ISO3, SIPASS, C2, JIS2, C4, NONE
    """

    GMagT2Encoding = 47
    """
    GMagT2Encoding
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ISO1, ISO2, ISO3, SIPASS, C2, JIS2, C4, NONE
    """

    GMagT3Encoding = 48
    """
    GMagT3Encoding
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ISO1, ISO2, ISO3, SIPASS, C2, JIS2, C4, NONE
    """

    GOutputTray = 49
    """
    GOutputTray
    Usable in PrintSessions: true
    Type: LIST
    Possible values: PRINTER, HOPPER, REAR, MANUAL, REJECT, BEZEL
    """

    GPipeDetection = 50
    """
    GPipeDetection
    Usable in PrintSessions: true
    Type: LIST
    Possible values: OFF, DEFAULT, CUSTOM
    """

    GRejectBox = 51
    """
    GRejectBox
    Usable in PrintSessions: true
    Type: LIST
    Possible values: PRINTER, DEFAULTREJECT, HOPPER, MANUAL, REJECT, BEZEL
    """

    GRibbonType = 52
    """
    GRibbonType
    Usable in PrintSessions: true
    Type: LIST
    Possible values: RC_YMCKI, RC_YMCKKI, RC_YMCFK, RC_YMCK, RC_YMCKK, RC_YMCKO, RC_YMCKOS, RC_YMCKOS13, RC_YMCKOK, RC_YMCKOKS13, RC_YMCKOKOS, RC_YMCKOO, RM_KO, RM_KBLACK, RM_KWHITE, RM_KRED, RM_KGREEN, RM_KBLUE, RM_KSCRATCH, RM_KMETALSILVER, RM_KMETALGOLD, RM_KSIGNATURE, RM_KWAX, RM_KPREMIUM, RM_HOLO, RM_SOKO, RC_YMCK_A, RC_YMCKK_A, RC_YMCKI_A, RC_YMCKH_A, RC_YMCFK_A, RC_YMCKSI_A, RM_KBLACK_R
    """

    GRwCard = 53
    """
    GRwCard
    Usable in PrintSessions: true
    Type: LIST
    Possible values: MBLACK, MBLUE, CUSTOM_FRONT, CUSTOM_DUPLEX
    """

    GPrintingMode = 54
    """
    GPrintingMode
    Usable in PrintSessions: true
    Type: LIST
    Possible values: D2T2, RW_2IN1
    """

    GShortPanelManagement = 55
    """
    GShortPanelManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: AUTO, CUSTOM, OFF
    """

    GSmoothing = 56
    """
    GSmoothing
    Usable in PrintSessions: true
    Type: LIST
    Possible values: STDSMOOTH, ADVSMOOTH, NOSMOOTH
    """

    GUvPremium = 57
    """
    GUvPremium
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    IBBlackCustom = 58
    """
    IBBlackCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    IBBlackLevelValue = 59
    """
    IBBlackLevelValue
    Usable in PrintSessions: true
    Type: INT
    Range: 1-255
    """

    IBDarkLevelValue = 60
    """
    IBDarkLevelValue
    Usable in PrintSessions: true
    Type: INT
    Range: 0-255
    """

    IBNoTransferAreas = 61
    """
    IBNoTransferAreas
    Usable in PrintSessions: true
    Type: TEXT
    """

    IBOverlayCustom = 62
    """
    IBOverlayCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    IBOverlayDefaultContent = 63
    """
    IBOverlayDefaultContent
    Usable in PrintSessions: false
    Type: BLOB
    """

    IBOverlaySecondCustom = 64
    """
    IBOverlaySecondCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    IBOverlaySecondDefaultContent = 65
    """
    IBOverlaySecondDefaultContent
    Usable in PrintSessions: false
    Type: BLOB
    """

    IBRegionPrintingMode = 66
    """
    IBRegionPrintingMode
    Usable in PrintSessions: true
    Type: LIST
    Possible values: RESIN, BLACK_COMPOSITE
    """

    IBRwCustom = 67
    """
    IBRwCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    IBRwCustomBitmap = 68
    """
    IBRwCustomBitmap
    Usable in PrintSessions: false
    Type: BLOB
    """

    IBTextRegion = 69
    """
    IBTextRegion
    Usable in PrintSessions: true
    Type: TEXT
    """

    IBThresholdValue = 70
    """
    IBThresholdValue
    Usable in PrintSessions: true
    Type: INT
    Range: 1-255
    """

    IBUvContent = 71
    """
    IBUvContent
    Usable in PrintSessions: false
    Type: BLOB
    """

    IBUvCustom = 72
    """
    IBUvCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    IFBlackCustom = 73
    """
    IFBlackCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    IFBlackLevelValue = 74
    """
    IFBlackLevelValue
    Usable in PrintSessions: true
    Type: INT
    Range: 1-255
    """

    IFDarkLevelValue = 75
    """
    IFDarkLevelValue
    Usable in PrintSessions: true
    Type: INT
    Range: 0-255
    """

    IFNoTransferAreas = 76
    """
    IFNoTransferAreas
    Usable in PrintSessions: true
    Type: TEXT
    """

    IFOverlayCustom = 77
    """
    IFOverlayCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    IFOverlayDefaultContent = 78
    """
    IFOverlayDefaultContent
    Usable in PrintSessions: false
    Type: BLOB
    """

    IFOverlaySecondCustom = 79
    """
    IFOverlaySecondCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    IFOverlaySecondDefaultContent = 80
    """
    IFOverlaySecondDefaultContent
    Usable in PrintSessions: false
    Type: BLOB
    """

    IFRegionPrintingMode = 81
    """
    IFRegionPrintingMode
    Usable in PrintSessions: true
    Type: LIST
    Possible values: RESIN, BLACK_COMPOSITE
    """

    IFRwCustom = 82
    """
    IFRwCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    IFRwCustomBitmap = 83
    """
    IFRwCustomBitmap
    Usable in PrintSessions: false
    Type: BLOB
    """

    IFTextRegion = 84
    """
    IFTextRegion
    Usable in PrintSessions: true
    Type: TEXT
    """

    IFUvContent = 85
    """
    IFUvContent
    Usable in PrintSessions: false
    Type: BLOB
    """

    IFUvCustom = 86
    """
    IFUvCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    IFThresholdValue = 87
    """
    IFThresholdValue
    Usable in PrintSessions: true
    Type: INT
    Range: 1-255
    """

    IGBlackSub = 88
    """
    IGBlackSub
    Usable in PrintSessions: true
    Type: TEXT
    """

    IGDuplexPreset = 89
    """
    IGDuplexPreset
    Usable in PrintSessions: false
    Type: INT
    Range: 0-99
    """

    IGIQLABC = 90
    """
    IGIQLABC
    Usable in PrintSessions: true
    Type: INT
    Range: 0-20
    """

    IGIQLABM = 91
    """
    IGIQLABM
    Usable in PrintSessions: true
    Type: INT
    Range: 0-20
    """

    IGIQLABY = 92
    """
    IGIQLABY
    Usable in PrintSessions: true
    Type: INT
    Range: 0-20
    """

    IGIQLACC = 93
    """
    IGIQLACC
    Usable in PrintSessions: true
    Type: INT
    Range: 0-20
    """

    IGIQLACM = 94
    """
    IGIQLACM
    Usable in PrintSessions: true
    Type: INT
    Range: 0-20
    """

    IGIQLACY = 95
    """
    IGIQLACY
    Usable in PrintSessions: true
    Type: INT
    Range: 0-20
    """

    IGMonoReaderType = 96
    """
    IGMonoReaderType
    Usable in PrintSessions: false
    Type: LIST
    Possible values: REG, FILE
    """

    IGMonochromeSpeed = 97
    """
    IGMonochromeSpeed
    Usable in PrintSessions: true
    Type: INT
    Range: 1-10
    """

    IGRegionOrientation = 98
    """
    IGRegionOrientation
    Usable in PrintSessions: true
    Type: LIST
    Possible values: LANDSCAPE, PORTRAIT
    """

    IGSendIQLA = 99
    """
    IGSendIQLA
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    IGSendSpoolerSession = 100
    """
    IGSendSpoolerSession
    Usable in PrintSessions: false
    Type: LIST
    Possible values: ON, OFF
    """

    IGDisableAutoEject = 101
    """
    IGDisableAutoEject
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    IGStrictPageSetup = 102
    """
    IGStrictPageSetup
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    IGTextRectErr = 103
    """
    IGTextRectErr
    Usable in PrintSessions: true
    Type: INT
    Range: 0-20
    """

    IOverlayCustomContentAfnor = 104
    """
    IOverlayCustomContentAfnor
    Usable in PrintSessions: false
    Type: BLOB
    """

    IOverlayCustomContentIso = 105
    """
    IOverlayCustomContentIso
    Usable in PrintSessions: false
    Type: BLOB
    """

    IOverlayCustomContentMag = 106
    """
    IOverlayCustomContentMag
    Usable in PrintSessions: false
    Type: BLOB
    """

    IPipeDefinition = 107
    """
    IPipeDefinition
    Usable in PrintSessions: false
    Type: TEXT
    """

    IPostSmoothing = 108
    """
    IPostSmoothing
    Usable in PrintSessions: true
    Type: LIST
    Possible values: STDSMOOTH, ADVSMOOTH, NOSMOOTH
    """

    ISendBlankPanel = 109
    """
    ISendBlankPanel
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    IShortPanelShift = 110
    """
    IShortPanelShift
    Usable in PrintSessions: true
    Type: INT
    Range: 0-9999
    """

    Orientation = 111
    """
    Orientation
    Usable in PrintSessions: true
    Type: LIST
    Possible values: LANDSCAPE_CC90, PORTRAIT
    """

    RawData = 112
    """
    RawData
    Usable in PrintSessions: false
    Type: TEXT
    """

    Resolution = 113
    """
    Resolution
    Usable in PrintSessions: true
    Type: LIST
    Possible values: DPI300260, DPI300, DPI600300, DPI600, DPI1200300
    """

    Track1Data = 114
    """
    Track1Data
    Usable in PrintSessions: false
    Type: TEXT
    """

    Track2Data = 115
    """
    Track2Data
    Usable in PrintSessions: false
    Type: TEXT
    """

    Track3Data = 116
    """
    Track3Data
    Usable in PrintSessions: false
    Type: TEXT
    """

    PrinterIsManaged = 117
    """
    PrinterIsManaged
    Usable in PrintSessions: false
    Type: INT
    Range: 0-1
    """

    srvAddress = 118
    """
    srvAddress
    Usable in PrintSessions: false
    Type: TEXT
    """

    UIMagTrackSettingMode = 119
    """
    UIMagTrackSettingMode
    Usable in PrintSessions: false
    Type: INT
    Range: 0-1
    """

    UIRibbonMode = 120
    """
    UIRibbonMode
    Usable in PrintSessions: false
    Type: INT
    Range: 0-1
    """

    UpdatedByDrv = 121
    """
    UpdatedByDrv
    Usable in PrintSessions: false
    Type: INT
    Range: 0-1
    """

    UpdatedBySrv = 122
    """
    UpdatedBySrv
    Usable in PrintSessions: false
    Type: INT
    Range: 0-1
    """

    GColorProfileMode = 123
    """
    GColorProfileMode
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NOPROFILE, DRIVERPROFILE, CUSTOM
    """

    GColorProfile = 124
    """
    GColorProfile
    Usable in PrintSessions: true
    Type: LIST
    Possible values: STDPROFILE
    """

    GColorProfileRendering = 125
    """
    GColorProfileRendering
    Usable in PrintSessions: true
    Type: LIST
    Possible values: PERCEPTUAL, SATURATION
    """

    IGColorProfileCustom = 126
    """
    IGColorProfileCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    IGColorProfileContent = 127
    """
    IGColorProfileContent
    Usable in PrintSessions: false
    Type: BLOB
    """

    UIColorProfileName = 128
    """
    UIColorProfileName
    Usable in PrintSessions: false
    Type: TEXT
    """

    WIScanImageDepth = 129
    """
    WIScanImageDepth
    Usable in PrintSessions: false
    Type: LIST
    Possible values: BPP8, BPP16, BPP24, BPP32
    """

    WIScanImageResolution = 130
    """
    WIScanImageResolution
    Usable in PrintSessions: false
    Type: LIST
    Possible values: DPI300, DPI600
    """

    WIScanImageFileFormat = 131
    """
    WIScanImageFileFormat
    Usable in PrintSessions: false
    Type: LIST
    Possible values: JPG, BMP, PNG
    """

    WIScanSpeed = 132
    """
    WIScanSpeed
    Usable in PrintSessions: false
    Type: INT
    Range: 0-40
    """

    WIScanOffset = 133
    """
    WIScanOffset
    Usable in PrintSessions: false
    Type: INT
    Range: 0-40
    """

    WIScanCardSides = 134
    """
    WIScanCardSides
    Usable in PrintSessions: false
    Type: LIST
    Possible values: FRONT_BACK, FRONT_ONLY, BACK_ONLY
    """

    passthrough = 135
    """
    passthrough
    Usable in PrintSessions: false
    Type: TEXT
    """

    PaperSize = 136
    """
    PaperSize
    Usable in PrintSessions: true
    Type: LIST
    Possible values: CR80, ISOCR80, CR120X50, CR150X50, AVANSIACR80
    """

    FGamma = 137
    """
    FGamma
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    FGammaFactor = 138
    """
    FGammaFactor
    Usable in PrintSessions: true
    Type: INT
    Range: 0-100
    """

    BGamma = 139
    """
    BGamma
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    BGammaFactor = 140
    """
    BGammaFactor
    Usable in PrintSessions: true
    Type: INT
    Range: 0-100
    """

    FBlackPrinting = 141
    """
    FBlackPrinting
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    BBlackPrinting = 142
    """
    BBlackPrinting
    Usable in PrintSessions: true
    Type: LIST
    Possible values: ON, OFF
    """

    FSilverManagement = 143
    """
    FSilverManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NOSILVER
    """

    IFSilverCustom = 144
    """
    IFSilverCustom
    Usable in PrintSessions: true
    Type: TEXT
    """

    BSilverManagement = 145
    """
    BSilverManagement
    Usable in PrintSessions: true
    Type: LIST
    Possible values: NOSILVER
    """

    IBSilverCustom = 146
    """
    IBSilverCustom
    Usable in PrintSessions: true
    Type: TEXT
    """


