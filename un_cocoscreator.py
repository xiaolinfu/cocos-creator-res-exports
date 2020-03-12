#!/usr/bin/env python  
# coding=utf-8  
# Python 2.7.3  
import os
import sys
import argparse
import json,shutil


from PIL import Image

pvr_file_ext = (".pvr", ".pvr.gz", ".pvr.ccz")
support_file_ext = (".png", ".jpg", ) + pvr_file_ext

BASE64_KEYS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
BASE64_VALUES = [0 for _ in range(123)]
for i in range(123): 
    BASE64_VALUES[i] = 64
for i in range(64):
    # print(i,ord(BASE64_KEYS[i]))
    BASE64_VALUES[ord(BASE64_KEYS[i])] = i

HexChars = '0,1,2,3,4,5,6,7,8,9,a,b,c,d,e,f'.split(',')

UuidTemplate = ['' for i in range(36)]
UuidTemplate[8] = UuidTemplate[13] = UuidTemplate[18] = UuidTemplate[23] = '-'
Indices = [i for i in range(36)]
Indices.remove(8)
Indices.remove(13)
Indices.remove(18)
Indices.remove(23)
# print(UuidTemplate)
# print(Indices)
# print(BASE64_VALUES)

def decodeuuid(base64):
    UuidTemplate[0] = base64[0];
    UuidTemplate[1] = base64[1];
    j = 2
    for i in range(2,22,2):
        lhs = BASE64_VALUES[ord(base64[i])];
        rhs = BASE64_VALUES[ord(base64[i+1])];
        UuidTemplate[Indices[j]] = HexChars[lhs >> 2];
        j += 1
        UuidTemplate[Indices[j]] = HexChars[((lhs & 3) << 2) | rhs >> 4];
        j += 1
        UuidTemplate[Indices[j]] = HexChars[rhs & 0xF];
        j += 1
    return ''.join(UuidTemplate);

# print(decodeuuid('fcmR3XADNLgJ1ByKhqcC5Z'))

def parseRes(path):
    for name in os.listdir(path):
        full_name = os.path.join(path, name)
        pre,ext = os.path.splitext(name)
        # print(pre,ext)
        # print(full_name)
        if os.path.isdir(full_name):
            # print(full_name)
            parseRes(full_name)
        elif ext == ".atlas":
            # print(full_name)
            spineAtlas.append(full_name)
        elif ext == ".mp3":
            audios.append(full_name)
        elif ext == ".json":
            data =  {}
            with open(full_name, "r") as f:
                data = json.loads(f.read())
            if '__type__' in data and data['__type__'] == "cc.SpriteFrame":
                # print(data)
                texture = data['content']['texture']
                if texture not in texture2framesmap:
                    texture2framesmap[texture] = []
                texture2framesmap[texture].append(data['content'])
                name2texture[data['content']['name']] = texture
            elif '__type__' in data and data['__type__'] == "cc.SpriteAtlas":
                altas.append(data)
            elif '__type__' in data and data['__type__'] == "sp.SkeletonData":
                spines.append(data)
            elif 'skeleton' in data:
                spineHash2jsonpath[data['skeleton']['hash']] = full_name
            # elif '__type__' in data and data['__type__'] == "cc.Asset":
            # 	print(data)
            elif '__type__' in data and data['__type__'] == "cc.JsonAsset":
                # print(data)
                name2json[data['_name']] = data['json']
                # audioName2path[data['_name']] = data
            # elif '__type__' in data:
            #     print(data['__type__'])
            # else:
            #     print()
            #     return
        elif ext == ".png":
            # print(full_name)
            # try:
                src_image = Image.open(full_name)
                key = str(src_image.width) + "." + str(src_image.height)
                # print(key,full_name)
                if key not in pngWH2path:
                    pngWH2path[key] = []
                pngWH2path[key].append(full_name)
                paths = os.path.basename(full_name).split('.')
                pngurl2md5path[paths[0]] = full_name
                
                # else:
                #     print("key exists",key,full_name,pngWH2path[key])
                # print(src_image.width,src_image.height)
            # except Exception:
            #     print("fail: can't open image %s " %full_name)
            #     return -1
        else:
            print("ext ",ext)
       
