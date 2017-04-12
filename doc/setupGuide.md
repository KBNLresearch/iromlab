# Iromlab Setup Guide

Before trying to set up Iromlab, check if the following requirements are met:

* The installation platform is Microsoft Windows (tested with Windows 7). Other platforms (e.g. Linux-based one) will not work properly, because various parts of the code are Windows-specific.
* Python 3.6 (or more recent) is installed on the target platform. Older 3.x versions may (but are not guaranteed to) work.
* Since Iromlab uses the [IsoBuster](https://www.isobuster.com/) and [dBpoweramp](https://www.dbpoweramp.com/) software for data extraction and audio ripping, licensed copies of both software packages must be available.
* Iromlab was created to be used in conjuction with Acronova Nimbie disc autoloaders. It has been tested with the [Nimbie NB21-DVD model](http://www.acronova.com/product/auto-blu-ray-duplicator-publisher-ripper-nimbie-usb-nb21/9/review.html). It may work with other models as well.

Getting Iromlab up running requires a number of installation and configuration steps:

1. Install the device driver for the Nimbie disc robot
2. Install Isobuster
3. Configure Isobuster to make it play nicely with Iromlab
4. Install dBpoweramp
5. Configure dBpoweramp
6. Install Iromlab
7. Configure Iromlab 

This is a bit tedious, but you only have to do this once. Each step is described in detail below.

## Installation of Nimbie device driver

For this you need the installation disc that is shipped with the Nimbie machine. 

* Insert the installation disc in the CD-drive (not the Nimbie!).
* If the installer program does not launch automatically, navigate to the disc in Windows Explorer, right-click on *Autorun.exe* and select *Run as administrator*.
* In the opening menu, click on *Nimbie USB*.
* From the menu that appears, now select *Install Driver*.
* The device driver is now installed!

**Note:** you don't need to install any of the other software on the installation disc.


## [Isobuster setup and configuration](./setupIsobuster.md)

## [dBpoweramp setup and configuration](./setupDbpoweramp.md)

## [Iromlab setup and configuration](./setupIromlab.md)

