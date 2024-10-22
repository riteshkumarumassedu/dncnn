
import argparse
import re
import os, glob, datetime
#export CUDA_VISIBLE_DEVICES=3
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import numpy as np
from keras.layers import  Input,Conv2D,BatchNormalization,Activation,Subtract, Add
from keras.models import Model, load_model
from keras.callbacks import CSVLogger, ModelCheckpoint, LearningRateScheduler, ReduceLROnPlateau
from keras.optimizers import Adam
import data_generator as dg
import keras.backend as K

# integrating tensorboard
from keras.callbacks import TensorBoard
from time import time



## Params
parser = argparse.ArgumentParser()
parser.add_argument('--model', default='DnCNN', type=str, help='choose a type of model')
parser.add_argument('--batch_size', default=128, type=int, help='batch size')
parser.add_argument('--val_data', default='data/Train400_val', type=str, help='path of train data')
parser.add_argument('--train_data', default='data/Train400', type=str, help='path of train data')
parser.add_argument('--sigma', default=25, type=int, help='noise level')
parser.add_argument('--epoch', default=100, type=int, help='number of train epoches')
parser.add_argument('--lr', default=1e-3, type=float, help='initial learning rate for Adam')
parser.add_argument('--save_every', default=10, type=int, help='save model at every x epoches')
args = parser.parse_args()


save_dir = os.path.join('models','sigma'+str(args.sigma))
steps_per_epoch = 300

if not os.path.exists(save_dir):
    os.mkdir(save_dir)

def DnCNN(depth,filters=64,image_channels=1, use_bnorm=True):

    layer_count = 0
    inpt = Input(shape=(None,None,image_channels),name = 'input'+str(layer_count))


    # 1st layer, Conv+relu
    layer_count += 1
    x = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',name = 'conv'+str(layer_count))(inpt)
    layer_count += 1
    x = Activation('relu',name = 'relu'+str(layer_count))(x)


    # depth-2 layers, Conv+BN+relu
    for i in range(depth-2):
        layer_count += 1
        y_loop = Conv2D(filters=filters, kernel_size=(3,3), strides=(1,1),kernel_initializer='Orthogonal', padding='same',use_bias = False,name = 'conv'+str(layer_count))(x)
        if use_bnorm:
            layer_count += 1
            y_loop = BatchNormalization(axis=3, momentum=0.1,epsilon=0.0001, name = 'bn'+str(layer_count))(y_loop)

        layer_count += 1
        y_loop = Activation('relu',name = 'relu'+str(layer_count))(y_loop)


        layer_count += 1
        y_loop = Conv2D(filters=filters, kernel_size=(3, 3), strides=(1, 1), kernel_initializer='Orthogonal', padding='same', use_bias=False, name='conv' + str(layer_count))(y_loop)
        if use_bnorm:
            layer_count += 1
            y_loop = BatchNormalization(axis=3, momentum=0.1, epsilon=0.0001, name='bn' + str(layer_count))(y_loop)

        layer_count += 1
        y_loop = Activation('relu', name='relu' + str(layer_count))(y_loop)


        # Adding skip connections
        layer_count += 1
        y_loop = Add(name='Add'+ str(layer_count))([y_loop, x])
        x = y_loop



    # last layer, Conv
    layer_count += 1
    x = Conv2D(filters=image_channels, kernel_size=(3,3), strides=(1,1), kernel_initializer='Orthogonal',padding='same',use_bias = False,name = 'conv'+str(layer_count))(y_loop)
    layer_count += 1
    x = Subtract(name = 'subtract' + str(layer_count))([inpt, x])   # input - noise
    model = Model(inputs=inpt, outputs=x)
    
    return model


def findLastCheckpoint(save_dir):
    file_list = glob.glob(os.path.join(save_dir,'model_*.hdf5'))  # get name list of all .hdf5 files
    #file_list = os.listdir(save_dir)
    if file_list:
        epochs_exist = []
        for file_ in file_list:
            result = re.findall(".*model_(.*).hdf5.*",file_)
            #print(result[0])
            epochs_exist.append(int(result[0]))
        initial_epoch=max(epochs_exist)   
    else:
        initial_epoch = 0
    initial_epoch = 0
    return initial_epoch