def calcSpriteAltas(texture2framesmap):
    for key in texture2framesmap:
        # print("_",decodeuuid(key))
        # width = 0
        # height = 0
        # if len(maps[key]) == 1:
        #     originalSize = maps[key][0]['originalSize']
        #     width = originalSize[0]
        #     height = originalSize[1]
        # else:
        #     for frame in maps[key]:
        #         # print(frame)
        #         rect = frame['rect']
        #         originalSize = frame['originalSize']
        #         # print(rect)
        #         if width < rect[0] + rect[2]:
        #             width = rect[0] + rect[2]
        #         if height < rect[0+1] + rect[2+1]:
        #             height = rect[0+1] + rect[2+1]
        #     width += 2
        #     height += 2
        # keywd = str(width) + "." + str(height)
        keywd = pngurl2md5path[decodeuuid(key)]
        plistUrl2frames[keywd] = texture2framesmap[key]
        # if keywd:
        #     print("OK",keywd,key)
        # else:
        #     print("Not find Pngs",keywd,key)
def splitPng(frames,image_file,output_dir):
    # print(len(frames),image_file)
    try:
        src_image = Image.open(image_file)
    except Exception:
        print("fail: can't open image %s " %image_file)
        return -1
   
    for frame_data in frames:
        rect = frame_data['rect']
        offset = frame_data['offset']
        originalSize = frame_data['originalSize']
        if src_image.width == originalSize[0] and src_image.height == originalSize[1]:
            # print("大图",image_file)
            continue
        src_rect = (rect[0],rect[1],rect[0]+rect[2],rect[1] + rect[3])
        source_size = (originalSize[0],originalSize[1])
        source_offset = (int(offset[0]),int(offset[1]))
        # print(offset)
        temp_image = src_image.crop(src_rect)
        # if frame_data["rotated"]:
        #     temp_image = temp_image.rotate(90, expand=1)

        # create dst image
        mode = "RGBA" if (src_image.mode in ('RGBA', 'LA') or (src_image.mode == 'P' and 'transparency' in src_image.info)) else "RGB"
        dst_image = Image.new(mode, source_size, (0,0,0,0))
        dst_image.paste(temp_image, source_offset, mask=0)

        output_path = os.path.join(output_dir, frame_data["name"])
        pre,ext = os.path.splitext(output_path)
        if not ext:
            output_path = output_path + ".png"
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        dst_image.save(output_path)

def expotImags():
    for pngpath in plistUrl2frames:
        splitPng(plistUrl2frames[pngpath],pngpath,"./out/textures")
        paths = os.path.basename(pngpath).split('.')
        if paths[0] in pngurl2md5path:
        	del pngurl2md5path[paths[0]]
        else:
        	print('key error',pngpath)

    # pngKeys = pngWH2path.keys()
    # pngKeys.sort(key=lambda elem :int(elem.split('.')[0]))
    # for key in pngKeys:
    #     print(key,pngWH2path[key])
    #     if key not in plistUrl2frames or len(plistUrl2frames[key]) == 1 :
    #         dest = "./out/texturesBig/" + os.path.basename(pngWH2path[key][0])
    #         # print(key)
    #         if not os.path.exists(os.path.dirname(dest)):
    #             os.makedirs(os.path.dirname(dest))
    #         if len(pngWH2path[key]) == 1:
    #             shutil.copyfile(pngWH2path[key][0],dest)
    #         else:
    #             for i in range(len(pngWH2path[key])):
    #                 shutil.copyfile(pngWH2path[key][i],dest.replace(".png","_" +str(i) + ".png"))
    #         continue
    #     if len(pngWH2path[key]) == 1:
    #         splitPng(plistUrl2frames[key],pngWH2path[key][0],"./out/textures")
    #     else:
    #         for i in range(len(pngWH2path[key])):
    #             splitPng(plistUrl2frames[key],pngWH2path[key][i],"./out/textures/" + os.path.basename(pngWH2path[key][i]).split('.')[0] + str(i))
