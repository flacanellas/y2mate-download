# IMPORTANT
Y2mate service has been unestable this las time... you usually will get Clouflare HTTP 522 error, it's normal behaviour.
<br>On future time on my next free weekend, i will start migrate process to **y2mate.is** service, until then, please be patient.
<br>Thanks for your understanding.

# y2mate-download
Easy client script for download Youtube videos from Y2mate.com

P.S. I love download Youtube videos from Y2mate but I feel lazy to use browser and deal with site ads. (Develop this was more fun than install ad-blocker).
<br>
P.S.2 'Readme' is english version only...

### Supported services

- Youtube Download
- Youtube MP3 Converter

---
### Warning
**Not tested on Windows yet!**

---
### About developement

This still is in dev mode, all suggestions will be heards, but I work on this on my free time.

---
### FAQ

#### About errors?

If you find some please report it on issues section.

#### Meaby an API for this?

Yes, I thoguht it already... I like the idea but right now this is only for save me time from browser use.

#### Meaby an Android APP?

Yes, I thought too, is on the task list.

#### Windows support?

On the task list too.

---

### Python Version

`+3.8`

#### Modules needed
> Please replace `pip3.8` with your pip version.

- AdvancedHTMLParser
> `pip3.8 install AdvancedHTMLParser`

- argparse
- copy
- os
- requests
> `pip3.8 install requets`

- sys
- tqdm
> `pip3.8 install tqdm`

#### Setup enviroment vars

`y2mate-download` will download files on your **env vars** paths. If isn't already setup current directory is used.

> Replace `USER_NAME` with yours.

File: `~/.bashrc`

```bash
export Y2MATE_AUDIO_FOLDER=/home/USER_NAME/Music/
export Y2MATE_VIDEO_FOLDER=/home/USER_NAME/Videos/
```

### Examples

### Version
`./y2mate-download.py -v`

### Help
`./y2mate-download.py -h`

### Debug Info
> Debug HTTP requests
`./y2mate-download.py -d`

### Verbose Info
> Show process status info
`./y2mate-download.py -ve`

---

### Download Service

---
#### Getting info about downloads options
`./y2mate-download.py -sio -f [mp3|mp4] VIDEO-URL`

#### Getting info abut specified format only
`./y2mate-download.py -sio -sfo -f [mp3|mp4] VIDEO-URL`

#### Download raw mp3 file on 128kbps
`./y2mate-download.py -f mp3 -q 128 VIDEO-URL`

#### Download raw mp4 file on 720p
`./y2mate-download.py -f mp4 -q 720 VIDEO-URL`

#### Using current directory for download
`./y2mate-download.py -cd -f [mp3|mp4] VIDEO-URL`

---

### Using MP3 Convertion service
---
#### Getting info about downloads options
`./y2mate-download.py -sio --mp3-convert -f mp3 VIDEO-URL`

#### Download (only for mp3 files)
`./y2mate-download.py --mp3-convert -f mp3 VIDEO-URL`

---
