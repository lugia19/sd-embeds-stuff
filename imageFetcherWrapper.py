# Yeah I could use requests but I'd rather use something builtin
from math import floor
from urllib import request, parse
from datetime import date, datetime
import time
import os
import re
import shutil
import subprocess
import json
import pathlib


class ImageData:
    def __init__(self, path, resolution):
        self.path = path
        self.width = int(resolution[0:resolution.find("x")])
        self.height = int(resolution[resolution.find("x")+1:len(resolution)])
        self.filename = path[path.rfind("\\")+1:len(path)]
        if path != "":
            self.size = os.path.getsize(path)
        else:
            self.size = 0

    def __str__(self):
        return "filename: {0}, resolution: {1}x{2}, size: {3}".format(self.filename, self.width, self.height, self.size)


def askYesNo(prompt) -> bool:
    print(prompt)
    answerTemp = input("Type y/n\n")
    while len(answerTemp) < 1 or (answerTemp.lower()[0] != "y" and answerTemp.lower()[0] != "n"):
        print("Not a valid answer. \n")
        answerTemp = input("y/n\n")
    return answerTemp.lower()[0] == "y"


lastAPICallTime = datetime.now()
msBetweenRequestsMinimum = 300


def getTopImages(URL, targetNum) -> list[str]:
    print("Scraping image links...")
    tags = URL[URL.find("&tags=")+len("&tags="):]
    global lastAPICallTime
    msDelta = (datetime.now() - lastAPICallTime).microseconds / 1000
    if msDelta < msBetweenRequestsMinimum:
        secondsToSleep = (msBetweenRequestsMinimum - msDelta) / 1000
        print("Waiting " + str(secondsToSleep*1000) +
              " ms to avoid spamming the API...")
        time.sleep(secondsToSleep)
    lastAPICallTime = datetime.now()

    if "sort:score" not in tags:
        if tags[len(tags)-1] != "+":
            tags += "+"
        tags += "sort:score"

    imageCount = 0
    imageURLs = list()
    while imageCount < targetNum:
        page = json.load(request.urlopen("https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&tags=" + tags + "&pid=" + str(floor(imageCount/100))))
        print("")

        for post in page["post"]:
            if imageCount < targetNum:
                imageCount += 1
                imageURLs.append("https://gelbooru.com/index.php?page=post&s=view&id=" + str(post["id"]) + "\n")

        if len(page["post"]) < 100: #The query returned less than 100 images. We're done.
            print("Not enough images to reach the target, stopping at " + str(imageCount))
            break

    return imageURLs



def requestTagData(APIProvider, tag) -> dict:
    tagData = {}
    tag = parse.quote(tag)
    global lastAPICallTime
    msDelta = (datetime.now() - lastAPICallTime).microseconds / 1000
    if msDelta < msBetweenRequestsMinimum:
        secondsToSleep = (msBetweenRequestsMinimum - msDelta) / 1000
        print("Waiting " + str(secondsToSleep*1000) +
              " ms to avoid spamming the API...")
        time.sleep(secondsToSleep)
    lastAPICallTime = datetime.now()
    match APIProvider:
        case "gelbooru":
            page = json.load(request.urlopen(
                "https://gelbooru.com/index.php?page=dapi&s=tag&q=index&json=1&name=" + tag))
            pageTagData = page["tag"][0]
            # "type" values: 0 - Normal, 1 - Artist, 2 - Unused?, 3 - Series/Copyright, 4 - Character, 5 - meta (highres, etc)
            tagData["name"] = pageTagData["name"]
            tagData["id"] = pageTagData["id"]
            tagData["count"] = pageTagData["count"]
            match pageTagData["type"]:
                case 0: tagData["type"] = "normal"
                case 1: tagData["type"] = "artist"
                case 3: tagData["type"] = "copyright"
                case 4: tagData["type"] = "character"
                case 5: tagData["type"] = "meta"
                case 6: tagData["type"] = "deprecated"
                case _: tagData["type"] = "unknown"

        case "danbooru":
            page = json.load(request.urlopen(
                "https://danbooru.donmai.us/tags.json?search[name]=" + tag))
            pageTagData = page[0]
            tagData["name"] = pageTagData["name"]
            tagData["id"] = pageTagData["id"]
            # Name it count like it should be.
            tagData["count"] = pageTagData["post_count"]

            match pageTagData["category"]:
                case 0: tagData["type"] = "normal"
                case 1: tagData["type"] = "artist"
                case 3: tagData["type"] = "copyright"
                case 4: tagData["type"] = "character"
                case 5: tagData["type"] = "meta"
                case _: tagData["type"] = "unknown"
            if "is_deprecated" in pageTagData and pageTagData["is_deprecated"]:
                tagData["type"] = "deprecated"

    tagData["lastUpdate"] = date.today().isoformat()
    return tagData

