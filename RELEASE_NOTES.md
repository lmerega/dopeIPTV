## dopeIPTV 1.2.12

Fixes for the Windows in-app player, M3U links that turned into Xtream
logins and a crash when closing the "resume" prompt - and the results of
a full review of the code, which found parental control holes, playlists
and guides that never refreshed, and a set of smaller faults.

### Windows

- **In-app video works on PCs without a Vulkan driver.** The player
  library needs `vulkan-1.dll`, the Vulkan loader. Windows itself does
  not include it; graphics drivers install it. On a PC without one —
  an older graphics driver, a virtual machine, the basic display
  adapter — Windows refused to load the player, and every channel opened
  in an external player instead. The app now ships its own copy, and the
  build fails if the player ever needs a file that neither Windows nor
  the download provides. Thanks to @bcorsa2017 for the report and for
  confirming the cause (#19).
- **When in-app video is unavailable, Settings says why.** Under
  Settings > Playback the reason now names what is missing: the player
  file itself (often removed by an antivirus), or a file it depends on.
- **The README in the zip explains how to capture a log.**
- **No more console windows.** Every ffmpeg the app started - for a
  recording, a cast or a thumbnail - opened a console window of its own,
  and closing the one beside a recording killed the recording.
- **Local files get thumbnails**, from the ffmpeg in the download (it was
  only ever looked for on PATH, where there is none).

### Parental control

- **A locked category stays locked everywhere.** Its titles showed up on
  Home ("New movies", "New series", "New channels"), in the guide, in
  the guide search and in an actor's "other titles" - to anyone. Locked
  favorite folders showed on Home too.
- **Unlocking asks for the PIN.** Lifting a category's lock from its
  menu or from Manage categories, unlocking a favorite folder or removing
  a locked one all did so without it.
- **Each playlist keeps its own rules.** Switching playlists kept the
  previous one's hidden, renamed and locked categories.

### Playlists

- **An M3U link stays an M3U link.** A playlist served from an address
  such as `http://host:9191/output/m3u` (Dispatcharr and similar) was
  read as an Xtream login — username `output`, password `m3u` — and
  pasting it switched the playlist type to Xtream. Only a real Xtream
  stream address is read that way now, and the type you picked stays.
  Thanks to @brokenglasszero for reopening #17.
- **M3U playlists refresh.** Refresh and the automatic refresh never
  downloaded an M3U list again, and one that failed to load at startup
  stayed empty until the app restarted. A group name with a comma in it
  ("News, Sports") no longer garbles the channel.
- **Guides written as `20260927200000+0200` load.** A time zone without
  the space before it made every programme unreadable, and such a guide
  came out empty.
- **Refreshing while offline keeps the guide** you already had.

### Everywhere

- **Closing the "resume where you left off?" prompt no longer crashes the
  app.** Clicking a title under Continue watching on Home and then
  closing that prompt with the window's close button (the red button on
  macOS) crashed the whole app. Home cards now react when the mouse
  button is released, like any other button.
- **The Chromecast bridge was hardened further.** It finds the requested
  file by listing its own folder instead of building a path from the
  request.
- **Trakt stays connected.** The sign-in expires, and the app never
  renewed it: scrobbles and watched sync stopped quietly until you signed
  in again. It renews itself now. Closing the sign-in window also frees
  it for another try straight away.
- **Recordings work with more providers.** ffmpeg now identifies itself
  the way the player does, which panels that refused it accept, and a
  dropped connection no longer ends a live recording.
- **Recording from the guide uses the stream you are watching** when it
  is that channel, instead of a second connection that a
  single-connection account cuts off.
- **Renaming or moving a recording never replaces another one** that had
  the same name.
- **Posters recover from a network hiccup.** A lookup that timed out was
  remembered as "no poster" for good; an image server answering with a
  web page was fetched again on every repaint.
- **Local files**: leaving the section during a library scan no longer
  leaves the library half-scanned for the rest of the session, and "Add
  to multiview" offers every cell of a 3x3 grid.
- **The detail panel shows the right poster** when you arrow quickly
  through a list.
- **Crashes reach the log file** you attach to a bug report, with the
  account masked like every other line.

Full details in the [changelog](https://github.com/slimture/dopeIPTV/blob/main/CHANGELOG.md).

> Linux is and remains the primary target - Windows and macOS are a bonus.
