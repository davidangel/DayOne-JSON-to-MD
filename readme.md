# Day One JSON to Markdown (Obsidian)
A python script that converts [Day One](https://dayoneapp.com/) exports (JSON packed with media files into a zip file) to Markdown.

This is useful for exporting Day One entries to [Obsidian](https://obsidian.md/). By default it uses Obsidian's `![[]]` linking, change relativeMediaLinking value inside to `False` if you want regular Markdown links ( `![]()`).

Based on [ze-kel's efforts](https://github.com/ze-kel/DayOne-JSON-to-MD) to export text, headers, tags, date, photos and audios. I've extended this a bit to include videos and pdf attachments, as well.

## Usage
1. Install python 3
2. Go to **Day One: File > Export > JSON**. You can export everything to one zip file or have separate ones.
3. Download convert.py
4. Create "in" folder in the same directory as convert.py and place all Day One export zip files there
5. Run ```python convert.py```

----------

**Note**: Video files that use `.mov` are not currently embeddable in Obsidian, but Obsidian will open the default video player when these links are clicked. I wonder if this code could be extended to use `ffmpeg` to convert those videos... :-)