import os, io, glob, logging
from PIL import Image, ImageOps, ImageDraw, ImageFont
import numpy as np
from numpy.random import default_rng
import qoi
from headpatExceptions import WaifuDNEError

POLL_FOLDER=os.path.join('img','waifu')
HEADPAT_FOLDER=os.path.join('img','headpat')
rng = default_rng()
font = ImageFont.truetype(os.path.join('data','Cotham',"CothamSans.otf"), size=20)
logger=logging.getLogger(os.environ['LOGGER_NAME'])

def imageToBytes(image:Image.Image) -> io.BytesIO:
    """
    Converts a PIL image into a discord-sendable bytes format

    Parameters
    ---
    image: :class:`PIL.Image.Image`
        The image to convert for sending

    Returns
    ---
    :class:`io.BytesIO`:
        a bytestream that can be sent as a discord attachment
    """
    bytes= io.BytesIO()
    image.save(bytes, format="PNG")
    bytes.seek(0)
    return bytes

def bytesToArray(data:io.BytesIO):
    image = Image.open(data)
    array = np.array(image)
    return array

def arrayToBytes(array):
    image=Image.fromarray(array)
    return imageToBytes(image)

def sourceNameFolder(name:str,source:str) -> str:
    return os.path.join(source,name)

def saveHeadpatImage(data:io.BytesIO) -> None:
    """
    Saves an image to the filesystem

    Parameters
    ---
    data: `filelike`
        bytestream image
    """
    image = Image.open(data)
    array = np.array(image)
    path = os.path.join(HEADPAT_FOLDER,f'{image.__hash__}.qoi')
    qoi.write(path,array)

def loadHeadpatImage() -> Image.Image:
    """
    Loads a random headpat from the filesystem

    Returns
    ---
    :class:`PIL.Image.Image`:
        an image of the headpat
    """
    logger.debug('loading headpat')
    pattern = os.path.join(HEADPAT_FOLDER,'*.qoi')
    matches = glob.glob(pattern)
    filePath = rng.choice(matches)
    imageArray=qoi.read(filePath)
    image = Image.fromarray(imageArray)
    return image

def savePollImage(data:io.BytesIO, filename:str, subfolder:str) -> bool:
    """
    Saves a waifu image to the filesystem, creating any necessary directories
    
    Parameters
    ---
    data: `filelike`
        the image to save
    filename: `str`
        name of the output file
    subfolder: `str`
        where to save the file. Reccomended to use `sourceNameFolder()` to generate

    Returns
    ---
    `bool`
        `True` if the subfolder alread existed  
        `False` if the subfolder did not previously exist
    """
    image = Image.open(data)
    array = np.array(image)
    return saveRawPollImage(array,filename,subfolder)

def saveRawPollImage(array,filename:str,subfolder:str) -> bool:
    """
    Saves a waifu image to the filesystem, creating any necessary directories
    
    Parameters
    ---
    array: `arraylike`
        the image to save, as an nxnx3 rgb value array
    filename: `str`
        name of the output file
    subfolder: `str`
        where to save the file. Reccomended to use `sourceNameFolder()` to generate

    Returns
    ---
    `bool`
        `True` if the subfolder alread existed  
        `False` if the subfolder did not previously exist
    """
    logger.debug('saving ' + filename + ' for ' + subfolder)
    prevExist = True
    folder=os.path.join(POLL_FOLDER,subfolder)
    if not os.path.exists(folder):
        prevExist=False
        os.makedirs(folder)
    path = os.path.join(folder,f'{filename}.qoi')
    qoi.write(path,array)
    return prevExist

def removePollImage(filename:str,subfolder:str):
    """
    removes a waifu image from the filesystem, deleting the whole directory if there are no images left

    Parameters
    ---
    filename: `str`
        name of the file to remove
    subfolder: `str`
        folder to look in and delete if necessary
    
    Returns
    ---
    `bool`
        `True` if the entire directory was removed  
        `False` otherwise
    """
    logger.debug('removing ' + filename + ' for ' + subfolder)
    lastOne=False
    folder = os.path.join(POLL_FOLDER,subfolder)
    rmFile = os.path.join(folder,f'{filename}.qoi')
    if os.path.exists(rmFile):
        os.remove(rmFile)
    else:
        raise WaifuDNEError
    pattern = os.path.join(folder,'*.qoi')
    matches = glob.glob(pattern)
    if not matches and os.path.exists(folder): #no waifus left, but folder *does* exist
        lastOne = True
        os.removedirs(folder)
    return lastOne

def loadPollImage(subfolder:str) -> Image.Image:
    """
    Loads a waifu image from the filesystem, randomly selecting within a defined range
    
    Parameters
    ---
    subfolder: `str`
        where the file to load is. Reccomended to use `sourceNameFolder()` to generate

    Returns
    ---
    :class:`PIL.Image.Image`
    """

    logger.debug('loading '+ subfolder + ' poll image')
    folder = os.path.join(POLL_FOLDER,subfolder)
    pattern = os.path.join(folder,'*.qoi')
    matches = glob.glob(pattern)
    if not matches:
        raise WaifuDNEError
    logger.debug(f'{pattern}\n matched by\n{matches}')
    filePath = rng.choice(matches)
    imageArray=qoi.read(filePath)
    image = Image.fromarray(imageArray)
    return image

