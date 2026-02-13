# 🎮 Cheat Editor Manager Tool

> Edit. Organise. Export.\
> Cheat files made simple for emulators and modded consoles.

------------------------------------------------------------------------

## 🚀 What Is This?

**Cheat Editor Manager Tool** is a desktop app that lets you:

✔ Edit cheat files safely\
✔ Automatically build correct folder structures\
✔ Detect Switch TitleID (TID) & BuildID (BID)\
✔ Export to the correct emulator format\
✔ Manage custom emulator profiles\
✔ Avoid breaking file paths

You don't need to know where cheats go.\
The program handles it.

------------------------------------------------------------------------

# 🧠 Who Is This For?

-   🎮 Emulator users\
-   🔓 Switch CFW users\
-   🕹 RetroArch users\
-   🧩 Modded console users\
-   👶 Beginners who don't understand folder structures\
-   🛠 Advanced users who want control

------------------------------------------------------------------------

# 🖥 Supported Platforms

## 🧰 PC Emulators

-   Yuzu\
-   Ryujinx\
-   RetroArch\
-   Dolphin\
-   PCSX2\
-   PPSSPP\
-   DuckStation\
-   RPCS3\
-   Cemu\
-   Xenia

## 🔓 Switch Custom Firmware

-   Atmosphère (CFW)

## 🧩 Modded Consoles

-   Nintendo 3DS (Luma)\
-   PSP (CFW)\
-   PS Vita (taiHEN)\
-   Wii (Homebrew)\
-   Wii U (CFW)

You can also create your own custom profile.

------------------------------------------------------------------------

# 🧭 How To Use (Beginner Guide)

## 1️⃣ Select Your Emulator / Console

Choose your platform at the top of the app.

This controls:

-   Folder structure\
-   File extension\
-   Export behaviour\
-   Helper instructions

------------------------------------------------------------------------

## 2️⃣ Load A Cheat File (Optional)

Click:

Load File...

If it's a Switch cheat file:

✔ TitleID auto-detected\
✔ BuildID auto-detected\
✔ Editor remains cheat-text only

------------------------------------------------------------------------

## 3️⃣ Edit Your Cheats

Use the Cheat Editor box to:

-   Add cheats\
-   Modify codes\
-   Remove cheats\
-   Undo / Redo\
-   Add headings\
-   Wrap text\
-   Clear safely

------------------------------------------------------------------------

## 4️⃣ Quick Export (Recommended)

Click:

Quick Export

The program automatically builds the correct folder structure.

Examples:

Switch (Atmosphère)
atmosphere/contents/`<TID>`{=html}/cheats/`<BID>`{=html}.txt

Yuzu load/`<TID>`{=html}/`<Cheat Name>`{=html}/cheats/`<BID>`{=html}.txt

RetroArch cheats/`<Core Name>`{=html}/`<Game>`{=html}.cht

Dolphin GameSettings/`<GameID>`{=html}.ini

No manual folder creation required.

------------------------------------------------------------------------

## 5️⃣ Convert & Save (Advanced Option)

Use this if you want to:

-   Choose your own folder\
-   Pick a different extension\
-   Rename the file

You will select the extension first, then save location.

------------------------------------------------------------------------

# 🧩 Understanding The Helper Section

The Helper box changes based on the selected emulator.

Switch Profiles: - Shows TitleID field - Shows BuildID field

RetroArch: - Shows Core selector

Other Emulators: - Shows relevant export instructions

This section does NOT modify cheat text.

------------------------------------------------------------------------

# 🛠 Custom Profiles

You can create your own emulator or custom firmware profile.

You define:

-   Folder structure\
-   File extension\
-   Helper instructions

Custom profiles appear in the main dropdown automatically.

Built-in profiles remain untouched.

------------------------------------------------------------------------

# 🎨 Appearance

You can:

-   Switch Dark / Light mode\
-   Enable full Custom colour mode\
-   Reset to default colours

------------------------------------------------------------------------

# ⚙ Advanced

-   Override export paths (optional)\
-   Remember window size

Defaults are safe.

------------------------------------------------------------------------

# 🔒 Design Philosophy

The editor contains cheat text only.

IDs, folder paths, and structure are handled by the tool.

This prevents:

-   Broken exports\
-   Wrong folder placement\
-   Incorrect file naming

------------------------------------------------------------------------

# 📦 Building The Program

Using PyInstaller:

py -m PyInstaller --clean --noconfirm --onefile --windowed --name
"cheat_editor_manager_tool" cheat_editor_manager_tool.py

------------------------------------------------------------------------

# 🎯 Goal Of The Tool

You focus on editing cheats.

The program handles:

-   Structure\
-   Format\
-   Extensions\
-   Export safety

------------------------------------------------------------------------

# 🧑‍💻 Credits

Concept & Design: Marcus\
Development Support: ChatGPT
