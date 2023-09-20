This repo contains a python script that's a gallery-dl/czkawka-cli wrapper meant to make training more streamlined.
# Dummy's guide to training (anime) embeddings from A to Z

**WARNING: YOU'LL NEED AN NVIDIA GPU WITH AT LEAST 8GB OF VRAM**

Step 0
------ 
Have a working [webUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) install that's up to date and with the model you'd like to use.

Personally I use the novelAI one. Follow [this guide](https://rentry.co/nai-speedrun) to set it up if you haven't already.

**FOR THE LOVE OF GOD TURN OFF VAE WEIGHTS DURING TRAINING**

Step Anime
------
Optional, only recommended if you're training anime-styled stuff (tested on the novelAI model)

Create a second install, which will be used exclusively for training. Roll it back to some commit before [this pull request](https://github.com/AUTOMATIC1111/stable-diffusion-webui/pull/4886) was merged by doing `git reset --hard commitID`. 

Personally I use commit 3e15f8e for training anime. This is because in my experience the change made in the pull request actually made it worse for anime specifically.

**THIS INSTANCE SHOULD NOT HAVE ANY VAE WEIGHTS (so you don't forget to turn them off), BUT IT SHOULD STILL HAVE THE MODELS YOU'D LIKE TO USE!**



Step 1
------
Download the zip via the green code button > download zip, extract it and place imageFetcherWrapper.py and run.bat and place them in some directory. Run run.bat once to generate the config file.

Sidenote: The reason why you need to use the batch file is due to the inconsistent way in which Windows handles setting the working directory with python scripts. See [here](https://bugs.python.org/issue26866) for the technical details.


Step 2
------
Download [czkawka-cli](https://github.com/qarmin/czkawka/releases/latest) and [gallery-dl](https://github.com/mikf/gallery-dl/releases/latest).

Either put them in the same directory where you put the python script, or edit the config file so the paths point to them. By default it will also download images in that same folder.




Step 3
------ 
Just run it and follow the prompts. The program will ask you if you would like to download images from a URL (or multiple) or process ones you have already downloaded.

If you're going to download them the program will also ask if you'd like to set a maximum amount of images to download. This is good for cases where there are a lot more images for your search than you need (but generally the more the merrier). In addition to this, it will also ask you if you would like to only keep the X most upvoted images.

The script will then download the images (if needed), automatically use czkawka to remove duplicates and convert the tags into the format used by the webUI. Once that's finished, it will open the resulting folder in windows explorer. 

You will also notice that there's a subfolder called "backup". That contains the downloaded images before any processing took place.




Step 4
------
Start up the webUI (either your normal one or the training-specific one you set up in step 0) and under "Training" go to "Create embedding". Give it a name and a vector size - I've found 20-24ish works well. 

Next go to "Preprocess Images", input the folder that was opened by the script, and set the destination folder to whatever you want. My recommended settings here are "Use BLIP for captioning" and "Ignore" for existing tag files. 

**If you have less than 100-ish images, also check "Mirror images".**

Step 5
------

Go to Train, select your embedding and let it run. I would recommend setting max steps to something sane like 12000, so it stops at a good time.
You will find the resulting embeddings in the "embeddings" folder. 

**If you're using a separate instance for training, copy them to the one you use to generate images.**