def makeTile(image:Image.Image,width:int=500,height:int=500) -> Image.Image:
    """
    Turn an image into a tile, for use in poll collages

    Parameters
    ---
    image: :class:`PIL.Image.Image`
        the image to reshape and size
    width: `int`
        final image width in pixels  
        default: 500
    height: `int`
        final image height in pixels  
        default: 500

    Returns
    ---
    :class:`PIL.Image.Image`
        a final tile-sized image
    """
    #TODO: See if cropping then resizing is easier.
    inSize=image.size
    aspectDesired=width/height
    aspectCurrent=inSize[0]/inSize[1]
    if aspectCurrent >= aspectDesired: #image is wider than desired
        scale = height/inSize[1] #determine scale by height
        newWidth=int(scale*inSize[0]) #find new width to avoid stretching
        newHeight=height #the height we need
    else: #taller than desired
        scale=width/inSize[0]
        newWidth=width
        newHeight=int(scale*inSize[1])
    #grab the top middle (more likely to have face)
    left=(newWidth-width)/2
    top=0 
    image=image.resize((newWidth,newHeight)) #resize the image
    box=(left,top,left+width,top+width) #TODO: set box to contain a found face
    return image.crop(box)


def addBorder(image:Image.Image,thickness:int=20,fill=(255,255,255)) -> Image.Image:
    """
    Adds a single color border around an image by expanding the image

    Parameters
    ---
    image: :class:`PIL.Image.Image`
        image to modify
    thickness: `int`
        how much to add to each side  
        default: 20
    fill: `tuple(int,int,int)`
        RGB color to make border  
        default: (255,255,255) (white)

    Returns
    ---
    :class:`PIL.Image.Image`
        modified image
    """
    return ImageOps.expand(image,thickness,fill)

def caption(image:Image.Image,text:str) -> Image.Image:
    """
    add lines of text to the bottom of an image

    Parameters
    ---
    image: :class:`PIL.Image.Image`
        the image to caption
    text: `str`
        the text to write

    Returns
    ---
    :class:`PIL.Image.Image`
        Captioned image
    """
    image=image.copy()
    draw=ImageDraw.Draw(image) #create a canvas
    imageSize=image.size
    textbbox=draw.multiline_textbbox((imageSize[0]/2,imageSize[1]),text,font=font,anchor='md',align='center') #determine the size of the text needed
    #print(textbbox)
    draw.rectangle((0,textbbox[1],imageSize[0],imageSize[1]),fill=(0,0,0),outline=(128,128,128)) #add a black backing rectangle
    draw.multiline_text((imageSize[0]/2,imageSize[1]),text,anchor='md',align='center',fill=(255,255,255),font=font) #Fill the text over the rectangle
    return image

def collage(images:list[Image.Image],width:int=4) -> Image.Image:
    """
    Combine multiple images together into a large collage with `width` columns and `ceil(len(images)/width)` rows.
    If there are insufficient images to fill the last row, the remainder are centered

    Parameters
    ---
    images: List[:class:`PIL.Image.Image`]
        list of images to combine
    width: `int`
        number of images to place horizontally adjacent  
        default: 4
    
    Returns:
    :class:`PIL.Image.Image`
        Input images combined into one larger image

    """
    count = len(images) #number of images we have to deal with
    tileSize=images[0].size
    height = int(np.ceil(count/width)) #determine the number of rows to make
    finalSize=(tileSize[0]*width,tileSize[1]*height)
    collage=Image.new('RGB',finalSize)
    #print(finalSize)
    i=0;
    for y in range(height-1): #fill all but the last row
        for x in range(width):
            left=tileSize[0]*x
            top=tileSize[1]*y
            collage.paste(images[i],(left,top))
            i+=1 #next image
    remainder=count-i #figure out how many images are left to place
    for x in range(remainder): #last row may have fewer
        offset=int((finalSize[0]-remainder*tileSize[0])/2)#skip over to the side a bit to center the images
        left=tileSize[0]*x+offset
        top=tileSize[1]*(height-1)
        collage.paste(images[i],(left,top))
        i+=1
    return collage

def createPollImage(names:list[str],sources:list[str]) -> Image.Image:
    """
    Creates a postable waifupoll image from the namse and sources of waifus

    Parameters
    ---
    names: list[`str`]
        list of all the waifus to include, in order
    sources: list[`str`]
        list of the sources for each waifu, in order  
        `sources[i]` must be the source for `names[i]`
    
    Returns
    ---
    :class:`PIL.Image.Image`
        completed waifu poll image
    """
    assert(len(names)==len(sources))
    images=list[Image.Image]()
    for i in range(len(names)):
        filepath=sourceNameFolder(names[i],sources[i])
        image=loadPollImage(filepath) #get the image
        image=makeTile(image) #resize it
        image=caption(image,f'{names[i]}\n{sources[i]}') #add the name
        image=addBorder(image) #create a border
        images.append(image) #put it in the list
    return collage(images) #create the poll image