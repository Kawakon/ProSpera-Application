# ProSpera-Application
Python application to test ProSpera camera

In this repository, I have developed a Python script to test an Linux-based embedded camera device, called the ProSpera Camera, that is used to monitor the growth of crops. The ProSpera camera would be fastened 
to a moving pivot and directed towards the section of the field to capture images of the plants growing on the crop field. The purpose of testing the ProSpera camera was to verify the camera features and identify and compile a list 
of any bugs found in the devices. The Python script would connect to the ProSpera camera via a SSH (Secure Shell) connection and execute commands to control the camera from a Linux terminal, as the camera could connect to a local network using Wi-Fi. 

** PLEASE NOTE THAT THIS REPOSITORY DOES NOT INCLUDE THE SSH KEYS USED TO AUTHENTICATE ACCESS TO THE PROSPERA CAMERA. THIS REPOSITORY SIMPLY DEMONSTRATES THE CODE WRITTEN FOR THIS PROJECT. **

I also converted the Python script into a file can be run as an Windows executable application to avoid installing a Python interpreter on a user's machine, using the Python tool PyInstaller. 

![app_interface](https://user-images.githubusercontent.com/43174428/139049034-d3303983-6c8d-41ef-9b84-a99ff17cad67.png)

The image above shows the application interface where the user enters the conditions for the test to be performed. The application takes the MAC address of the device to obtain the corresponding IP address for SSH access. Once the application is able connect to the device, one of the following tests are conducted:

* Image Capture: Performs an image capture on the ProSpera camera and presents the image on the user's machine.
* Load Capture: Performs a series of image captures on the ProSpera camera, according to the number of pictures inputted by the user.
* Zoom Capture: Performs five image captures at camera zoom positions between 390 and 1700 zoom units in intervals of 100 units. 
* Reboot: Performs a system reboot of the ProSpera camera.
* Zoom Change: Changes the position of the zoom on the ProSpera camera between 390 and 1700 zoom units and checks if the actual zoom position matches the set value.
* Hardware Button: Checks state of a button on the ProSpera camera to determine if button has been pressed.
* Wi-Fi Board: A file is sent to the ProSpera camera via SSH and connectivity statistics throughout the transfer are presented.

Images that are captured by the camera are saved onto the user's Desktop into a directory called *test_imgs*. Furthermore, test status, image file properties, and test conditions are saved in text files corresponding to the test performed within the *statistics* directory on the user's Desktop.

