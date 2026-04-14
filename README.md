# J1850VPW_USB_HW-SW
Contains the hardware and software to go with the J1850VPW_USB repo
Note: if your module is not showing up as a serial port, you need to install the CH340 driver.

## Software
C# project built in Visual Studio. Located in the SW subfolder
"Bridge Pro" allows you to send and receive J1850VPW frames. It also allows for a scripted playback
This program supports all the commands for the 99-02 swap box if you have one and need to configure it. I really wrote this tool as a tool for configuring that but also added a few features.

Scripted playback
"#" and"//" are ignored
"*XXXX" sets the delay in mS where *100 would be a 100ms delay between frames.
Do not include the CRC its already calculated by the module.

## Hardware
SCH and Gerbers are available in the HW subfolder

## Firmware 
It's in its own repo https://github.com/garnerm91/J1850VPW_USB


## REv A video
[![Rev A video](https://img.youtube.com/vi/8Q_QOkDVAA0/0.jpg)](https://youtu.be/8Q_QOkDVAA0)
