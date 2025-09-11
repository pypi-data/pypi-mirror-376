"""Fake Argyll process information."""

SUBPROCESS_COM = (
    b"Create CCMX or CCSS, Version 2.3.0\nAuthor: Graeme W. Gill, licensed under "
    b"the AGPL Version 3\nDiagnostic: Usage requested\nusage: ccxxmake -t dtech ["
    b"-options] output.ccmx\n -v Verbose mode\n -S Create CCSS rather than CCMX\n"
    b" -f ref.ti3[,targ.ti3] Create from one or two .ti3 files rather than measur"
    b"e.\n -display displayname Choose X11 display name\n -d n[,m] Choose the dis"
    b"play n from the following list (default 1)\n Optionally choose different di"
    b"splay m for VideoLUT access\n 1 name = ':1.0'\n 1 = 'Monitor 1, Output D"
    b"P-2 at 0, 0, width 2560, height 1440'\n -dweb[:port] Display via a web ser"
    b"ver at port (default 8080)\n -dcc[:n] Display via n'th ChromeCast (default"
    b" 1, ? for list)\n -d dummy Dummy (non-existant, invisible) display\n -p Use"
    b" telephoto mode (ie. for a projector, if available)\n -a Use ambient measur"
    b"ement mode (ie. for a projector, if available)\n -y l|c Other: l = LCD, c ="
    b" CRT\n -z disptype Different display type for spectrometer (see -y)\n -P ho"
    b",vo,ss[,vs] Position test window and scale it\n ho,vi: 0.0 = left/top, 0.5 "
    b"= center, 1.0 = right/bottom etc.\n ss: 0.5 = half, 1.0 = normal, 2.0 = dou"
    b"ble etc.\n -F Fill whole screen with black background\n -n Don't set overr"
    b"ide redirect on test window\n -N Disable initial calibration of instrument "
    b'if possible\n -H Use high resolution spectrum mode (if available)\n -C "com'
    b'mand" Invoke shell "command" each time a color is set\n -M "command" Invoke'
    b' shell "command" each time a color is measured\n -o observ Choose CIE Obser'
    b"ver for CCMX spectrometer data:\n 1931_2 (def), 1964_10, 2012_2, 2012_10, S"
    b"&B 1955_2, shaw, J&V 1978_2 or file.cmf\n -s steps Override default patch s"
    b"equence combination steps (default 1)\n -W n|h|x Override serial port flow "
    b"control: n = none, h = HW, x = Xon/Xoff\n -D [level] Print debug diagnostic"
    b"s to stderr\n -E desciption Override the default overall description\n -I d"
    b"isplayname Set display make and model description (optional)\n -t dtech Set"
    b" display technology type\n (Use -?? to list technology choices)\n -U c Set "
    b"UI selection character(s)\n -Y r|n Set or override refresh/non-refresh disp"
    b"lay type\n -Y R:rate Override measured refresh rate with rate Hz\n -Y A Use"
    b" non-adaptive integration time mode (if available).\n correction.ccmx | cal"
    b"ibration.ccss\n File to save result to\n",
    None,
)
