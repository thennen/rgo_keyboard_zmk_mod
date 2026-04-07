# tl;dr: How to compile and flash when environment is already set up

Put keyboard into bootloader mode (left half: Fn-1, right half: RCtrl-7), then in cmd.exe:
```
set PATH=%PATH%;"C:\Users\t\anaconda3\Scripts";"C:\QMK_MSYS\mingw64\bin"
subst Q: "C:\Users\t\Proton Drive\My files\github\rgo_wireless"
cd desktop\zmk\app
west build -d build/left -p -b nice_nano_v2 -- -DSHIELD=rgo_left -DZMK_CONFIG="Q:/config" -DZMK_EXTRA_MODULES="Q:/zmk-unicode"
copy build\left\zephyr\zmk.uf2 E:\zmk.uf2
```


# How I set up zmk to locally build and flash firmware to rgo (2x nice!nano) on windows:

You need to clone zmk, I did not add it to this repo because it is 4 gb for some reason

```
pip install west
set PATH=%PATH%;"C:\Users\t\anaconda3\Scripts";"C:\QMK_MSYS\mingw64\bin"

git clone https://github.com/zmkfirmware/zmk zmk
cd zmk
west init -l app/
west update
west zephyr-export
```

From elevated powershell:
```
choco install cmake ninja dtc-msys2 gperf
```

```
pip install -r zephyr/scripts/requirements-base.txt
```

```
cd %HOMEPATH%
wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.16.3/zephyr-sdk-0.16.3_windows-x86_64.7z
7z x zephyr-sdk-0.16.3_windows-x86_64.7z
cd zephyr-sdk-0.16.3
setup.cmd
```

only this directory matters for the keyboard config, and it doesn't actually have to be in the zmk folder

```
mkdir config/boards/shields/rgo
```
I think you are rather supposed to make some kind of zmk "module" with a whole ton of files in it, but the above still works.  Module might be important if you want to build with github actions...


To build you need to be in the zmk/app folder
```
cd desktop\zmk\app
```

In the build command you have to point to the config directory.  but West can't handle spaces in paths even if quoted. I just use subst as a workaround (windows):

```
subst Q: "C:\Users\t\Proton Drive\My files\github\rgo_wireless"
```

for a split build
```
west build -d build/left -p -b nice_nano_v2 -- -DSHIELD=rgo_left -DZMK_CONFIG="Q:/config" -DZMK_EXTRA_MODULES="Q:/zmk-unicode"
```
```
west build -d build/right -p -b nice_nano_v2 -- -DSHIELD=rgo_right -DZMK_CONFIG="Q:/config" -DZMK_EXTRA_MODULES="Q:/zmk-unicode"
```


Sometimes you need to "reset" the keyboard by clearing the non-volatile memory.  This firmware is supposed to do that but stupidly doesn't go into bootloader mode again until you reset/ cycle the power
```
west build -d build/reset -p -b nice_nano_v2 -- -DSHIELD=settings_reset
```

There are some config settings that get overwritten when zmk detects that you are trying to compile a split keyboard.  I think this is just detected by whether there are _left or _right suffixes on the config file names..
The only way to override it is to use a command line option, so e.g. if you want to separately connect the two halves to the keyboard you have build with
```
-DCONFIG_ZMK_SPLIT=n
```

Put the left side bootloader mode, then:
```
copy build\left\zephyr\zmk.uf2 E:\zmk.uf2
```

right in bootloader, then:
```
copy build\right\zephyr\zmk.uf2 E:\zmk.uf2
```


btw I think west.yml and rgo.zmk.yml don't do anything because I build locally, that's some github shenanigans