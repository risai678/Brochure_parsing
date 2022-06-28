import glob
import re
import time

import pandas as pd
from pdf2image import convert_from_path
import os
import cv2
# import keras_ocr
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
# pipeline = keras_ocr.pipeline.Pipeline()
BASE_DIR = os.getcwd()
from paddleocr import PaddleOCR, draw_ocr
ocr = PaddleOCR(use_angle_cls=True,
                                lang='en')




def get_price(pred):
    price=[]
    for i in pred[0][0]:
        if i!='rs':
            price.append(i)
    return ''.join(price)
def gett_boxes(image,box_measurement):
    if box_measurement!=[]:
        x=box_measurement[0]
        y=box_measurement[1]
        w=box_measurement[2]
        h=box_measurement[3]
        cropped = image[int(y ):y + (h), int(x):x + w]
        image = cv2.fastNlMeansDenoisingColored(cropped, None, 10, 10, 7, 15)
    else:
        image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 15)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 30, 200)
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    products_list=[]
    price_list=[]
    previous_list=[]
    boxx=True
    if box_measurement==[]:
        boxx=False
    full_list=[]
    brand_list=[]
    listt_h=[]
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4:
            if cv2.contourArea(cnt) <= 200:
                continue
            # print(cv2.contourArea(cnt))
            x, y, w, h = cv2.boundingRect(cnt)
            # print(h)

            if h>900:
                box_measurement=[x,y,w,h]
            z = y + 50

            if boxx==True:
                z=y+40

            p=y-50
            if w > 200 and h<900 :
                # print(cnt)
                # cv2.drawContours(image, [cnt], -1, (0, 255, 0), 3)
                price_cropped = image[int(y-3):y + (h+3), int(x):x + w]

                roi_cropped = image[int(z):z + (h+40), int(x):x + w]
                previous_cropped = image[int(p):p + (h+3), int(x):x + w]



                price_result = ocr.ocr(price_cropped, cls=True)
                name_result = ocr.ocr(roi_cropped, cls=True)
                previous_result = ocr.ocr(previous_cropped, cls=True)
                # cv2.imshow('External Contours', previous_cropped)
                # cv2.waitKey(0)
                product=[]
                Pricee = False
                try:
                    if 'Rs' not in price_result[0][1][0]:
                        continue
                except:
                    continue
                for line in price_result:
                    Pricee=True
                    price_list.append(line[1][0])
                if Pricee==False:
                    price_list.append('None')
                try:
                    previous_list.append(previous_result[0][1][0])
                except:
                    previous_list.append('Not_Given')
                for line in name_result:
                    price=line[1][0]
                    product.append(price)
                brand=name_result[0][1][0]
                if len(brand)>1:
                    brand=brand.split(' ')[0]
                brand_list.append(brand)
                product_name=' '.join(product)
                products_list.append(product_name)

    products_list.append(' ')
    brand_list.append(' ')
    price_list.append(' ')
    previous_list.append(' ')
    return products_list,brand_list,price_list,previous_list,box_measurement




def get_roii(image):
    box_measurement=[]
    products,brand_list,new_price,previous_price,box=gett_boxes(image,box_measurement)

    if box_measurement!=[]:
        products2,brand_list2,new_price2,previous_price2,boxx=gett_boxes(image,box)
        products=products+products2
        brand_list=brand_list+brand_list2
        new_price=new_price+new_price2
        previous_price=previous_price+previous_price2
    products.reverse()
    brand_list.reverse()
    new_price.reverse()
    previous_price.reverse()


    df = pd.DataFrame([products, brand_list,new_price, previous_price])

    df = df.T
    df.columns=['Products', 'Brand', 'New_price', 'Previous_price']
    df.drop(df[df.New_price =='None'].index,inplace=True)
    # df.Products.drop(list(df.filter(regex = 'Rs 24')),inplace = True)
    # df.drop(df[df.Products.isnan].index,inplace=True)
    df=df[~df.Products.str.contains("Rs",na=False)]
    df = df[df['Products'].notna()]
    df.drop_duplicates(inplace=True)
    # df.to_csv('lolo.csv')
    return df

def extract_data(files):
    # files = glob.glob(BASE_DIR + '/images/*.jpg')
    # files = sorted(files, key=lambda x: float(re.findall("(\d+)", x)[0]))
    count=0
    df_list=[]
    for i in files:
        print(i.split('/')[-1].split('.')[0])
        image = cv2.imread(i, flags=cv2.IMREAD_COLOR)
        print('extracting data from Page '+str(i.split('/')[-1].split('.')[0]))
        dff=get_roii(image)
        df_list.append(dff)
        count+=1
    final_df = pd.concat(df_list, ignore_index=True)
    final_df.columns = ['Products', 'Brand', 'New_price', 'Previous_price']
    # final_df.to_csv(BASE_DIR+'/csvs/extracted.csv',index=False)
    final_df.to_csv(BASE_DIR+'/extracted.csv',index=False)





if __name__ == "__main__":
    files=glob.glob(BASE_DIR+'/images/*.jpg')
    files = sorted(files, key=lambda x: float(re.findall("(\d+)", x)[0]))
    extract_data(files)

