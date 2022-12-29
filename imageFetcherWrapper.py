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
    while answerTemp.lower()[0] != "y" and answerTemp.lower()[0] != "n":
        print("Not a valid answer. \n")
        answerTemp = input("y/n\n")
    return answerTemp.lower()[0] == "y"

def main():
    #Change these parameters
    configFilePath = os.path.join(os.getcwd(),"config.json")
    if not os.path.exists(configFilePath):
        print("Error. Config file missing.\n")
        print(
            "I'm going to create the config file in this directory ASSUMING that you have gallery-dl and czkawka-cli in the same folder as this script "
            "and that you'd like the downloaded images to be here as well. If that is not the case, you can edit config.json later.\n")
        cwd = os.getcwd()

        defaultConfigData = {
            "czkawka_cli_path": os.path.join(cwd,"czkawka_cli.exe"),
            "gallery-dl_path": os.path.join(cwd,"gallery-dl.exe"),
            "root_download_folder": cwd,
            "backup_original_folder": True,
            "supress_tag_suggestions": False,
            "czkawka_similarity_preset": "Minimal",
            "czkawka_algorithm": "Lanczos3",
            "tags_to_warn_when_not_excluded": ["monochrome"]
        }
        json.dump(defaultConfigData, open(configFilePath, mode="w"), indent=4)

    configData = json.load(open(configFilePath))
    if not "czkawka_cli_path" in configData:
        print("Error. czkawka_cli_path missing from config file.")
        exit()
    czkawkaCLIPath = configData["czkawka_cli_path"]
    if not os.path.exists(czkawkaCLIPath):
        print("Error. Czkawka CLI path is not valid. You probably forgot to escape the backslashes (every \\ should be replaced by \\\\).")
        exit()

    if not "gallery-dl_path" in configData:
        print("Error. gallery-dl_path missing from config file.")
        exit()
    galleryDLPath = configData["gallery-dl_path"]
    if not os.path.exists(galleryDLPath):
        print("Error. gallery-dl_path is not valid. You probably forgot to escape the backslashes (every \\ should be replaced by \\\\).")
        exit()

    rootDownloadFolder = configData["root_download_folder"]
    if not os.path.exists(rootDownloadFolder):
        print("Error. root_download_folder is not valid. You probably forgot to escape the backslashes (every \\ should be replaced by \\\\).")
        exit()


    print("Do you want to:")
    print("1) Download images via gallery-dl and deduplicate them")
    print("2) Deduplicate images you've already downloaded within a directory")
    choice_num = -1
    while not (0 < choice_num < 3):
        try:
            choice_num = int(input("Please select which option you'd like and press enter.\n"))
        except:
            print("Not a valid number.")
    overrideDir = (choice_num == 2)

    imageDirs = []

    if overrideDir: #If the directory is overridden, simply run it on this directory
        runAgain = True
        while runAgain:
            print("Please input the directory you'd like to run the program on and press enter.")
            imageDir = input()
            while not os.path.exists(imageDir):
                imageDir = input("Specified image directory does not exist! Try again.")
            imageDirs.append(imageDir)
            runAgain = askYesNo("Would you like to queue another up directory?")
    else:
        print("Note: downloaded images are saved in "+rootDownloadFolder+"\\gallery-dl\\[sitename]\\[tags]")
        print("I'm going to assume that this is a valid link that gallery-dl can actually use.")
        runAgain = True
        downloadURLs = []
        while runAgain:
            newDownloadData = dict()
            newDownloadData["URL"] = input("Please input the URL and press enter.")

            if askYesNo("Would you like to download only a certain amount of images?"):
                range_max = -1
                while not (0 < range_max):
                    try:
                        range_max = int(input("How many images max would you like to download?.\n"))
                        newDownloadData["range_max"] = str(range_max)
                    except:
                        print("Not a valid number.")
            downloadURLs.append(newDownloadData)

            runAgain = askYesNo("Would you like to queue up another URL?")
        #Directory not overridden, run gallery-dl
        for downloadData in downloadURLs:
            downloadURL = downloadData["URL"]
            dlcommand = galleryDLPath +" \""+ downloadURL +"\""+ \
                          " --write-tags " + \
                          " --write-metadata " + \
                          " --exec-after \"echo {} > outputdir.txt\""
            if "range_max" in downloadData:
                dlcommand += " --range 1-" + downloadData["range_max"]
            print(dlcommand)
            subprocess.run(dlcommand,cwd=rootDownloadFolder)

            imageDirFile = open(os.path.join(rootDownloadFolder,"outputdir.txt"), mode="r")
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
            imageDirs.append(imageDir)

    for imageDir in imageDirs:
        similarityPreset = configData["czkawka_similarity_preset"] #Acceptable values: Minimal, VerySmall, Small, Medium, High, VeryHigh (minimal works best in my experience)
        algorithm = configData["czkawka_algorithm"] #Allowed: Lanczos3, Nearest, Triangle, Faussian, Catmullrom
        tagsToFilterOut = configData["tags_to_warn_when_not_excluded"]  # ["monochrome"]
        backupOriginalFolder = configData["backup_original_folder"]
        ignoreTagSuggestions = configData["supress_tag_suggestions"]

        if not ignoreTagSuggestions:
            missingTags = False
            for tag in tagsToFilterOut:
                if "-" + tag not in imageDir:
                    print("You forgot to filter out " + tag + " which is highly recommended for better results.")
                    missingTags = True
            if missingTags:
                if not askYesNo("Proceed anyway?"):
                    exit(1)

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
            shutil.copytree(imageDir,backupDir)
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
                        separator2Index = line.find(separator, separatorIndex + len(separator))
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
                                    print("Deleting associated tags file:" + tagsPath)
                                    os.remove(tagsPath)
                                metadataPath = image.path + ".json"
                                if os.path.exists(metadataPath):
                                    print("Deleting associated metadata file:" + metadataPath)
                                    os.remove(metadataPath)
                        print("Deleted copies (and associated tag files if they existed).")
            #Prep for the next loop
            os.remove(tempFile)

        #we're done removing duplicates
        if askYesNo("Would you like to keep only a certain number of the most upvoted images?"
            "(For example only the 100 most upvoted)"):
            scores = {}
            for filename in os.listdir(imageDir):
                metadataPath = os.path.join(imageDir, filename)
                if os.path.isfile(metadataPath) and ".json" in metadataPath:
                    metadata = json.load(open(metadataPath, mode="r"))
                    scores[metadataPath.replace(".json", "")] = metadata["score"]
            currentNumber = 0

            numOfImages = -1
            while not (0 < numOfImages):
                try:
                    numOfImages = int(input("Please input how many of the top images you'd like to keep.\n"))
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
        for filename in os.listdir(imageDir):
            tagsPath = os.path.join(imageDir, filename)
            if os.path.isfile(tagsPath) and ".txt" in tagsPath:
                tagsFile = open(tagsPath, mode="r")
                tagsContent = tagsFile.read()
                tagsContent = tagsContent.replace("_", " ")
                tagsContent = re.sub(r"([^\\])\(", r"\1\(", tagsContent)
                tagsContent = re.sub(r"([^\\])\)", r"\1\)", tagsContent)
                tagsContent = tagsContent.replace("\n", ", ")
                tagsContent = tagsContent.replace("\r", "")
                if tagsContent[len(tagsContent) - 2] == ",":
                    tagsContent = tagsContent[:len(tagsContent) - 2]
                tagsFile.close()

                #We need to modify the path to the format used by fucking sd by removing the image extension
                imagePath = tagsPath.replace(".txt","")
                if os.path.isfile(imagePath):
                    os.remove(tagsPath)  # Remove the old filepath
                    #The image actually exists, so this tag filename wasn't properly fixed.
                    imageExtension = imagePath[imagePath.rindex("."):]
                    tagsPath = tagsPath.replace(imageExtension,"")
                    tagsFile = open(tagsPath, mode="w")
                    tagsFile.write(tagsContent)
                    tagsFile.close()

        print("The directory containing your images is")
        print(imageDir)
        subprocess.Popen('explorer \"'+imageDir+'\"')
    input("Press enter to exit...")
    exit(0)






if __name__ == "__main__":
    main()