def exportAudio():
    for audiofile in audios:
        dest = "./out/sounds/" + os.path.basename(audiofile)
        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        shutil.copyfile(audiofile,dest )
def exportSpine():
    # .atlas
    for atlasPath in spineAtlas:
        # print(atlasPath)
        f = open(atlasPath)
        f.readline()
        filename = f.readline().replace('\n','').split('.')[0]
        dest = "./out/spines/" + filename + "/" + filename + ".atlas"
        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        shutil.copyfile(atlasPath,dest )

        # if filename in name2texture and name2texture[filename] in texture2framesmap:
        #     frames = texture2framesmap[name2texture[filename]]
        #     if len(frames) == 1:
        #          key = str(frames[0]['originalSize'][0]) + "." + str(frames[0]['originalSize'][1])
        #          if key in pngWH2path:
        #             print("spine==",filename,key,pngWH2path[key])
        #             dest = dest = "./out/spines/" + filename + "/" + filename + ".png"
        #             if len(pngWH2path[key]) == 1:
        #                 shutil.copyfile(pngWH2path[key][0],dest)
        #             else:
        #                 for i in range(len(pngWH2path[key])):
        #                     shutil.copyfile(pngWH2path[key][i],dest.replace(".png","_" +str(i) + ".png"))
    # .png .json
    for skdata in spines:
        filename = skdata['_name']
        # png
        pnguuid = decodeuuid(skdata['textures'][0]["__uuid__"])
        dest = dest = "./out/spines/" + filename + "/" + filename + ".png"
        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        if pnguuid in pngurl2md5path:
	        shutil.copyfile(pngurl2md5path[pnguuid],dest)
	        del plistUrl2frames[pngurl2md5path[pnguuid]]
	        del pngurl2md5path[pnguuid]
        else:
	        print('sk image error',filename,pnguuid)

        # json
        hashkey = skdata['_skeletonJson']['skeleton']['hash'] 
        dest = "./out/spines/" + filename + "/" + filename + ".json"
        shutil.copyfile(spineHash2jsonpath[hashkey],dest )
        # print ('skins' in skdata['_skeletonJson'])
        

        f = open(spineHash2jsonpath[hashkey])
        jsonobj = json.loads(f.read())
        f.close()
        skins = jsonobj['skins']
        for skinkey in skins:
            if skinkey[0] in [str(i) for i in range(0,10)]:
                # print(skinkey)
                jsonobj['skins']['s' + skinkey] = skins[skinkey]
                del jsonobj['skins'][skinkey] 
        
        f = open(dest,'w')
        f.write(json.dumps(jsonobj))
        f.close()
       
def exportJson():
	for filename in name2json:
		# print(json.dumps(name2json[filename]))
		dest = "./out/jsonconfig/" + filename + ".json"
		if not os.path.exists(os.path.dirname(dest)):
			os.makedirs(os.path.dirname(dest))
		f = open(dest,'w')
		f.write(json.dumps(name2json[filename]))
		f.close()
		# break





name2texture = {}

texture2framesmap = {}
altas = []
pngWH2path = {}
pngurl2md5path = {}
plistUrl2frames = {}
audios = []
spines = []
spineAtlas = []
spineHash2jsonpath = {}

name2json = {}

if __name__ == '__main__':
    parseRes("./res")
    print('')

    calcSpriteAltas(texture2framesmap)
    # # spine
    exportSpine()
    # 图片
    expotImags()
    # # 音乐
    exportAudio()

    # Json
    exportJson()

    
    

    

