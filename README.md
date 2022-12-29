This repo contains all the embeddings I've made, in additon to a python script that's a gallery-dl/czkawka-cli wrapper meant to make training more streamlined.

# Okay but how do I use existing embeddings?

Step 1
------ 
Have a working [webUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) install that's up to date and with the model the embeddings were trained on.

I would HIGHLY recommend installing the "Autocomplete tags" extension. You can find it under the "Extensions" tab in the webUI.

For my embeddings, all of them were trained on the leaked novelAI model. You should [FOLLOW THIS GUIDE CAREFULLY](https://rentry.co/nai-speedrun) to set it up. 

Note: The guide DOES NOT INCLUDE the required files themselves. I cannot link to them, as it is a leak. Google is your friend. 

Step 2
------
Download the embedding(s) you'd like by navigating to them and clicking "Download".

![download](https://user-images.githubusercontent.com/21088033/209887795-3e3010c1-c60d-43f4-876f-d1ebc6d432f8.png)

Put them in the "embeddings" folder of your installation. Note: they need to be in the embeddings folder. You cannot put them inside subfolders.

Step 3
------
Generate the images you'd like! For more general info on how to make good prompts, check the [sd resource goldmine](https://rentry.org/sdupdates) and the [webui wiki](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Features).

Personally, my negative prompt is:
```
lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name, disfigured, deformed, malformed, mutant, monstrous, ugly, gross, disgusting, old, fat, obese, out of frame, poorly drawn, extra limbs, extra fingers, missing limbs, bokeh, depth of field
```

and my prompts always start with `masterpiece, best quality`. To use the embedding you just need to add its filename like any other tag. **WORKS BEST BY FAR IF THE EMBEDDING IS THE VERY LAST TAG**

Simple example of a paizuri using the Granberia embedding: `masterpiece, best quality, paizuri, granberia`

Additional tags to help bitchy embeddings
------
Some of the embeddings are not very cooperative. This can be due to confusion in the training data (The Alice one, for example, has both a human form and a lamia form). You can use some additonal tags to help steer it in the right direction. 

Known bitchy embeddings and tags that help:

- Granberia: scales, solo (if you want to just generate her) or 1girl (if you want to generate her and male characters). 

The second tag is needed because the embed tends to create some other mystery character for no reason. 
- Erubetie: slime girl, blue hair, blue skin
- Alice: lamia, either in the positive or negative prompt depending on which form you'd like.
- Ilias: White dress, angel wings

How to improve your generations
------

## Video version

[Click to play](https://u.teknik.io/h7adP.mp4)

## Text version

- Generate images with your prompt until you find something that's close to what you want. Edit the batch size/batch count to let it generate a bunch of images. 

Batch size is how many images it can do at once, whereas batch count is how many batches it will do. The former is restricted by your VRAM, the latter isn't.

Feel free to play around with the tags in the next two stages, it might help get you closer to what you want.

- Use the "send to img2img" button and generate a bunch of images derived from the first one until you find one that's perfect (or only has a couple sections that are fucked).
- If the image still has issues, use the "send to inpaint" button. You'll want to paint over the bits you'd like the AI to redo, and let it do its thing over and over until it gives you a good result. You can change the mask blur to make the edge of the mask less blurry.

Making manual edits
------
## Video version

[Click to play](https://u.teknik.io/EOGHR.mp4)

## Text version

If you'd like something specific that the AI isn't giving you, you can very easily modify the image using something like photoshop, then feed it back to the AI with either img2img or inpainting. In the video I show this by modifying the chest size.





# Dummy's guide to training (anime) embeddings from A to Z

**WARNING: YOU'LL NEED AN NVIDIA GPU WITH AT LEAST 8GB OF VRAM**

Video example
------
[Click to play](https://u.teknik.io/dfBqC.mp4)

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
