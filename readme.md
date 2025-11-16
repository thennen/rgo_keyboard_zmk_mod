# Not putting the zmk folder here as it is 4 gb for some reason
# here's how I set it up

pip install west
set PATH=%PATH%;"C:\Users\t\anaconda3\Scripts";"C:\QMK_MSYS\mingw64\bin"
git clone https://github.com/zmkfirmware/zmk zmk
cd zmk
west init -l app/
west update
west zephyr-export

# from elevated powershell
choco install cmake ninja dtc-msys2 gperf

pip install -r zephyr/scripts/requirements-base.txt

cd %HOMEPATH%
wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.16.3/zephyr-sdk-0.16.3_windows-x86_64.7z
7z x zephyr-sdk-0.16.3_windows-x86_64.7z
cd zephyr-sdk-0.16.3
setup.cmd


# only this directory matters, doesn't actually have to be in the zmk folder
mkdir config/boards/shields/rgo

# I think you are supposed to make some kind of zmk "module" with a whole ton of files in it

cd app
west build -p -b nice_nano_v2 -- -DSHIELD=rgo_right -DZMK_CONFIG="../config"

# for split build

west build -d build/left -p -b nice_nano_v2 -- -DSHIELD=rgo_left -DZMK_CONFIG="../config"
west build -d build/right -p -b nice_nano_v2 -- -DSHIELD=rgo_right -DZMK_CONFIG="../config"

# this shit doesn't go into bootloader mode unless you disconnect the power
west build -d build/reset -p -b nice_nano_v2 -- -DSHIELD=settings_reset

# for separately connected halves with _left _right suffixes, add
-DCONFIG_ZMK_SPLIT=n


and all these columns and rows
of immaculate flows
hacker poetry prose
hit it right on the nose