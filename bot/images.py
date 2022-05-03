import os, io, glob
from PIL import Image, ImageOps, ImageDraw, ImageFont
import numpy as np
from numpy.random import default_rng
import qoi

POLL_FOLDER=os.path.join('img','waifu')
HEADPAT_FOLDER=os.path.join('img','headpat')
rng = default_rng()
font = ImageFont.truetype(os.path.join('data','Cotham',"CothamSans.otf"), size=20)

def imageToBytes(image:Image.Image,filename:str='image'):
    bytes= io.BytesIO()
    image.save(bytes, format="PNG")
    bytes.seek(0)
    return bytes

def sourceNameFolder(name:str,source:str):
    return os.path.join(source,name)

def saveHeadpatImage(data:io.BytesIO):
    image = Image.open(data)
    array = np.array(image)
    path = os.path.join(HEADPAT_FOLDER,f'{image.__hash__}.qoi')
    qoi.write(path,array)

def loadHeadpatImage():
    pattern = os.path.join(HEADPAT_FOLDER,'*.qoi')
    matches = glob.glob(pattern)
    filePath = rng.choice(matches)
    imageArray=qoi.read(filePath)
    image = Image.fromarray(imageArray)
    return image

def savePollImage(data:io.BytesIO, filename:str, subfolder:str):
    image = Image.open(data)
    array = np.array(image)
    return saveRawPollImage(array,filename,subfolder)

def saveRawPollImage(array,filename:str,subfolder:str):
    prevExist = True
    folder=os.path.join(POLL_FOLDER,subfolder)
    if not os.path.exists(folder):
        prevExist=False
        os.makedirs(folder)
    path = os.path.join(folder,f'{filename}.qoi')
    qoi.write(path,array)
    return prevExist


def loadPollImage(subfolder:str):
    folder = os.path.join(POLL_FOLDER,subfolder)
    pattern = os.path.join(folder,'*.qoi')
    matches = glob.glob(pattern)
    #print(f'{pattern}\n matched by\n{matches}')
    filePath = rng.choice(matches)
    imageArray=qoi.read(filePath)
    image = Image.fromarray(imageArray)
    return image

def makeTile(image:Image.Image,width:int=500,height:int=500):
    #TODO: assumes square in some math. Also, see if cropping then resizing is easier.
    inSize=image.size
    if inSize[0] >= inSize[1]: #wider than it is tall
        scale=height/inSize[1]
        newWidth=int(scale*inSize[0])
        newHeight=height
        #get the dead middle
        left=(newWidth-width)/2 
        top =(newHeight-height)/2 
    else: #taller than wide
        scale=width/inSize[0]
        newWidth=width
        newHeight=int(scale*inSize[1])
        #grab the top middle (more likely to have face)
        left=(newWidth-width)/2
        top =0 
    image=image.resize((newWidth,newHeight))
    
    box=(left,top,left+width,top+width)
    return image.crop(box)


def addBorder(image:Image.Image,thickness:int=20,fill=(255,255,255)):
    return ImageOps.expand(image,thickness,fill)

def caption(image:Image.Image,text:str):
    image=image.copy()
    draw=ImageDraw.Draw(image)
    imageSize=image.size
    textbbox=draw.multiline_textbbox((imageSize[0]/2,imageSize[1]),text,font=font,anchor='md',align='center')
    #print(textbbox)
    draw.rectangle((0,textbbox[1],imageSize[0],imageSize[1]),fill=(0,0,0),outline=(128,128,128))
    draw.multiline_text((imageSize[0]/2,imageSize[1]),text,anchor='md',align='center',fill=(255,255,255),font=font)
    return image

def collage(images:list[Image.Image],width:int=4):
    count = len(images)
    tileSize=images[0].size
    height = int(np.ceil(count/width))
    finalSize=(tileSize[0]*width,tileSize[1]*height)
    collage=Image.new('RGB',finalSize)
    #print(finalSize)
    i=0;
    for y in range(height-1):
        for x in range(width):
            left=tileSize[0]*x
            top=tileSize[1]*y
            #right=left+tileSize[0]
            #bot=top+tileSize[1]
            collage.paste(images[i],(left,top))
            i+=1
    remainder=count-i
    for x in range(remainder): #last row may have fewer
        left=tileSize[0]*x+int((finalSize[0]-remainder*tileSize[0])/2)
        top=tileSize[1]*(height-1)
        collage.paste(images[i],(left,top))
        i+=1
    return collage

def createPollImage(names:list[str],sources:list[str]):
    images=[]
    for i in range(len(names)):
        filepath=sourceNameFolder(names[i],sources[i])
        image=loadPollImage(filepath)
        image=makeTile(image)
        image=caption(image,f'{names[i]}\n{sources[i]}')
        image=addBorder(image)
        images.append(image)
    return collage(images)