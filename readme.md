# Iromlab

## What it does

Iromlab (Image and Rip Optical Media Like A Boss ) provides a simple and straightforward way to save the content of offline optical media from the KB collection. Internally it wraps around a number of widely-used software tools. Iromlab automatically detects if a carrier contains data, audio, or both. The content of data sessions is extracted and saved as an ISO image using [IsoBuster](https://www.isobuster.com/). For audio sessions all tracks are ripped to WAV or FLAC format with [dBpoweramp](https://www.dbpoweramp.com/). Iromlab supports 'enhanced' audio CDs that contain both audio and data sessions. ('Mixed mode' discs, which contain 1 session that holds both audio and data tracks, are currently not supported).

ISO images are verified using [Isolyzer](https://github.com/KBNLresearch/isolyzer). Audio files are checked for errors using [shntool](http://www.etree.org/shnutils/shntool/) (WAV format) or [flac](https://xiph.org/flac/) (FLAC format).

The disc images/rips are saved in a simple batch structure. Each batch contains a batch manifest, which is a comma-delimited text file with basic information about each carriers, such as:

- An identifier that links to a record in the KB catalogue.
- A serial number (because carriers may span multiple volumes).
- A carrier type code (cd-rom, dvd-rom, cd-audio or dvd-video).
- A True/False flag that indicates the status of iromlab's imaging/ripping process.

These batches can be further processed into ingest-ready Submission Information Packages using [omSipCreator](https://github.com/KBNLresearch/omSipCreator).

## Using Iromlab outside the KB

Iromlab is tailored specifically to the situation at the KB, which makes it unsuitable as a general-purpose workflow solution. This is because:

1. For each carrier it needs an identifier (PPN) that corresponds to a record in the KB catalogue. Iromlab also queries the catalogue using HTTP requests. This limits the usability of Iromlab for other users and institutions. 
2. Iromlab is based on a pretty specific hardware/software setup (see sections below). 

However, as for *1.* it should be fairly straightforward to adapt these parts of the software to other catalogues/databases. As for *2.*, most of the software dependencies are implemented using simple wrapper modules, so this is also something that can be modified quite easily. 

## Platform

MS Windows only. It may be possible to adapt the software to other platforms.

## Hardware dependencies

Iromlab was created to be used in conjuction with Acronova Nimbie disc autoloaders. It has been tested with the [Nimbie NB21-DVD model](http://www.acronova.com/product/auto-blu-ray-duplicator-publisher-ripper-nimbie-usb-nb21/9/review.html). It may work with other models as well.

## Wrapped software

Iromlab wraps around a number of existing software tools:

* [IsoBuster](https://www.isobuster.com/)
* dBpoweramp, dBpoweramp Batch Ripper and Nimbie Batch Ripper Driver; all available [from the dBpoweramp website](https://www.dbpoweramp.com/batch-ripper.htm). (Note: Iromlab wraps dBpoweramp's Nimbie driver binaries to control the disc loading / unloading process.)
* [cd-info](https://linux.die.net/man/1/cd-info) - this tool is part of [libcdio](https://www.gnu.org/software/libcdio/),  the "GNU Compact Disc Input and Control Library".
* [shntool](http://www.etree.org/shnutils/shntool/) - used to verify the integrity of created WAVE files.
* [flac](https://xiph.org/flac/) - used to verify the integrity of created WAVE files.

Both IsoBuster and dBpoweramp require a license, and they must be installed separately. Binaries of cd-info, shntool and flac are included in the iromlab installation, and they are automatically copied to directory `iromlab/tools' in the Windows user directory during the setup process.

## Documentation

* [Setup Guide](./doc/setupGuide.md) - covers installation, setup and configuration of Iromlab and the wrapped software
* [User Guide](./doc/userGuide.md) - explains how to use Iromlab.
* [Architecture Overview](./doc/architectureOverview.md) - gives an overview of Iromlab's architecture

## Contributors

Written by Johan van der Knijff, except *sru.py* which was adapted from the [KB Python API](https://github.com/KBNLresearch/KB-python-API) which is written by WillemJan Faber. 

## License

Iromlab is released under the  Apache License 2.0. The KB Python API is released under the GNU GENERAL PUBLIC LICENSE. Libcdio, shntool and flac are released under the GNU GENERAL PUBLIC LICENSE. See the directories under `tools` for the respective license statements of these tools. dBpoweramp console rip tool: copyright Illustrate Ltd., 2017.