def main():
    global lastAPICallTime
    cwd = os.getcwd()
    configFilePath = os.path.join(cwd, "config.json")
    tagDatabasePath = os.path.join(cwd, "tagDatabase.json")
    if not os.path.exists(tagDatabasePath):
        json.dump({}, open(tagDatabasePath, mode="w", encoding="utf-8"),
                  indent=4)  # Create empty file
    try:
        tagsDB = json.load(open(tagDatabasePath, mode="r", encoding="utf-8"))
    except:
        print("Error loading tag database file! Resetting it...")
        json.dump({}, open(tagDatabasePath, mode="w", encoding="utf-8"), indent=4)
        tagsDB = {}

    defaultConfigData = {
        # Path to czkawka-cli
        "czkawka_cli_path": os.path.join(cwd, "windows_czkawka_cli.exe"),
        # Path to gallery-dl
        "gallery-dl_path": os.path.join(cwd, "gallery-dl.exe"),
        "root_download_folder": cwd,  # Folder to put downloaded images
        "backup_original_folder": True,  # Back up images before processing
        "supress_tag_suggestions": False,  # Stop suggesting tags
        "czkawka_similarity_preset": "Minimal",  # Czkawka setting
        "czkawka_algorithm": "Lanczos3",  # Czkawka setting
        # Will warn (and allow the user to add if doing a download) when these tags aren't filtered out
        "tags_to_warn_when_not_excluded": ["text_focus", "monochrome", "character_profile"],
        # Will warn (and allow the user to add if doing a download) when these tags aren't included in the search
        "tags_to_warn_when_not_included": ["solo"],
        # Tags that have less than this amount of posts will get removed (-1 to disable).
        "tags_count_ignored_threshold": 10,
        #How many days before tag data needs to be re-downloaded (-1 to disable)
        "tag_data_expiration_days": 30,
        # Controls whether or not tags get _ replaced by spaces and () escaped.
        "convert_tags_to_DDB_format": False
    }

    if not os.path.exists(configFilePath):
        print("Error. Config file missing.\n")
        print(
            "I'm going to create the config file in this directory ASSUMING that you have gallery-dl and czkawka-cli in the same folder as this script "
            "and that you'd like the downloaded images to be here as well. If that is not the case, you can edit config.json later.\n")

        json.dump(defaultConfigData, open(configFilePath, mode="w", encoding="utf-8"), indent=4)

    configData = json.load(open(configFilePath, encoding="utf-8"))

    missingKeys = False
    for key in defaultConfigData:
        if key not in configData:
            missingKeys = True
            configData[key] = defaultConfigData[key]
    if missingKeys:
        json.dump(configData, open(configFilePath, mode="w", encoding="utf-8"), indent=4)

    czkawkaCLIPath = configData["czkawka_cli_path"]
    if not os.path.exists(czkawkaCLIPath):
        print("Error. Czkawka CLI path is not valid. You probably forgot to escape the backslashes (every \\ should be replaced by \\\\).")
        exit()

    galleryDLPath = configData["gallery-dl_path"]
    if not os.path.exists(galleryDLPath):
        print("Error. gallery-dl_path is not valid. You probably forgot to escape the backslashes (every \\ should be replaced by \\\\).")
        exit()

    rootDownloadFolder = configData["root_download_folder"]
    if not os.path.exists(rootDownloadFolder):
        print("Error. root_download_folder is not valid. You probably forgot to escape the backslashes (every \\ should be replaced by \\\\).")
        exit()

    convertTagsToDDBFormat = configData["convert_tags_to_DDB_format"]

    print("Do you want to:")
    print("1) Download images via gallery-dl and deduplicate them")
    print("2) Deduplicate images you've already downloaded within a directory")
    choice_num = -1
    while not (0 < choice_num < 3):
        try:
            choice_num = int(
                input("Please select which option you'd like and press enter.\n"))
        except:
            print("Not a valid number.")
    overrideDir = (choice_num == 2)

    imageDirs = []

    if overrideDir:  # If the directory is overridden, simply run it on this directory
        runAgain = True
        while runAgain:
            print(
                "Please input the directory you'd like to run the program on and press enter.")
            imageDir = input()
            while not os.path.exists(imageDir):
                imageDir = input(
                    "Specified image directory does not exist! Try again.\n")
            imageDirs.append(imageDir)
            runAgain = askYesNo(
                "Would you like to queue another up directory?")
    else:
        print("Note: downloaded images are saved in " +
              rootDownloadFolder+"\\gallery-dl\\[sitename]\\[tags]")
        print("I'm going to assume that this is a valid link that gallery-dl can actually use.")
        runAgain = True
        downloadURLs = []
        ignoreTagSuggestions = configData["supress_tag_suggestions"]
        # ["monochrome"]
        tagsToFilterOut = configData["tags_to_warn_when_not_excluded"]
        tagsToFilterIn = configData["tags_to_warn_when_not_included"]

        while runAgain:
            newDownloadData = dict()
            redo = True
            while redo:
                newDownloadData["URL"] = input(
                    "Please input the URL and press enter.\n")
                if "gelbooru" in newDownloadData["URL"] and "&pid" in newDownloadData["URL"]:
                    newDownloadData["URL"] = str(newDownloadData["URL"])[
                        :newDownloadData["URL"].rfind("&")]
                redo = False
                # Don't suggest tags if the URL is from danbooru, due to the 2 tag maximum.
                if not ignoreTagSuggestions and "danbooru.donmai.us" not in newDownloadData["URL"]:
                    for tag in tagsToFilterOut:
                        if "-" + tag not in newDownloadData["URL"]:
                            print(
                                "You didn't filter out " + tag + " in the search, which is recommended for better results.")
                            if askYesNo("Would you like to add it?"):
                                newDownloadData["URL"] += "+-" + tag
                    for tag in tagsToFilterIn:
                        if not "+" + tag in newDownloadData["URL"] or "=" + tag in newDownloadData["URL"]:
                            print("You didn't include " + tag +
                                  " in the search, which is recommended for better results.")
                            if askYesNo("Would you like to add it?"):
                                newDownloadData["URL"] += "+" + tag

            if askYesNo("Would you like to download only a certain amount of images?"):
                range_max = -1
                while not (0 < range_max):
                    try:
                        range_max = int(
                            input("How many images max would you like to download?.\n"))

                        if "sort:score" in newDownloadData["URL"] or askYesNo("Would you like to get the top rated images? (No will pull the latest instead)"):
                            newDownloadData["URL_list"] = getTopImages(newDownloadData["URL"], range_max)
                        else:
                            newDownloadData["range_max"] = str(range_max)
                    except:
                        print("Not a valid number.")
            downloadURLs.append(newDownloadData)

            runAgain = askYesNo("Would you like to queue up another URL?")
        # Directory not overridden, run gallery-dl
        for downloadData in downloadURLs:
            downloadURL = downloadData["URL"]
            dlcommand = galleryDLPath + " \"" + downloadURL + "\"" + \
                " --write-tags " + \
                " --write-metadata " + \
                " --exec-after \"echo {} > outputdir.txt\""
            if "range_max" in downloadData:
                dlcommand += " --range 1-" + downloadData["range_max"]
            if "URL_list" in downloadData:
                dlcommand += " --range 1-1"
            print(dlcommand)
            subprocess.run(dlcommand, cwd=rootDownloadFolder)

            imageDirFile = open(os.path.join(
                rootDownloadFolder, "outputdir.txt"), mode="r", encoding="utf-8")
            imageDir = imageDirFile.read().strip()
            print("imagedir got from gallery-dl:")
            print(imageDir)
            if imageDir[1] != ":" or imageDir[len(imageDir)-1] == "\"":
                print("For some reason it's a bit fucked. Fixing it...")
                if imageDir[1] != ":":
                    startIndex = imageDir.index(":")-1
                    imageDir = imageDir[startIndex:len(imageDir)]
                if imageDir[len(imageDir)-1] == "\"":
                    endIndex = imageDir.rindex("\\")
                    imageDir = imageDir[:endIndex]
                print("Fixed up path:")
                print(imageDir)

            if "URL_list" in downloadData:
                downloadLinksFile = open(os.path.join(
                    rootDownloadFolder, "links.txt"), mode="w", encoding="utf-8")
                downloadLinksFile.writelines(downloadData["URL_list"])
                downloadLinksFile.close()
                dlcommand = galleryDLPath + \
                            " --write-tags " + \
                            " --write-metadata " + \
                            " -D " + "\"" + imageDir + "\"" + \
                            " -i " + os.path.join(rootDownloadFolder, "links.txt")
                print(dlcommand)
                subprocess.run(dlcommand, cwd=rootDownloadFolder)

            imageDirs.append(imageDir)

    for imageDir in imageDirs:
        # Acceptable values: Minimal, VerySmall, Small, Medium, High, VeryHigh (minimal works best in my experience)
        similarityPreset = configData["czkawka_similarity_preset"]
        # Allowed: Lanczos3, Nearest, Triangle, Faussian, Catmullrom
        algorithm = configData["czkawka_algorithm"]

        backupOriginalFolder = configData["backup_original_folder"]

        blockIndicator1 = "images which have similar friends"
        blockIndicator2 = "Found"
        separator = " - "

        tempFile = os.path.join(imageDir, "output.txt")
        if os.path.exists(tempFile):
            os.remove(tempFile)
        backupDir = os.path.join(imageDir, "backup")

        if os.path.exists(backupDir) and backupOriginalFolder:
            print("The backup folder already exists! Would you like to:")
            print("1) Delete it and back up again")
            print("2) Skip the backup")
            print("3) Exit")
            answerTemp = input("\n")
            while answerTemp != "1" and answerTemp != "2" and answerTemp != "3":
                print("Not a valid answer. \n")
                answerTemp = input("\n")
            if answerTemp == "1":
                shutil.rmtree(backupDir)
            elif answerTemp == "2":
                backupOriginalFolder = False
            else:
                exit(1)

        if backupOriginalFolder:
            print("Backing up existing images...")
            shutil.copytree(imageDir, backupDir)
            print("Backed up the image folder to " + backupDir)

        while True:
            fullCommand = czkawkaCLIPath + " image" + \
                " -z " + algorithm + \
                " -s " + similarityPreset + \
                " -f \"" + tempFile + "\"" + \
                " -d \"" + imageDir + "\"" + \
                " -e \"" + backupDir + "\""
            print(fullCommand)
            subprocess.run(fullCommand)
            allLines = open(tempFile, "r", encoding="utf-8").readlines()
            if "Not found any similar images" in allLines[1]:
                os.remove(tempFile)
                break

            currentLine = -1
            for s in allLines:
                currentLine += 1
                print(s)
                if blockIndicator1 in s and blockIndicator2 and not separator in s:  # Start of a new block
                    index = currentLine + 1
                    images = []
                    while pathlib.Path(imageDir).anchor in allLines[index]:
                        line = allLines[index]
                        print(line)
                        separatorIndex = line.find(separator)
                        separator2Index = line.find(
                            separator, separatorIndex + len(separator))
                        images.append(
                            ImageData(line[0:separatorIndex], line[separatorIndex + len(separator):separator2Index]))
                        print(images[len(images) - 1])
                        index += 1
                    if len(images) > 0:
                        maxImage = ImageData("", "0x0")
                        for image in images:
                            print(image)
                            if image.width * image.height > maxImage.width * maxImage.height or image.size > maxImage.size:
                                maxImage = image
                        print("Selected image:")
                        print(maxImage)
                        for image in images:

                            if image.path != maxImage.path:
                                os.remove(image.path)
                                tagsPath = image.path + ".txt"
                                if os.path.exists(tagsPath):
                                    print(
                                        "Deleting associated tags file:" + tagsPath)
                                    os.remove(tagsPath)
                                metadataPath = image.path + ".json"
                                if os.path.exists(metadataPath):
                                    print(
                                        "Deleting associated metadata file:" + metadataPath)
                                    os.remove(metadataPath)
                        print(
                            "Deleted copies (and associated tag files if they existed).")
            # Prep for the next loop
            os.remove(tempFile)

        # we're done removing duplicates
        if askYesNo("Would you like to keep only a certain number of the most upvoted images?"
                    "(For example only the 100 most upvoted)"):
            scores = {}
            for filename in os.listdir(imageDir):
                metadataPath = os.path.join(imageDir, filename)
                if os.path.isfile(metadataPath) and ".json" in metadataPath:
                    metadata = json.load(open(metadataPath, mode="r"))
                    scores[metadataPath.replace(
                        ".json", "")] = metadata["score"]
            currentNumber = 0

            numOfImages = -1
            while not (0 < numOfImages):
                try:
                    numOfImages = int(
                        input("Please input how many of the top images you'd like to keep.\n"))
                    if numOfImages >= len(scores):
                        if not askYesNo("That's every image you've downloaded (" + str(len(scores)) + "). Is that okay?"):
                            numOfImages = -1
                except:
                    print("Not a valid number.")

            for imagePath in sorted(scores, key=scores.get, reverse=True):
                print(imagePath + " : " + str(scores[imagePath]))
                currentNumber += 1
                if currentNumber > numOfImages:
                    print("Deleting this...")
                    os.remove(imagePath)
                    tagsPath = imagePath + ".txt"
                    if os.path.exists(tagsPath):
                        os.remove(tagsPath)
                    else:  # Delete it even if it's already been converted to the correct filename.
                        imageExtension = imagePath[imagePath.rindex("."):]
                        tagsPath = tagsPath.replace(imageExtension, "")
                        if os.path.exists(tagsPath):
                            os.remove(tagsPath)

                    if os.path.exists(imagePath + ".json"):
                        os.remove(imagePath + ".json")

        print("Converting tag files...")

        # we have all the tags in the gelbooru format in tagsDict.
        # Now we check if we know their count and metadata, otherwise we pull it from the provider.
        # Also we check if it's a series tag, in which case we throw it out (pretty sure it's literally just bad data for the AI)
        lastBackslashIndex = imageDir.rfind("\\")
        secondToLastBackslashIndex = imageDir[:lastBackslashIndex].rfind("\\")
        APIProvider = imageDir[secondToLastBackslashIndex +
                               1:lastBackslashIndex]
        tagThreshold = configData["tags_count_ignored_threshold"]
        tagsToRemove = []
        alreadyClearedTags = []

        supportedAPIProviders = ["gelbooru", "danbooru"]
        if APIProvider in supportedAPIProviders:
            if APIProvider not in tagsDB:
                tagsDB[APIProvider] = {}
        # rule34.xxx isn't supported because their API straight up sucks dick

        tagsUpdated = 0
        currentDirTagsDict = {}
        for filename in os.listdir(imageDir):
            tagsPath = os.path.join(imageDir, filename)
            if os.path.isfile(tagsPath) and ".txt" in tagsPath:
                tagsFile = open(tagsPath, mode="r", encoding="utf-8")
                tagLines = tagsFile.readlines()

                tagsFile.seek(0)
                tagsContent = tagsFile.read()
                alreadyConverted = len(tagLines) == 1
                if alreadyConverted:
                    tagsList = tagsContent.split(",")
                else:
                    tagsList = tagLines

                for tag in tagsList:
                    strippedTag = tag.strip()
                    # Convert the tag back to the aa_bb_(cc) format if it was converted
                    if alreadyConverted and "_" not in tagsContent:
                        strippedTag = re.sub(r"([^,]) ", r"\1_", strippedTag)
                        strippedTag = strippedTag.replace("\\(", "(")
                        strippedTag = strippedTag.replace("\\)", ")")
                    strippedTag = fixEncoding(strippedTag)
                    if strippedTag in currentDirTagsDict:
                        currentDirTagsDict[strippedTag] += 1
                    else:
                        currentDirTagsDict[strippedTag] = 1

                    # Only do this if the API provider is supported AND the tag hasn't been checked yet.
                    if APIProvider in supportedAPIProviders and \
                            strippedTag not in tagsToRemove and \
                            strippedTag not in alreadyClearedTags and \
                            tagThreshold > -1 and "gelbooru_" not in strippedTag:
                        print("Filtering out low imagecount tags...")
                        tagsProviderDB = tagsDB[APIProvider]
                        print(strippedTag)
                        if strippedTag not in tagsProviderDB:
                            print("Tag " + strippedTag +
                                  " data missing, updating...")
                            try:
                                tagsProviderDB[strippedTag] = requestTagData(
                                    APIProvider, strippedTag)
                                tagsUpdated += 1
                            except Exception as e:
                                print(e)
                        else:
                            tagDataAge = date.fromisoformat(
                                tagsProviderDB[strippedTag]["lastUpdate"])
                            if (date.today() - tagDataAge).days > configData["tag_data_expiration_days"] != -1:
                                print("Tag " + strippedTag +
                                      " data older than set number of days, updating...")
                                tagsProviderDB[strippedTag] = requestTagData(
                                    APIProvider, strippedTag)
                                tagsUpdated += 1
                        # Every 30 new/updated tags, write to file to save progress.
                        if tagsUpdated >= 30:
                            json.dump(tagsDB, open(
                                tagDatabasePath, mode="w", encoding="utf-8"), indent=4)
                            tagsUpdated = 0
                        # Now we have the tag data updated within the last 7 days
                        # Let's check if the count is below the threshold
                        # If either one of those is true, add it to the tags that need to be nuked.
                        if strippedTag in tagsProviderDB:
                            tagData = tagsProviderDB[strippedTag]
                            if (tagData["count"] < tagThreshold and tagData["type"] != "character") or tagData["type"] == "copyright" or tagData["type"] == "deprecated":  # Remove it
                                tagsToRemove.append(strippedTag)
                            else:  # Mark it as already processed.
                                alreadyClearedTags.append(strippedTag)

                if not alreadyConverted:  # Not converted yet
                    if convertTagsToDDBFormat:
                        tagsContent = tagsContent.replace("_", " ")
                        tagsContent = re.sub(
                            r"([^\\])\(", r"\1\(", tagsContent)
                        tagsContent = re.sub(
                            r"([^\\])\)", r"\1\)", tagsContent)
                    tagsContent = tagsContent.replace("\n", ", ")
                    tagsContent = tagsContent.replace("\r", "")
                    tagsContent = fixEncoding(tagsContent)
                    if tagsContent[len(tagsContent) - 2] == ",":
                        tagsContent = tagsContent[:len(tagsContent) - 2]
                    tagsFile.close()

                    # We need to modify the path to the format used by fucking sd by removing the image extension
                    imagePath = tagsPath.replace(".txt", "")
                    if os.path.isfile(imagePath):
                        os.remove(tagsPath)  # Remove the old filepath
                        # The image actually exists, so this tag filename wasn't properly fixed.
                        imageExtension = imagePath[imagePath.rindex("."):]
                        tagsPath = tagsPath.replace(imageExtension, "")
                        tagsFile = open(tagsPath, mode="w", encoding="utf-8")
                        tagsFile.write(tagsContent)
                        tagsFile.close()

        # This section of code shows the user the X tags most commonly present in the data
        for tag in tagsToRemove:  # Remove tags that area already set to be deleted from the dict
            if tag in currentDirTagsDict:  # Make sure it's actually in the dict
                currentDirTagsDict.pop(tag)

        sortedListOfTuples = sorted(
            currentDirTagsDict.items(), key=lambda x: x[1], reverse=True)

        json.dump(tagsDB, open(tagDatabasePath, mode="w", encoding="utf-8"), indent=4)
        index = 0
        numOfTopTags = 30
        for item in sortedListOfTuples:
            print(str(index) + ": " +
                  str(item[0]) + " found " + str(item[1]) + " times in files.")
            index += 1
            if index >= numOfTopTags:
                break

        if askYesNo("Is there a tag you would like to remove from all files? (Recommended for tags that might pollute the dataset)"):
            tagIndexesToRemove = []
            numOfTagsToRemove = 0
            repeat = True
            while repeat:
                tagIndexesToRemove.append(-1)
                while not (0 <= tagIndexesToRemove[numOfTagsToRemove] < numOfTopTags):
                    try:
                        newIndex = int(input(
                            "Please input the number of the tag you'd like to remove from all files.\n"))
                        if newIndex not in tagIndexesToRemove:
                            tagIndexesToRemove[numOfTagsToRemove] = newIndex
                        else:
                            print("Value already previously selected.")
                    except:
                        print("Not a valid number.")
                numOfTagsToRemove += 1
                repeat = askYesNo("Would you like to remove another tag?")

            for tagIndex in tagIndexesToRemove:
                tagsToRemove.append(sortedListOfTuples[tagIndex][0])

        if len(tagsToRemove) > 0:  # Remove tags if we have any to remove.
            for filename in os.listdir(imageDir):
                tagsPath = os.path.join(imageDir, filename)
                if os.path.isfile(tagsPath) and ".txt" in tagsPath:
                    tagsFile = open(tagsPath, mode="r", encoding="utf-8")
                    tagsContent = tagsFile.read()
                    for tagToRemove in tagsToRemove:
                        tagsContent = re.sub(
                            r"(^| )" + tagToRemove.replace("\\", "\\\\") + "($|,)", "", tagsContent)
                    tagsFile.close()

                    tagsFile = open(tagsPath, mode="w", encoding="utf-8")
                    tagsFile.write(tagsContent)
                    tagsFile.close()

        print("The directory containing your images is")
        print(imageDir)
        subprocess.Popen('explorer \"'+imageDir+'\"')
    input("Press enter to exit...")
    exit(0)


def fixEncoding(text):
    return text.replace("&gt;", ">")\
        .replace("&lt;", "<")\
        .replace("&#039;", "'")\
        .replace("&amp;", "&")


if __name__ == "__main__":
    main()
