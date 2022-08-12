from collections import OrderedDict
from IPython.display import Image
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import glob
import pandas
import cv2 as cv
from numpy import expand_dims
from keras.preprocessing.image import load_img, img_to_array, ImageDataGenerator
from matplotlib import pyplot
from sklearn.utils import shuffle
from sklearn.metrics import confusion_matrix, f1_score, accuracy_score

import tensorflow
from tensorflow import keras
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Dense, Conv2D, Activation, GlobalAveragePooling2D, MaxPooling2D, Flatten
from tensorflow.keras.preprocessing import image
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.applications.vgg16 import VGG16
from tensorflow.keras.applications.vgg16 import preprocess_input

import flwr as fl

toTERFolder = '/Users/hbp/Documents/GitHub.nosync/TER2021-074/Code'
testImage = toTERFolder + '/TestImageDemo'
testData30 = toTERFolder + '/TestData/P30'
testData50 = toTERFolder + '/TestData/P50'
data30 = toTERFolder + '/DataClient1-P30/P30'
data50 = toTERFolder + '/DataClient1-P30/P50'
modelPath = toTERFolder + '/DataClient1-P30/model'

classes = ['Speed Limit 30', 'Speed Limit 50']
nbClasses = 2
classLabel = 0
nbAugmented = 10
xTrain = np.empty(shape=(0, 224, 224, 3))
yTrain = []
xTest = np.empty(shape=(0, 224, 224, 3))
yTest = []

for cl in classes:
    augmentedIndex = 0
    if(cl == 'Speed Limit 30'):
        listImages = glob.glob(data30+'/*')
    else:
        listImages = glob.glob(data50+'/*')
    yTrain += [classLabel]*len(listImages)
    for pathImg in listImages:
        img = image.load_img(pathImg, target_size=(224, 224))
        im = image.img_to_array(img)
        normalizedImg = np.zeros((224, 224))
        im = cv.normalize(im,  normalizedImg, 0, 255, cv.NORM_MINMAX)
        im = np.expand_dims(im, axis=0)
        im = preprocess_input(im)
        xTrain = np.vstack([xTrain, im]) #Adding normal image
    classLabel += 1

classLabel = 0
for cl in classes:
    augmentedIndex = 0
    if(cl == 'Speed Limit 30'):
        listImages = glob.glob(testData30+'/*')
    else:
        listImages = glob.glob(testData50+'/*')
    yTest += [classLabel]*len(listImages)
    for pathImg in listImages:
        img = image.load_img(pathImg, target_size=(224, 224))
        im = image.img_to_array(img)
        normalizedImg = np.zeros((224, 224))
        im = cv.normalize(im,  normalizedImg, 0, 255, cv.NORM_MINMAX)
        im = np.expand_dims(im, axis=0)
        im = preprocess_input(im)
        xTest = np.vstack([xTest, im]) #Adding normal image
    classLabel += 1

yTrain = keras.utils.to_categorical(yTrain, nbClasses)
xTrain, yTrain = shuffle(xTrain, yTrain)

yTest = keras.utils.to_categorical(yTest, nbClasses)
xTest, yTest = shuffle(xTest, yTest)

# Load model and data
model = keras.models.load_model(modelPath)
    
listImages = glob.glob(testImage+'/*')
for pathImg in listImages:
    imTest = image.load_img(pathImg, target_size=(224, 224))
    imTest = image.img_to_array(imTest)
    normalizedImg = np.zeros((224, 224))
    imTest = cv.normalize(imTest,  normalizedImg, 0, 255, cv.NORM_MINMAX)
    imTest = np.expand_dims(imTest, axis=0)
    imTest = preprocess_input(imTest)
beforeFederatedPredictionImTest = model.predict(imTest)
if(beforeFederatedPredictionImTest[0][0] == 1):
    print("\nBefore Federated Test image recognized at : Speed Limit 30")
else:
    print("\nBefore Federated Test image recognized at : Speed Limit 50")

print("\nShould have bad results on P50")
yPredictedTest = model.predict(xTest)
print("Confusion Matrix : \n")
print(confusion_matrix(yTest.argmax(axis=1), yPredictedTest.argmax(axis=1)))
print("F1 Score : ", str(f1_score(yTest.argmax(axis=1), yPredictedTest.argmax(axis=1))))
print("Accuracy : ", str(accuracy_score(yTest.argmax(axis=1), yPredictedTest.argmax(axis=1))))

class PanelClient(fl.client.NumPyClient):
    def get_parameters(self):
        return model.get_weights()

    def fit(self, parameters, config):
        model.set_weights(parameters)
        model.fit(xTrain, yTrain, epochs=15, batch_size=32, steps_per_epoch=3)
        return model.get_weights(), len(xTrain), {}

    def evaluate(self, parameters, config):
        model.set_weights(parameters)
        loss, accuracy = model.evaluate(xTest, yTest)
        return loss, len(xTest), {"accuracy": accuracy}

print("\nFederation")
# Load Flower
fl.client.start_numpy_client("[::]:8080", client=PanelClient())

print("\nShould have good results on P30")
yPredictedTest = model.predict(xTest)
print("Confusion Matrix : \n")
print(confusion_matrix(yTest.argmax(axis=1), yPredictedTest.argmax(axis=1)))
print("F1 Score : ", str(f1_score(yTest.argmax(axis=1), yPredictedTest.argmax(axis=1))))
print("Accuracy : ", str(accuracy_score(yTest.argmax(axis=1), yPredictedTest.argmax(axis=1))))

if(beforeFederatedPredictionImTest[0][0] == 1):
    print("\nBefore Federated Test image recognized at : Speed Limit 30")
else:
    print("\nBefore Federated Test image recognized at : Speed Limit 50")
print(beforeFederatedPredictionImTest)

afterFederatedPredictionImTest = model.predict(imTest)
if(afterFederatedPredictionImTest[0][0] == 1):
    print("\nnAfter Federated Test image recognized at : Speed Limit 30")
else:
    print("\nAfter Federated Test image recognized at : Speed Limit 50")
print(afterFederatedPredictionImTest)