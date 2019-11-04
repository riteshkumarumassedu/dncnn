State of the Art Deep learning based "Image Denoising" algorithm : DnCNN implementation in Keras and Pytorch for dicom, jpeg and numpy data.

## How to Run the Training:

3.	Run the following command from the terminal:
“Python main_train.py “ and pass the following arguments:
<pre>
--batch_size
--val_data <validation data dir>
--train_data <training data dir>
-- sigma <amount of gaussian noise you want to add 0-100>
--epoch <number of epochs you want to run the training for>
--lr <learning rate>
--save_every <would save the model weights after every x epochs>

All the trained model weights would be saved in the “models” directory of this project.
</pre>

## How to Run the Inference:

Run the following command from the terminal:
“Python main_test.py”  and pass the following arguments:
<pre>
--set_dir <test data directory>
--sigma <amount of gaussian noise you want you want to add>
--model_dir <directory where saved model weights have been stored>
--model_name <saved model weights filename>
-- result_dir <directory to store the results>
-- save_results <whether to save the results or not 0 or 1>
</pre>


<pre>
. dncnn                   Code Root Directory
  |- data                 Images directory
    |- test               Test images directory	
    |-train               Training images 
    |- val                validation images 
  |- data_generator.py    data loader method implementation
  |- data_transform.py    PyTorch data transformations implementation
  |- main_train.py        Projects main file to start the training 
  |- main_test.py         Projects main file to run inference
  |- logs                 Tensor board logs
  |- models               saved model weights
  |- results              inference output images 

</pre>
