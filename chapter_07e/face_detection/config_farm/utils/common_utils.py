#-*-coding:utf-8-*-
# date:2020-04-11
# Author: xiang li

import os
import shutil
import cv2
import numpy as np
import json

def mkdir_(path, flag_rm=False):
    if os.path.exists(path):
        if flag_rm == True:
            shutil.rmtree(path)
            os.mkdir(path)
            print('remove {} done ~ '.format(path))
    else:
        os.mkdir(path)

def plot_box(bbox, img, color=None, label=None, line_thickness=None):
    tl = line_thickness or round(0.002 * max(img.shape[0:2])) + 1
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl)# 目标的bbox
    if label:
        tf = max(tl - 2, 1)
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0] # label size
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3 # 字体的bbox
        cv2.rectangle(img, c1, c2, color, -1)  # label 矩形填充
        # 文本绘制
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 4, [225, 255, 255],thickness=tf, lineType=cv2.LINE_AA)

class JSON_Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(JSON_Encoder, self).default(obj)

def draw_landmarks(img,output,draw_circle):
    img_width = img.shape[1]
    img_height = img.shape[0]
    dict_landmarks = {}
    for i in range(int(output.shape[0]/2)):
        x = output[i*2+0]*float(img_width)
        y = output[i*2+1]*float(img_height)
        if 41>= i >=33:
            if 'left_eyebrow' not in dict_landmarks.keys():
                dict_landmarks['left_eyebrow'] = []
            dict_landmarks['left_eyebrow'].append([int(x),int(y),(0,255,0)])
            if draw_circle:
                cv2.circle(img, (int(x),int(y)), 2, (0,255,0),-1)
        elif 50>= i >=42:
            if 'right_eyebrow' not in dict_landmarks.keys():
                dict_landmarks['right_eyebrow'] = []
            dict_landmarks['right_eyebrow'].append([int(x),int(y),(0,255,0)])
            if draw_circle:
                cv2.circle(img, (int(x),int(y)), 2, (0,255,0),-1)
        elif 67>= i >=60:
            if 'left_eye' not in dict_landmarks.keys():
                dict_landmarks['left_eye'] = []
            dict_landmarks['left_eye'].append([int(x),int(y),(255,55,255)])
            if draw_circle:
                cv2.circle(img, (int(x),int(y)), 2, (255,0,255),-1)
        elif 75>= i >=68:
            if 'right_eye' not in dict_landmarks.keys():
                dict_landmarks['right_eye'] = []
            dict_landmarks['right_eye'].append([int(x),int(y),(255,55,255)])
            if draw_circle:
                cv2.circle(img, (int(x),int(y)), 2, (255,0,255),-1)
        elif 97>= i >=96:
            cv2.circle(img, (int(x),int(y)), 2, (0,0,255),-1)
        elif 54>= i >=51:
            if 'bridge_nose' not in dict_landmarks.keys():
                dict_landmarks['bridge_nose'] = []
            dict_landmarks['bridge_nose'].append([int(x),int(y),(0,170,255)])
            if draw_circle:
                cv2.circle(img, (int(x),int(y)), 2, (0,170,255),-1)
        elif 32>= i >=0:
            if 'basin' not in dict_landmarks.keys():
                dict_landmarks['basin'] = []
            dict_landmarks['basin'].append([int(x),int(y),(255,30,30)])
            if draw_circle:
                cv2.circle(img, (int(x),int(y)), 2, (255,30,30),-1)
        elif 59>= i >=55:
            if 'wing_nose' not in dict_landmarks.keys():
                dict_landmarks['wing_nose'] = []
            dict_landmarks['wing_nose'].append([int(x),int(y),(0,255,255)])
            if draw_circle:
                cv2.circle(img, (int(x),int(y)), 2, (0,255,255),-1)
        elif 87>= i >=76:
            if 'out_lip' not in dict_landmarks.keys():
                dict_landmarks['out_lip'] = []
            dict_landmarks['out_lip'].append([int(x),int(y),(255,255,0)])
            if draw_circle:
                cv2.circle(img, (int(x),int(y)), 2, (255,255,0),-1)
        elif 95>= i >=88:
            if 'in_lip' not in dict_landmarks.keys():
                dict_landmarks['in_lip'] = []
            dict_landmarks['in_lip'].append([int(x),int(y),(50,220,255)])
            if draw_circle:
                cv2.circle(img, (int(x),int(y)), 2, (50,220,255),-1)
        else:
            if draw_circle:
                cv2.circle(img, (int(x),int(y)), 2, (255,0,255),-1)

    return dict_landmarks

def draw_contour(image,dict,r_bbox):
    x0 = r_bbox[0]# 全图偏置
    y0 = r_bbox[1]

    for key in dict.keys():
        # print(key)
        _,_,color = dict[key][0]

        if 'left_eye' == key:
            eye_x = np.mean([dict[key][i][0]+x0 for i in range(len(dict[key]))])
            eye_y = np.mean([dict[key][i][1]+y0 for i in range(len(dict[key]))])
            cv2.circle(image, (int(eye_x),int(eye_y)), 3, (255,255,55),-1)
        if 'right_eye' == key:
            eye_x = np.mean([dict[key][i][0]+x0 for i in range(len(dict[key]))])
            eye_y = np.mean([dict[key][i][1]+y0 for i in range(len(dict[key]))])
            cv2.circle(image, (int(eye_x),int(eye_y)), 3, (255,215,25),-1)

        if 'basin' == key or 'wing_nose' == key:
            pts = np.array([[dict[key][i][0]+x0,dict[key][i][1]+y0] for i in range(len(dict[key]))],np.int32)
            # print(pts)
            cv2.polylines(image,[pts],False,color,thickness = 2)

        else:
            points_array = np.zeros((1,len(dict[key]),2),dtype = np.int32)
            for i in range(len(dict[key])):
                x,y,_ = dict[key][i]
                points_array[0,i,0] = x+x0
                points_array[0,i,1] = y+y0

            # cv2.fillPoly(image, points_array, color)
            cv2.drawContours(image,points_array,-1,color,thickness=2)
def refine_face_bbox(bbox,img_shape):
    height,width,_ = img_shape

    x1,y1,x2,y2 = bbox

    expand_w = (x2-x1)
    expand_h = (y2-y1)

    x1 -= expand_w*0.06
    y1 += expand_h*0.15
    x2 += expand_w*0.06
    y2 += expand_h*0.03

    x1,y1,x2,y2 = int(x1),int(y1),int(x2),int(y2)

    x1 = int(max(0,x1))
    y1 = int(max(0,y1))
    x2 = int(min(x2,width-1))
    y2 = int(min(y2,height-1))

    return (x1,y1,x2,y2)