def log(*args,**kwargs):
     print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:"),*args,**kwargs)

def lr_schedule(epoch):
    initial_lr = args.lr
    if epoch<=50:
        lr = initial_lr
    elif epoch<=70:
        lr = initial_lr/10
    elif epoch<=90:
        lr = initial_lr/10 
    else:
        lr = initial_lr/10 
    log('current learning rate is %2.8f' %lr)
    return lr

def train_datagen(epoch_num=5,batch_size=128,data_dir=args.train_data):
    while(True):
        n_count = 0
        if n_count == 0:
            #print(n_count)
            xs = dg.datagenerator(data_dir)
            assert len(xs)%args.batch_size ==0, \
            log('make sure the last iteration has a full batchsize, this is important if you use batch normalization!')
            xs = xs.astype('float32')/255.0
            indices = list(range(xs.shape[0]))
            n_count = 1
        for _ in range(epoch_num):
            np.random.shuffle(indices)    # shuffle
            for i in range(0, len(indices), batch_size):
                batch_x = xs[indices[i:i+batch_size]]
                noise =  np.random.normal(0, args.sigma/255.0, batch_x.shape)    # noise
                #noise =  K.random_normal(ge_batch_y.shape, mean=0, stddev=args.sigma/255.0)
                batch_y = batch_x + noise 
                yield batch_y, batch_x
        

def val_datagen(epoch_num=5,batch_size=128,data_dir=args.val_data):
    while(True):
        n_count = 0
        if n_count == 0:
            xs = dg.datagenerator(data_dir)
            assert len(xs)%args.batch_size ==0, \
            log('make sure the last iteration has a full batchsize, this is important if you use batch normalization!')
            xs = xs.astype('float32')/255.0
            indices = list(range(xs.shape[0]))
            n_count = 1
        for _ in range(epoch_num):
            np.random.shuffle(indices)    # shuffle
            for i in range(0, len(indices), batch_size):
                batch_x = xs[indices[i:i+batch_size]]
                noise =  np.random.normal(0, args.sigma/255.0, batch_x.shape)    # noise
                #noise =  K.random_normal(ge_batch_y.shape, mean=0, stddev=args.sigma/255.0)
                batch_y = batch_x + noise
                yield batch_y, batch_x


# define loss
def sum_squared_error(y_true, y_pred):
    #return K.mean(K.square(y_pred - y_true), axis=-1)
    #return K.sum(K.square(y_pred - y_true), axis=-1)/2
    return K.sum(K.square(y_pred - y_true))/2


    
if __name__ == '__main__':
    # model selection
    model = DnCNN(depth=20,filters=64,image_channels=1,use_bnorm=True)
    model.summary()

    tensorboard = TensorBoard(log_dir="logs/{}".format(time()),update_freq='epoch')

    # load the last model in matconvnet style
    initial_epoch = findLastCheckpoint(save_dir=save_dir)
    if initial_epoch > 0:  
        print('resuming by loading epoch %03d'%initial_epoch)
        model = load_model(os.path.join(save_dir,'model_%03d.hdf5'%initial_epoch), compile=False)
    
    # compile the model
    model.compile(optimizer=Adam(0.001), loss=sum_squared_error)
    
    # use call back functions
    checkpointer = ModelCheckpoint(os.path.join(save_dir,'model_{epoch:03d}.hdf5'), verbose=1, period=args.save_every, save_best_only=True)
    csv_logger = CSVLogger(os.path.join(save_dir,'log.csv'), append=True, separator=',')

    # criteria to reduce the learning rate
    # lr_scheduler = LearningRateScheduler(lr_schedule)

    # Reduce learning rate if there is no improvement in last x epochs
    lr_scheduler = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.00001)


    history = model.fit_generator(train_datagen(batch_size=args.batch_size),steps_per_epoch=steps_per_epoch, epochs=args.epoch, verbose=1,
                                  initial_epoch=initial_epoch, validation_data=val_datagen(batch_size=args.batch_size),validation_steps=1,
                callbacks=[checkpointer,csv_logger,lr_scheduler])

















