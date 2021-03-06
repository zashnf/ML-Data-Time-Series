# -*- coding: utf-8 -*-
"""TimeSeries_ZashikaHanifa.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XDsmn9c7b5MLZ2Q7PntjMd7N4kMwYkQC
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from keras.layers import Dense, LSTM
from sklearn.model_selection import train_test_split

#membaca dataset delhiweather.csv
df = pd.read_csv('delhiweather.csv')
df.shape
#pada data set ini terdapat 100990 data dengan kolom sebanyak 20

df.info()

df.head(10)

#mengecek apakah ada nilai yang hilang dr dataset
df.isnull().sum()

df['datetime_utc']=pd.to_datetime(df['datetime_utc'])
df['datetime_utc'].head()
df[' _tempm'].fillna(df[' _tempm'].mean(), inplace=True) 
df = df[['datetime_utc',' _tempm' ]]
df.head(10)

#mengubah kolom datatime_utc menjadi date dan dibuat df baru bernama delhinew
delhi=df[['datetime_utc',' _tempm']].copy()
delhi['date'] = delhi['datetime_utc'].dt.date
delhinew=delhi.drop('datetime_utc',axis=1)
delhinew.set_index('date', inplace= True)
delhinew.head(10)

delhinew.info()

#membuat plot dari data delhi weather
date = delhi['date'].values
temp = delhi[' _tempm'].values

plt.figure(figsize=(18,6))
plt.plot(delhinew)
plt.title('Delhi Weather')
plt.xlabel('Date')
plt.ylabel('Temperature')
plt.show()

#menerima sebuah atribut yg telah dikonversi menjadi tipe numpy,lalu mengembalikan label dan atribut dari dataset dalam bentuk batch
def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[-1:]))
    return ds.batch(batch_size).prefetch(1)

#split data dimana validation setnya 20% dari dataset
x_train, x_test, y_train, y_test = train_test_split(temp, date, test_size = 0.2, random_state = 0 , shuffle=False)
#mengetahui ukuran x_train dan x_test
print(len(x_train), len(x_test))

# model
data_x_train = windowed_dataset(x_train, window_size=60, batch_size=100, shuffle_buffer=5000)
data_x_test = windowed_dataset(x_test, window_size=60, batch_size=100, shuffle_buffer=5000)

model = tf.keras.models.Sequential([
  tf.keras.layers.LSTM(64, return_sequences=True),
  tf.keras.layers.Dense(30, activation="relu"),
  tf.keras.layers.Dense(1),
  tf.keras.layers.Lambda(lambda x: x * 400)
])

#Optimizer menggunakan Learning Rate
lr_schedule = tf.keras.callbacks.LearningRateScheduler(
    lambda epoch: 1e-8 * 10**(epoch / 20))
optimizer = tf.keras.optimizers.SGD(learning_rate=1e-8, momentum=0.9)
model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])

max = df[' _tempm'].max()
print('Max value: ' )
print(max)
min = df[' _tempm'].min()
print('Min Value: ')
print(min)

x = (max - min) * (10 / 100)
print(x)

# callback
class CallBack(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('mae')< x):
      self.model.stop_training = True
      print('\nFor Epoch', epoch, ' training has been stopped.''\n Because MAE of the model has reach < 10% of data scale')
callbacks = CallBack()

tf.keras.backend.set_floatx('float64')
history = model.fit(data_x_train ,epochs=100, validation_data=data_x_test, callbacks=[callbacks])

# plot of mean absolute error
plt.plot(history.history['mae'])
plt.plot(history.history['val_mae'])
plt.title('MAE')
plt.ylabel('MAE')
plt.xlabel('Epoch')
plt.legend(['train', 'test'], loc='upper right')
plt.show()

# plot of loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['train', 'test'], loc='upper right')
plt.show()