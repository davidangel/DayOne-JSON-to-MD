import io
import json
import os
import glob
import zipfile
import fnmatch
import shutil
import sys
from pytz import timezone
from datetime import datetime


# If you use Obsidian.md you don't have to specifically point to media file as long as they are somewhere in "embedded media" folder.
# If true link will be ![[file]] else ![](/folder/file)
relativeMediaLinking = False

# Cleans up text from "\special character"
def cleanup(input):
    def quickreplace(a, b):
        nonlocal input
        input = input.replace(a, b)

    quickreplace("\.", ".")
    quickreplace("\)", ")")
    quickreplace("\(", "(")
    quickreplace(r"\\", r"\\"[:-1])
    quickreplace("\+", "+")
    quickreplace("\!", "!")
    quickreplace("\-", "-")
    return input


# Removes everything that can't be in file name
def cleanFilename(input):
    def quickreplace(a, b):
        nonlocal input
        input = input.replace(a, b)

    quickreplace('"', "")
    quickreplace("*", "")
    quickreplace("\\", " ")
    quickreplace(r"/", " ")
    quickreplace("<", "")
    quickreplace(">", "")
    quickreplace(":", "")
    quickreplace("|", " ")
    quickreplace("?", "")
    quickreplace(".", "")

    return input


def processJson(readFrom, subfolder, tempsubfolder, outpath):

    with io.open(readFrom, encoding="utf-8") as read_file:
        data = json.load(read_file)

    # Setting and creating output folder structure
    folderpath = outpath + "/" + subfolder + "/"
    if not os.path.exists(folderpath):
        os.makedirs(folderpath)

    if not os.path.exists(folderpath + "/audios/"):
        os.makedirs(folderpath + "/audios/")
    if not os.path.exists(folderpath + "/pdfs/"):
        os.makedirs(folderpath + "/pdfs/")
    if not os.path.exists(folderpath + "/photos/"):
        os.makedirs(folderpath + "/photos/")
    if not os.path.exists(folderpath + "/videos/"):
        os.makedirs(folderpath + "/videos/")

    yesterday = datetime.now().strftime('%Y-%m-%d')

        text = entry["text"]

        # 2020-01-31T09:44:02Z => 2020.01.31 09-44
        # date = entry['creationDate'][:-4].replace("-", ".").replace(":", "-").replace("T", " ")
        myTimezone = timezone(entry['timeZone'].replace("\\", ""))
        myDate = datetime.strptime(entry['creationDate'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone('UTC')).astimezone(myTimezone)
        date = myDate.strftime('%Y-%m-%d %H-%M-%S')
        if myDate.strftime('%Y-%m-%d') == yesterday:
            print("Duplicated date:",yesterday)
        yesterday = myDate.strftime('%Y-%m-%d')

        # If first line starts with "# " — treat it as entry title
        if text.split("\n")[0][:2] == "# ":
            title = text.split("\n")[0].replace("# ", "").replace("#", "")
            text = text[text.find("\n")+2:]
        else:
            title = ""

        # Process all "dayone-moments"(photos and audios)
        splitted = text.split("\n")
        filtered = fnmatch.filter(splitted, "![](dayone-moment:*)")

        for moment in filtered:
            # ![](dayone-moment:\/\/F7EEC3394BC0455FA513D9CAA0557C7E) => F7EEC3394BC0455FA513D9CAA0557C7E) = > F7EEC3394BC0455FA513D9CAA0557C7E
            momentIdentifier = moment.split("/")[-1]
            momentIdentifier = momentIdentifier[:-1]

            # Iterate over all media attached to entry and find filename and format of the right one

            if "audio" in moment:
                momentIn = entry["audios"]
                folder = "audios"
            elif "video" in moment:
                momentIn = entry["videos"]
                folder = "videos"
            elif "pdfAttachment" in moment:
                momentIn = entry["pdfAttachments"]
                folder = "pdfs"
            else:
                momentIn = entry["photos"]
                folder = "photos"
            for momentItem in momentIn:
                if momentIdentifier == momentItem["identifier"]:
                    if "type" in momentItem:
                        momentFormat = momentItem["type"]
                    else:
                        momentFormat = momentItem["format"]
                        # For some reason "format" is codec not container — "aac" corresponds to "m4a" files. This is a stupid fix but still.
                        if momentFormat == "aac":
                            momentFormat = "m4a"

                    # Jpegs have filenames. Audios don't
                    if "filename" in momentItem:
                        # Filename has file extension in it, we only need the name.
                        newName = momentItem["filename"].split(".")[0]
                    elif "md5" in momentItem:
                        newName = momentItem["md5"]
                    else:
                        if 'date' in momentItem:
                            # newName = momentItem['date'][:-4].replace("-", ".").replace(":", "-").replace("T", " ") + " " + momentIdentifier
                            newName = datetime.strptime(momentItem['date'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone('UTC')).astimezone(myTimezone).strftime('%Y-%m-%d %H-%M-%S') + " " + momentIdentifier
                        else:
                            # newName = date + " id " + momentIdentifier
                            newName = date + " " + momentIdentifier

                    momentFile = momentItem["md5"]

            shutil.copy2(
                f"temp/{tempsubfolder}/{folder}/{momentFile}.{momentFormat}",
                f"./out/{subfolder}/{folder}/{newName}.{momentFormat}",
            )

            if relativeMediaLinking:
                text = text.replace(moment, f"![[{newName}.{momentFormat}]]")
            else:
                newName = newName.replace(' ','%20')
                text = text.replace(moment, f"![](/{folder}/{newName}.{momentFormat})")
            
        rawtags = entry.get('tags')
        location = entry.get('location')
        
        if rawtags:
            # We only need to append tags that aren't set in text
            filteredtags = []
            for tag in rawtags:
                if "#" + tag not in text:
                    filteredtags.append(tag.replace(" ", ""))
                else:
                    print('This tag was ignored as it was in text: ',tag)

        text = cleanup(text)
        title = cleanup(title)
        title = cleanFilename(title)

        yamlString = "---\n"+"title: "+title+"\n"
        yamlString += "date: " + datetime.strptime(entry['creationDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone('UTC')).astimezone(myTimezone).strftime('%Y-%m-%d %H:%M:%S') + "\n"
        if len(filteredtags)>0:
            # add metadata for tags
            yamlString+="tags:\n- "+ "\n- ".join(filteredtags) + "\n"

        if location:
            yamlString += "latitude: " + str(location['latitude']) + "\n"
            yamlString += "longitude: " + str(location['longitude']) + "\n"

        yamlString+="---\n\n"

        # newfilename = date +" — " + title + ".md"
        newfilename = date[:-9] + ".md"
        newfile = io.open(folderpath  +  "/" + newfilename , mode="a", encoding="utf-8")
        newfile.write(yamlString)
        newfile.write(text)


def ProcessZips(inpath, outpath):
    for zipname in os.listdir(inpath + "/"):
        if zipname.endswith(".zip"):
            zipnameClean = zipname.split(".")[0]
            with zipfile.ZipFile(inpath + "/" + zipname, "r") as zip_ref:

                zip_ref.extractall("temp/" + zipnameClean)

            for jsonname in os.listdir("temp/" + zipnameClean):
                jsonnameClean = jsonname.split(".")[0]
                if jsonname.endswith(".json"):
                    processJson(
                        "temp/" + zipnameClean + "/" + jsonname,
                        jsonnameClean,
                        zipnameClean,
                        outpath,
                    )
    shutil.rmtree("temp")


if __name__ == "__main__":
    inpath = "in"
    outpath = "out"
    ProcessZips(inpath, outpath)
    print(f"Finished, check {outpath} folder")
