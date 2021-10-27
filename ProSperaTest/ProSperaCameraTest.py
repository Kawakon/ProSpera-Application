#!/usr/bin/python

# PACKAGE DEFITIONS AND CONSTANTS

import threading
import tkinter as tk
import sys
from tkinter.font import NORMAL
from tkinter.constants import CENTER, DISABLED, E, END, LEFT, RAISED
import socket
from ipaddress import IPv4Network
import nmap
import paramiko
import os
import PIL
from PIL import Image
import pathlib
import shutil
import time
import re
import datetime
from scp import SCPClient
from contextlib import contextmanager


from trace_thread import thread_with_trace
from mac import MacAddress
from InvalidMACException import InvalidMACError
from ProgramEndException import ProgramEndError
from TableHeaders import TableHeaders

### GLOBAL VARIABLES SHOULD BE WITH LOGIC OF PROGRAM -- MODEL

# GLOBAL VARIABLES
hn = 'Prospera-Camera'
hdr = ""
connectionTime = 0
zoomVal = ""
loadVal = ""
mac_address = ""
save = ""
network = ""
user = ""
test = ""
ip = ""
username = ""
threads = [""]

# setting user variable 
dir_path = os.getcwd()
truncated = dir_path[9:]
index = truncated.find("\\")
if index < 0:
    user = truncated
else:
    user = truncated[:index]

# error encountered
end_program = False

# CLASSES 

class ProsperaView:
    """
        The view for Prospera Camera Test application. Allows mac addresses of camera devices to be entered
        to begin tests and displays output. 
    """
    
    def __init__(self) -> None:
        self.window = tk.Tk()
        self.window.title("Prospera Camera Test")
        self.create_widgets()

    def create_widgets(self):

        # Features to test
        options = ["Image Capture", "Load Capture", "Zoom Capture", "Reboot", "Zoom Change", "Hardware Button", "Manufacturer Test", "Calibration", "Wi-Fi Board"]
        self.dropdownValue = tk.StringVar()
        self.logCheck = tk.IntVar()
        self.hdrCheck = tk.IntVar()
        self.dropdownValue.set("Select a Test")

        self.ask = tk.Label(
            text="Please scan the QR code on the Prospera Camera to enter the MAC address, then press ENTER or Start:",
            wraplength=300,
            pady=15,
            padx=5
        )
        
        self.entry = tk.Entry(
            justify=CENTER, 
            width=60
        )
        self.entry.focus_set()

        self.ask.pack()
        self.entry.pack()

        self.sub = tk.Frame()
        self.optionsButton = tk.Button(
            self.sub, 
            text="Enter test values",
            width=17,
            height=1,
            command=lambda: OptionsView(self.window)
        )
        self.testMenu = tk.OptionMenu(self.sub, self.dropdownValue, *options)
        self.testMenu.config(width=15)
        self.sub.pack(pady=10)

        
        self.sub2 = tk.Frame()
        self.start = tk.Button(
            self.sub2,
            text="Start",
            width=20,
            height=3, 
            bg="#4273c2",
            command=startThread,
            relief=RAISED
        )
        self.stop = tk.Button(
            self.sub2,
            text="Stop",
            width=20,
            height=3, 
            bg="#4273c2",
            command=stopThread,
            relief=RAISED,
            state=DISABLED
        )
        self.sub2.pack(pady=10)

        self.subCheck = tk.Frame()
        self.logCheckbox = tk.Checkbutton(
            self.subCheck,
            text="Logs",
            variable=self.logCheck,
            onvalue=1,
            offvalue=0,
            width=10
        )
        self.hdrCheckbox = tk.Checkbutton(
            self.subCheck,
            text="HDR",
            variable=self.hdrCheck,
            onvalue=1,
            offvalue=0,
            width=10
        )
        self.testMenu.grid(column=1, row=0, padx=35)
        self.optionsButton.grid(column=0, row=0, sticky="ew", padx=35)
        self.start.grid(column=0, row=0, padx=25)
        self.stop.grid(column=1, row=0, padx=25)
        self.logCheckbox.grid(row=0, column=0)
        self.hdrCheckbox.grid(row=0, column=1)
        self.subCheck.pack()

        self.output_label = tk.Label(
            text="Output:"
        )
        self.output_label.pack()

        self.output = tk.Text(
            height=10,
            width=70,
            wrap="word"
        )
        self.entry.bind('<Return>', lambda event: startThread(), add="+")

        self.scroll = tk.Scrollbar(
            command=self.output.yview, 
        )
        
        self.output.config(state=DISABLED)
        self.output.bind("<1>", lambda event: self.output.focus_set())
        self.output.pack(padx=10, pady=10, fill='both', side=LEFT, expand=True)
        self.scroll.pack(pady=10, fill='y', expand=True)
        self.output['yscrollcommand'] = self.scroll.set

        # tags
        self.output.tag_configure("default", foreground="#000000")
        self.output.tag_configure("success", foreground="#00ff00")
        self.output.tag_configure("error", foreground="#ff0000")

    def display(self):
        self.window.mainloop()

    def getMAC(self):
        return self.entry.get()
    
    def isHDR(self):
        global hdr
        if self.logCheck.get() == 1:
            hdr = "--hdr"
        else:
            hdr = ""

    def getTest(self):
        return self.dropdownValue.get()

    def writeToOutput(self, message, verbose, tagName="default", begin="end-1c linestart", end="end"):
        if self.logCheck.get() == 1 or verbose == "nv":
            self.output.config(state=NORMAL)
            self.output.insert(END, message, (tagName, begin, end))
            self.output.see(END)
            self.output.update_idletasks()
            self.output.config(state=DISABLED)

    def disableEntry(self):
        self.entry.config(state=DISABLED)
    
    def enableEntry(self):
        self.entry.focus_set()
        self.entry.config(state=NORMAL)

    def clearEntry(self):
        self.entry.delete(0, 'end')

    def disableView(self):
        self.start.config(state=DISABLED)
        self.output.config(state=NORMAL)
        self.output.delete('1.0', tk.END)

    def enableView(self):
        self.enableEntry()
        self.start.config(state=NORMAL)
        self.output.config(state=DISABLED)

    def disableStop(self):
        self.stop.config(state=DISABLED)
    
    def enableStop(self):
        self.stop.config(state=NORMAL)

class OptionsView(tk.Toplevel):
    """Creates top-level window when test parameters can be entered.
    """

    def __init__(self, master = None):
        super().__init__(master=master)
        self.title("Set Test Values")
        self.create_widgets()

    def create_widgets(self):

        # ZOOM VALUE
        self.zoomFrame = tk.Frame(
            self,
            padx=20,
            pady=20
        )
        self.zoomLabel = tk.Label(
            self.zoomFrame,
            text="Enter a zoom value between 390 and 1700:",
            pady=4
        )
        self.zoom = tk.Entry(
            self.zoomFrame,
            justify=CENTER,
            width=8
        )
        self.zoom.focus_set()
        self.zoomLabel.pack()
        self.zoom.pack()
        self.zoomFrame.grid(row=0, column=0)

        # LOAD VALUE
        self.loadFrame = tk.Frame(
            self,
            padx=20,
            pady=20
        )
        self.loadLabel = tk.Label(
            self.loadFrame,
            text="Enter a load value:",
            pady=4
        )
        self.load = tk.Entry(
            self.loadFrame,
            justify=CENTER,
            width=8
        )
        self.loadLabel.pack()
        self.load.pack()
        self.loadFrame.grid(row=0, column=1)

        self.enter = tk.Button(
            self,
            text="Enter",
            bg="#4273c2",
            width=15,
            height=1,
            pady=10,
            command=lambda: self.getOptions()
        )
        self.enter.grid(row=1, column=0, columnspan=2, pady=10)

    def getOptions(self):

        global zoomVal, loadVal

        zoomVal = self.zoom.get()
        loadVal = self.load.get()
        self.destroy()

### THREAD FUNCTIONS FOR PROSPERA VIEW -- VIEW

# THREAD FUNCTIONS

def startThread():
    """ Begins main execution thread upon clicking on the 'Start' button.
    """
    executionThread = thread_with_trace(target=verifyProsperaCamera, daemon=True)
    threads[0] = executionThread
    executionThread.start()
    view.enableStop()

def stopThread():
    """ Forces the main execution thread to exit.
    """
    #end = threading.Thread(target=killMain)
    #end.start()

    view.writeToOutput("\nStopping...\n", "nv")
    thread = threads[0]
    thread.kill()
    thread.join()
    view.enableView()
    view.disableStop()

def killMain():
    """ Thread used to kill main execution thread.
    """
    view.writeToOutput("\nStopping...\n", "nv")
    thread = threads[0]
    thread.kill()
    thread.join()
    view.enableView()
    view.disableStop()

# MAIN EVENT HANDLER -- CONTROLLER

def verifyProsperaCamera():
    """
        Begins test of Prospera Camera. Searches the network for the Prospera camera and establishes a connection via SSH, if possible. 
        Once connected, the following camera tests are performed:
        T1 - Capture Image
        T2 - Load Test
        T3 - Zoom Test
        T4 - Reboot
    """
    global end_program, connectionTime, test, network, zoomVal, loadVal 

    try:
        if not os.path.exists("C:\\Program Files (x86)\\Nmap"):
            view.writeToOutput("\nWARNING! NO VERSION OF NMAP HAS BEEN DETECTED ON YOUR SYSTEM. PLEASE INSTALL NMAP TO \"C:\\Program Files (x86)\\Nmap\" TO CONTINUE. THE LATEST VERSION OF NMAP CAN BE FOUND HERE: \nhttps://nmap.org/download.html\n", "nv", "error")
            end_program = True
            raise ProgramEndError() 

        start = time.time()
            
        test = view.getTest()
        view.isHDR()
        view.disableView()
        view.writeToOutput("\n***************BEGIN TEST***************\n\n", "nv")
        getMacAddress()
        checkValues()
        # view.clearEntry()
        view.disableEntry()

        if end_program:
            raise ProgramEndError()

        # create directory for test images 
        createDirectory(f"C:/Users/{user}/Desktop/Prospera/test_imgs", "Unable to create directory for test images")

        # create directory for private key and copy key to directory
        createDirectory(f"C:/Users/{user}/Desktop/Prospera/private_keys", "Unable to create directory for private key and add key file")

        # create directory for statistics (connectionTime, file copy properties)
        createDirectory(f"C:/Users/{user}/Desktop/Prospera/statistics", "Unable to create directory for test statistics")

        # copy private key to private_keys folder and icon file to Prospera folder
        privateKeyExist = True
        iconExist = True
        if not os.path.exists(f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem"):
            privateKeyExist = False
        if not os.path.exists(f"C:/Users/{user}/Desktop/Prospera/valley.ico"):
            iconExist = False
        if not iconExist or not privateKeyExist:
            try:
                if not privateKeyExist:
                    shutil.copy(f"C:/Users/{user}/Downloads/ProSperaTest/prospera-dev.pem", f"C:/Users/{user}/Desktop/Prospera/private_keys")
                if not iconExist:
                    shutil.copy(f"C:/Users/{user}/Downloads/ProSperaTest/valley.ico", f"C:/Users/{user}/Desktop/Prospera/")
                
            except Exception as e:
                #view.writeToOutput("\n" + e.__str__() + "\n", "nv")
                view.writeToOutput("\nCould not find SSH key file or icon file in Downloads folder. Please install the application zip file to the Downloads directory.\n", "nv", "error")
                end_program = True
                pass
        
        if test == "Select a Test":
            end_program=True
            view.writeToOutput("Please select a test.", "nv", "error")

        if end_program:
            raise ProgramEndError()

        view.writeToOutput(f"\nSearching for {hn} on network...\n", "nv", )
        establishConnection()

        if end_program:
            raise ProgramEndError()

        view.writeToOutput(f"\n{hn} found on network...\n", "nv", )

        scpInfo = []
        view.writeToOutput(f"\nStarting {test} test...\n", "nv", )
        
        with suppress_stdout():
            if test == "Image Capture":
                # TEST 1 : CAPTURE IMAGE FROM PROSPERA CAMERA
                scpInfo = testImageCapture()
            elif test == "Load Capture":
                # TEST 2 : LOAD CAPTURE OF PROSPERA CAMERA
                scpInfo = testLoadCapture(loadVal)
            elif test == "Zoom Capture":
                # TEST 3 : ZOOM CAPTURE OF PROSPERA CAMERA
                testZoomCapture()
            elif test == "Reboot":
                # TEST 4 : CAMERA REBOOT
                testReboot()
            elif test == "Zoom Change":
                testZoomChange()
            elif test == "Hardware Button":
                testHardwareInterfaceButton()
            elif test == "Manufacturer Test":
                scpInfo = testManufacture()
            elif test == "Calibration":
                scpInfo = testCalibration()
            elif test == "Wi-Fi Board":
                testWifiBoard()
            if test != "Zoom Capture" and test != "Reboot" and test != "Zoom Change" and test != "Wi-Fi Board":
                # mac address, ip address, connection time, test, load, zoom value, filename, date, upload time, size, upload speed, test status
                writeStatistics(test.lower().replace(" ", "_"), [mac_address.getMAC(), ip, connectionTime, test, scpInfo[0], scpInfo[1], scpInfo[2], scpInfo[3], scpInfo[4], scpInfo[5], scpInfo[6], scpInfo[7]])

        end = time.time()
        view.writeToOutput(f"\nTime taken for {test} test: {end-start} seconds\n", "nv")

    except Exception as e:
        view.writeToOutput("\n" + e.__str__() + "\n", "nv")
        view.writeToOutput("\AN ERROR HAS OCCURRED. PLEASE TRY AGAIN...", "nv", "error")
        end_program = False
        pass  

    view.enableView()
    view.disableStop() 

### FUNCTION DEFINITIONS AND CAMERA TESTS SHOULD BE IN THE LOGIC OF THE PROGRAM -- MODEL

# FUNCTION DEFINITIONS

def establishConnection():

    "Attempts to establish connection with Prospera camera and records time required to connect to device."

    global ip, username, connectionTime, end_program

    connected = False
    startConnectTime = time.time()
    tries = 1

    while not connected and tries <= 60:

        getNetwork()
        nm = nmap.PortScanner()

        nm.scan(hosts=network, arguments='-sn')

        host_list = nm.all_hosts()
        matches = []
        view.writeToOutput(f"\nThe existing hosts on the network {network} are the following: \n\n", "v")
        for host in host_list:
                if  'mac' in nm[host]['addresses']:
                        view.writeToOutput(host+' : '+nm[host]['addresses']['mac'] + "\n","v")
                        if mac_address.getMAC() == nm[host]['addresses']['mac']:
                                matches.append(nm[host]['addresses']['ipv4'])

        # printing the matched IP addresses
        view.writeToOutput("\n\nThe following IP addresses were matched to the MAC:\n\n", "v")
        for elem in matches:
                view.writeToOutput(elem + "\n", "v")
        # establishing SSH connection with each host found, check name of host
        found = False
        username = 'root'
        ip = ""
        for elem in matches:

            # connecting via SSH
            ip = elem   # current ip

            # might display connection verification here
            client = connect(ip, username, f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem")
            stdin, stdout, stderr = client.exec_command("hostname") # retrieve hostname corresponding to current ip
            lines = stdout.readlines()
            client.close()
            
            if lines and lines[0].strip() == hn: # found ip with desired hostname
                found = True
                view.writeToOutput("\n\n\nThe IP address for the hostname " + hn + " is " + elem + ".\n", "v")
                break

        if not found:
            tries += 1
        else:
            connected=True

    if tries <= 60:
        endConnectTime = time.time()
        connectionTime = endConnectTime - startConnectTime
    else: 
        view.writeToOutput(f"\nYou are currently connected to {network}, but unable to detect {hn} on the network.\nPlease wait and try again...\n", "nv", "error")
        end_program = True

def createDirectory(directory, errorMsg):
    """ Creates the directory at the path described by the parameter 'directory'. If unable to create the directory, the
    parameter 'errorMsg' is returned.
    """

    try: 
        if not os.path.exists(directory):
            oldMask = os.umask(000) # for permission to create folder
            os.makedirs(directory, 0o777)
            os.umask(oldMask)
        return True
    except Exception as e:
        #view.writeToOutput("\n" + e.__str__() + "\n", "nv")
        #view.writeToOutput("\n" + errorMsg + "...\n", "nv")
        return False

def writeStatistics(filename, message, test="default"):
    th = TableHeaders(test)
    fpath = f"C:/Users/{user}/Desktop/Prospera/statistics/{filename}.txt"
    statistics = ""
    if not os.path.exists(fpath):
        statistics = open(fpath, "w")
        statistics.write(th.getHeaderTemplate().format(*th.getTableHeaders()))
        statistics.write("\n")
        statistics.write(th.getHeaderTemplate().replace(':', ':-').format('', '', '', '', '', '', '', '', '', '', '', ''))
        statistics.write("\n")
    else:
        statistics = open(fpath, "a")
    statistics.write(th.getTemplate().format(*message))
    statistics.write("\n")
    statistics.close()

def scpCopy(client, source, destination, load=0):
    copy = SCPClient(client.get_transport(), socket_timeout=300)
    startTime = time.time()
    copy.get(source, destination, recursive=True, preserve_times=True)
    endTime = time.time()
    uploadTime = endTime-startTime
    basename = os.path.basename(source)
    filename = basename.split(".")[0]
    data = copy._read_stats(destination + "/" + basename)
    date = datetime.datetime.fromtimestamp(data[2]).__str__()
    kBytes = data[1]/1000
    if not os.path.isfile(destination + "/" + basename):
        kBytes = get_size(destination + "/" + basename)/1000
    uploadSpeed = (kBytes)/uploadTime
    stats = []
    if load == 0:
        stats.append("N/A")
    else:
        stats.append(load)
    stats.extend([zoomVal, filename, date, uploadTime, kBytes, uploadSpeed, "PASS"])
    copy.close()
    return stats

def connect(ip, username, key):
        """
        Establish SSH connection. 

        :param ip: ip address of remote server
        :param username: user account to use once connected
        :param key: location of private key file
        :type ip: str
        :type username: str
        :type key: str
        """
        client = paramiko.SSHClient()
        k = paramiko.RSAKey.from_private_key_file(key) # obtain private key file
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # automatically add the hostname and new host key to local HostKeys object (prior to connection, host key is unknown)
        client.connect(hostname=ip, username=username, pkey=k, timeout=120.5) # connect with current ip, username, and private key
        return client

def execute_commands(client, commands, files="default", fileNumber=0, log=True):
        """
        Execute multiple commands in succession.

        :param client: Client object in SSH connection
        :param commands: List of unix commands as strings.
        :param files: Specifies which test log files will be created for.
        :param fileNumber: Specifies numbering for log files 
        :param log: Sends output of command to log file, if True
        :type client: SSHClient
        :type commands: List[str]
        :type files: String
        :type fileNumber: int
        :type log: bool
        """
        ispError = False
        sharedLibraryError = False
        timeoutError = False
        zoomChangeError = False
        hardwareButtonResult = 0

        # creating directory to write log file
        success = createDirectory(f"C:/Users/{user}/Desktop/Prospera/log", "Unable to create log directory...")
        filename = f"log_{save}"
        filepath = f"C:/Users/{user}/Desktop/Prospera/log/{filename}.txt"
        if files == "loadTest":
            success = createDirectory(f"C:/Users/{user}/Desktop/Prospera/log/load", "Unable to create load directory...")
            filename = f"log{fileNumber}"
            filepath = f"C:/Users/{user}/Desktop/Prospera/log/load/{filename}.txt"
        elif files == "zoomTest":
            success = createDirectory(f"C:/Users/{user}/Desktop/Prospera/log/zoom", "Unable to create zoom directory...")
            filename = f"log_zoom{fileNumber}"
            filepath = f"C:/Users/{user}/Desktop/Prospera/log/zoom/{filename}.txt"
        elif files == "zoomChangeTest":
            success = createDirectory(f"C:/Users/{user}/Desktop/Prospera/log/zoomChange", "Unable to create zoomChange directory...")
            filename = f"log_zc{fileNumber}"
            filepath = f"C:/Users/{user}/Desktop/Prospera/log/zoomChange/{filename}.txt"
        elif files == "calibrationTest":
            success = createDirectory(f"C:/Users/{user}/Desktop/Prospera/log/calibration", "Unable to create calibration directory...")
            filename = "calibration"
            filepath = f"C:/Users/{user}/Desktop/Prospera/log/calibration/{filename}.txt"
        elif files == "wifiBoardTest":
            success = createDirectory(f"C:/Users/{user}/Desktop/Prospera/log/wifiBoard", "Unable to create wifiBoard directory...")
            filename = f"info_wfboard"
            filepath = f"C:/Users/{user}/Desktop/Prospera/log/wifiBoard/{filename}.txt"
        
        for cmd in commands:
            
            stdin, stdout, stderr = client.exec_command(cmd)

            # set and wait for timeout

            timeout = 210
            start = time.time()
            try:
                while time.time() < start + timeout:
                    if stdout.channel.exit_status_ready():
                        break
                else:
                    raise TimeoutError(f"{cmd}")
            except TimeoutError as e:
                timeoutError = True
                view.writeToOutput("\nThe following command has timed out:\n\n" + e.__str__() + f"\n\nPlease see the {filename} for more details.\n", "nv", "error")

            # read outputs from stdout, stderr

            stdout.channel.close()
            stderr.channel.close()
            response = stdout.readlines()
            error = stderr.readlines()

            writeFile = True              
            if not success:
                writeFile = False
            try:
                hardwareButtonResult = response[0].strip()
            except:
                pass

            if writeFile and log:
                try: 
                    log = open(filepath, "w")
                    log.write("\nCommand:\n" + cmd + "\n")
                    log.write("\nOutput: \n\n")
                    for line in response:
                        if ("[ISP_ERR]video_wait_buffer" in line) and not ispError:
                                ispError = True
                        if ("Error loading shared library" in line) and not sharedLibraryError:
                                sharedLibraryError = True
                                view.writeToOutput(f"\nMissing shared libraries on Prospera camera. Please view log{'_'+save if files == 'default' else fileNumber if files == 'loadTest' else '_'+'zoom'+str(fileNumber)} for more details.\n", "nv", "error")
                        if files == "zoomChangeTest" and (re.match(f"Zoom result after set is #\d+", line)):
                            if not re.match(f"Zoom result after set is #\d*:zoom:{fileNumber}", line):
                                zoomChangeError = True
                        log.write(line.strip() + "\n")
                    if len(error) > 0:
                        if files != "zoomChangeTest":
                            log.write("\nErrors:\n")
                        for error_line in error:
                            log.write("\n" + error_line.strip() + "\n")
                    if ispError:
                        log.write("\n*** ISP ERROR FOUND - VIDEO WAIT BUFFER LOOP ***\n")
                    if timeoutError:
                        log.write(f"\n*** TIMEOUT ERROR OCCURED. COMMAND EXECUTED FOR MORE THAN {timeout} SECONDS ***\n")
                    log.close()

                    if timeoutError or ispError:
                        break
                    
                except Exception as e:
                    # view.writeToOutput(e.__str__()))
                    view.writeToOutput("ERROR IN WRITING FILE. PLEASE CORRECT TO CONTINUE...", "nv", "error")


        return [not (ispError or timeoutError), not zoomChangeError, hardwareButtonResult]

def getMacAddress():
    """
        Parses MAC address from the view and validates the address.
    """

    global mac_address, save, end_program

    value = view.getMAC()
    view.writeToOutput("\nScanned value:", "v")
    view.writeToOutput("\n" + value + "\n", "v")
    try:
        if "," not in value:
            # entered MAC address without scan
            mac_address = MacAddress(value.upper())
            save = mac_address.getMAC().replace(":", "_")
            if not mac_address.validMac():
                raise InvalidMACError()
            if mac_address.getMAC() == "00:00:00:00:00:00":
                view.writeToOutput("\nZero MAC address.\n", "nv", "error")
                raise InvalidMACError()
        else:
            start = value.find(",") + 1
            end = start + 17
            mac_address = MacAddress(value[start:end].upper())
            if not mac_address.validMac():
                raise InvalidMACError()
            if mac_address.getMAC() == "00:00:00:00:00:00":
                view.writeToOutput("\nZero MAC address.\n", "nv", "error")
                raise InvalidMACError()
            save = mac_address.getMAC().replace(":", "_")
            view.writeToOutput(f"\nTarget MAC address is {mac_address.getMAC()}\n", "v")
    except Exception as e:
        view.writeToOutput("\n" + e.__str__() + "\n", "nv")
        view.writeToOutput("Invalid MAC address. Please try again.\n", "nv", "error")
        end_program = True

def getNetwork():
    """
        Retrieves IP address of network and subnet mask.
    """
    global network

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    netIP = s.getsockname()[0]
    s.close()

    # retrieve host ip address and net mask
   
    outf = os.popen('ipconfig')
    lines = outf.readlines()
    outf.close()
    count = 0
    for line in lines:
        if netIP in line:
            subnetAddr = lines[count+1]
            start = subnetAddr.find(":")+1
            strMask = subnetAddr[start:].strip()
            pureNetwork = "0.0.0.0/" + strMask
            subnet = IPv4Network(pureNetwork).prefixlen
            network = netIP + "/" + str(subnet)
            break
        count = count + 1

def checkValues():
    """ Verifies that values provided by user for the test are appropriate.
    """
    global end_program, zoomVal, loadVal

    # verify zoom value
    if test == "Image Capture" or test == "Manufacturer Test":
        try:
            if (390 <= int(zoomVal) <= 1700):
                zoomVal = int(zoomVal)
                view.writeToOutput(f"\nValue of zoom: \n{zoomVal}\n", "v")
            else:
                raise ValueError
        except:
            view.writeToOutput(f"\nInvalid zoom value. Please try again.\n", "nv", "error")
            end_program = True
    
    # verify load value
    if test == "Load Capture":
        try:
            view.writeToOutput(f"\nValue of load: \n{loadVal}\n", "v")
            loadVal = int(loadVal)
        except:
            view.writeToOutput(f"\nInvalid load value. Please try again.\n", "nv", "error")
            end_program = True

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.stat(fp).st_size

    return total_size

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

# CAMERA TESTS

def testImageCapture():

    global zoomVal

    """ Performs image capture test for Prospera camera. The test succeeds if an image is captured by the camera and copied 
    from the remote device to your device.
    """

    client = connect(ip, username, f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem")
    # LOAD, ZOOM VALUE, FILENAME, DATE, UPLOAD TIME, SIZE, UPLOAD SPEED, STATUS
    if zoomVal == "":
        zoomVal = 390
    stats = ["N/A", zoomVal, f"pic_{save}", "N/A", "N/A", "N/A", "N/A", "FAIL"]
    # capture camera image
    execute_commands(client, [f"export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; iesLens -c zoom -v {zoomVal}"], log=False)
    startIC = time.time()
    imageTest = execute_commands(client, [f"""export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; echo 0x40000> /sys/class/video4linux/video0/device/vinc0/vin_log_mask; ienso_image_capture -o /tmp/pic_{save} --overwrite; sleep 20"""])[0] # test value in 0th, 1st index
    endIC = time.time()
    view.writeToOutput(f"\nTime taken to capture image: {endIC-startIC} seconds\n", "nv")
    
    if imageTest:
        try:
            if os.path.exists(f"C:/Users/{user}/Desktop/Prospera/test_imgs/pic_{save}.jpeg"):
                os.remove(f"C:/Users/{user}/Desktop/Prospera/test_imgs/pic_{save}.jpeg")
            stats = scpCopy(client, f"../tmp/pic_{save}.jpeg", f"C:/Users/{user}/Desktop/Prospera/test_imgs")
            os.system(f"ssh -o StrictHostKeyChecking=no -i C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem {username}@{ip} rm ./../tmp/pic_{save}.jpeg")
            view.writeToOutput("\nIMAGE CAPTURE TEST SUCCESS.\n", "nv", "success")
            #read the image
            im = Image.open(pathlib.Path(rf"C:/Users/{user}/Desktop/Prospera/test_imgs/pic_{save}.jpeg"))
            #show image
            im.show()
        except Exception as e:
            view.writeToOutput("\n" + e.__str__() + "\n", "nv")
            view.writeToOutput(f"\nUnable to transfer file(s) from {hn}.\n", "nv")
            view.writeToOutput("\nIMAGE CAPTURE TEST FAILED.\n", "nv", "error")
            view.writeToOutput("\nUnable to retrieve image from Prospera Camera. Please try again.\n", "v")
    else:
        view.writeToOutput("\nIMAGE CAPTURE TEST FAILED. AN ISP ERROR HAS OCCURED.\n", "nv", "error")
    
    client.close()
    return stats

def testLoadCapture(load):
    """ Performs load capture test for Prospera camera. The test succeeds if all pictures specified by the parameter
    load have been captured and transferred to your device.

    :param load: The number of pictures to capture
    :type load: int
    """

    client = connect(ip, username, f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem")
    execute_commands(client, ["cd ./../tmp; mkdir load"], log=False)
    execute_commands(client, ["cd ./../mnt/UDISK; mkdir load"], log=False)
    loadTest = True
    if os.path.exists(f"C:/Users/{user}/Desktop/Prospera/log/load"):
        shutil.rmtree(f"C:/Users/{user}/Desktop/Prospera/log/load")
    # LOAD, ZOOM VALUE, FILENAME, DATE, UPLOAD TIME, SIZE, UPLOAD SPEED, STATUS
    stats = [load, zoomVal, "load", "N/A", "N/A", "N/A", "N/A", "FAIL"]
    startLC = time.time()
    for x in range(0,load):
        value = x+1
        execute_commands(client, [f"export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; iesLens -c zoom -v {zoomVal}"], log=False)
        imageTaken = execute_commands(client, [f"""export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; echo 0x40000> /sys/class/video4linux/video0/device/vinc0/vin_log_mask; ienso_image_capture -o /tmp/load/pic{value} --overwrite; sleep 20"""], "loadTest", value)[0]
        if not imageTaken:
            loadTest = False
            break
    endLC = time.time()
    view.writeToOutput(f"\nTime taken to capture images: {endLC-startLC} seconds\n", "nv")
    try:
        if os.path.exists(f"C:/Users/{user}/Desktop/Prospera/test_imgs/load"):
            shutil.rmtree(f"C:/Users/{user}/Desktop/Prospera/test_imgs/load")
        stats = scpCopy(client, f"../tmp/load", f"C:/Users/{user}/Desktop/Prospera/test_imgs", load=load)
        execute_commands(client, ["cd ./../tmp; rm -r load"], log=False)
    
    except:
        view.writeToOutput(f"\nUnable to transfer file(s) from {hn}.\n", "nv")
    
    if loadTest:
        view.writeToOutput("\nLOAD CAPTURE TEST SUCCESS\n", "nv", "success")
    else:
        view.writeToOutput("\nLOAD CAPTURE TEST FAILED\n", "nv", "error")
    
    client.close()
    return stats

def testZoomCapture():
    """ Performs the zoom capture test for the Prospera camera. The test will take a number of pictures, specified by the parameter
    loadVal, for zoom values of 390 and between 400 and 1700 (in increments of 100 units). The test succeeds if all images are captured 
    and transferred to your device. 
    """

    zoomTest = True
    # LOAD, ZOOM VALUE, FILENAME, DATE, UPLOAD TIME, SIZE, UPLOAD SPEED, STATUS
    stats = ["N/A", "N/A", "zoom", "N/A", "N/A", "N/A", "N/A", "FAIL"]
    client = connect(ip, username, f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem")
    startZC = time.time()
    execute_commands(client, ["cd ./../tmp; mkdir zoom"], log=False)
    execute_commands(client, [f"cd ./../tmp/zoom; mkdir zoom390"], log=False)
    execute_commands(client, ["cd ./../mnt/UDISK; mkdir zoom"], log=False)
    execute_commands(client, ["export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; iesLens -c zoom -v 390"], log=False)
    for i in range(0,5):
        execute_commands(client, [f"""export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; echo 0x40000> /sys/class/video4linux/video0/device/vinc0/vin_log_mask; ienso_image_capture -o /tmp/zoom/zoom390/pic390_{i} --overwrite {hdr}; sleep 30"""], "zoomTest", 390, True if i == 4 else False)
    for zoom in range(400, 1701, 100):
        execute_commands(client, [f"export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; iesLens -c zoom -v {zoom}"], log=False)
        execute_commands(client, [f"cd ./../tmp/zoom; mkdir zoom{zoom}"], log=False)
        for i in range(0,5):
            imageTaken = execute_commands(client, [f"""export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; echo 0x40000> /sys/class/video4linux/video0/device/vinc0/vin_log_mask; ienso_image_capture -o /tmp/zoom/zoom{zoom}/pic{zoom}_{i} --overwrite {hdr}; sleep 30"""], "zoomTest", zoom, True if i == 4 else False)[0]
            if not imageTaken:
                zoomTest = False
    endZC = time.time()
    timeTaken = endZC - startZC
    view.writeToOutput(f"\nTime taken to capture images: {timeTaken} seconds\n", "nv")
    try:                
        if os.path.exists(f"C:/Users/{user}/Desktop/Prospera/test_imgs/zoom"):
            shutil.rmtree(f"C:/Users/{user}/Desktop/Prospera/test_imgs/zoom")  
        os.makedirs(f"C:/Users/{user}/Desktop/Prospera/test_imgs/zoom")
        stats = scpCopy(client, f"../tmp/zoom/zoom390", f"C:/Users/{user}/Desktop/Prospera/test_imgs/zoom")        
        writeStatistics(test.lower().replace(" ", "_"), [mac_address.getMAC(), ip, connectionTime, test, stats[0], 390, stats[2], stats[3], stats[4], stats[5], stats[6], stats[7]])
        for i in range (400, 1701, 100):
            stats = scpCopy(client, f"../tmp/zoom/zoom{i}", f"C:/Users/{user}/Desktop/Prospera/test_imgs/zoom")
            writeStatistics(test.lower().replace(" ", "_"),[mac_address.getMAC(), ip, connectionTime, test, stats[0], i, stats[2], stats[3], stats[4], stats[5], stats[6], stats[7]])
        execute_commands(client, ["cd ./../tmp; rm -r zoom"], log=False)
    except Exception as e:
        view.writeToOutput("\n" + e.__str__() + "\n", "nv")
        writeStatistics(test.lower().replace(" ", "_"),[mac_address.getMAC(), ip, connectionTime, test, stats[0], "N/A", stats[2], stats[3], stats[4], stats[5], stats[6], stats[7]])
        view.writeToOutput(f"\nUnable to transfer file(s) from {hn}.\n", "nv")

    if zoomTest:
        view.writeToOutput("\nZOOM CAPTURE TEST SUCCESS\n", "nv", "success")
    else:
        view.writeToOutput("\nLOAD CAPTURE TEST FAILED\n", "nv", "error")

    if hdr != "":
       execute_commands(client, ["reboot"], log=False) 

    client.close()

def testReboot():
    """ Performs a test to verify the reboot feature of the Prospera camera. The test succeeds if the camera can be rebooted and reconnected
    to three times.
    """

    client = connect(ip, username, f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem")
    connected = False
    times = 10

    view.writeToOutput(f"\nAttempting to reconnect with {hn} {times} times...\n", "nv")
    for i in range(0,times):
        # reboot camera
        execute_commands(client, ["reboot"], log=False)
        start = time.time()
        connected = False
        while not connected:
            try:
                client = connect(ip, username, f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem")
                view.writeToOutput(f"\nEstablished connection {i+1}", "nv")
                view.writeToOutput("\nREBOOT TEST SUCCESS", "nv", "success")
                connected = True
            except Exception as e:
                #view.writeToOutput("\n" + e.__str__() + "\n", "nv")
                pass  
        end = time.time()
        reconnectionTime = end - start
        view.writeToOutput(f"\nReconnected to {hn} in {reconnectionTime} seconds.\n", "nv")

        # write statistics for reboot test 
        # message - mac address, ip address of camera, connection time, name of test, reboot attempt number, time to reconnect, filename/folder, test status
        writeStatistics("reboot", [mac_address.getMAC(), ip, connectionTime, test, i, reconnectionTime, "reboot", "PASS"], "reboot")
    client.close()
 
def testZoomChange():

    """ Performs a test to verify that the ProSpera camera can change its zoom position. The test succeeds if the current zoom position
    of the camera is the zoom value specified for each test.
    """

    client = connect(ip, username, f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem")
    zoomChangeTest = True

    # values to set for zoom
    test1 = [390, 500]
    test2 = [390, 900]
    test3 = [390, 1700]
    test4 = [500, 390]
    test5 = [900, 390]
    test6 = [1700, 390]
    test7 = [500, 800]
    oldZoom = 390

    execute_commands(client, [f"export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; time iesLens -c zoom -v 390"], log=False)
    try:
        for range in [test1, test2, test3, test4, test5, test6, test7]:
            if not zoomChangeTest:
                writeStatistics(test.lower().replace(" ", "_"), [mac_address.getMAC(), ip, connectionTime, test, "zoomChange", "N/A", "N/A", "N/A", "FAIL"], "zoomChange")
                break
            for position in range:

                # change zoom position
                zoomChangeTest = execute_commands(client, [f"export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; time iesLens -c zoom -v {position}"], "zoomChangeTest", position)[1]
                if not zoomChangeTest:
                    view.writeToOutput(f"\n{hn} did not change to zoom position {position}. Please try again.\n", "nv")
                    view.writeToOutput("\nZOOM CHANGE TEST FAILED.\n", "nv", "error")
                    break
                file = open(f"C:/Users/{user}/Desktop/Prospera/log/zoomChange/log_zc{position}.txt", 'r')
                content = file.readlines()
                elapsedTime = 0

                # get time for command to execute from log file
                for line in content:
                    if re.match("real\s*\d*m", line): 
                        elapsedTime = line[4:].strip()
                        file.close()
                        break

                # write statistics for zoom change test 
                # message - mac address, ip address of camera, connection time, name of test, filename/folder, old zoom value, new zoom value, time to change zoom position, test status
                writeStatistics(test.lower().replace(" ", "_"), [mac_address.getMAC(), ip, connectionTime, test, "zoomChange", oldZoom, position, elapsedTime, "PASS"], "zoomChange")
                oldZoom = position
        if zoomChangeTest:
            view.writeToOutput("\nZOOM CHANGE TEST SUCCESS.\n", "nv", "success")
            
    except Exception as e:
        view.writeToOutput(f"\nAn error occured while obtaining results for the zoom position test. Please try again.\n", "nv")
        view.writeToOutput("\nZOOM CHANGE TEST FAILED.\n", "nv", "error")

    client.close()

def testHardwareInterfaceButton():

    """ Perform a test to verifies the functionality of the button on the inner face of the ProSpera camera.
    If a button press yields a value of one (HIGH), the test is successful    
    """

    buttonTest = False

    # LOAD, ZOOM VALUE, FILENAME, DATE, UPLOAD TIME, SIZE, UPLOAD SPEED, STATUS
    stats = ["N/A", "N/A", "button", "N/A", "N/A", "N/A", "N/A", "FAIL"]

    client = connect(ip, username, f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem")

    # setting up button hardware
    execute_commands(client, [f"echo 364 > /sys/class/gpio/export; echo in > /sys/class/gpio/gpio364/direction; echo rising > /sys/class/gpio/gpio364/edge"], log=False)
    view.writeToOutput("\nChecking button state...\n", "nv")

    try:    
        result = execute_commands(client, ["cat /sys/class/gpio/gpio364/value"], log=False)[2]
        if int(result) == 0:
            view.writeToOutput("\nNo button press detected.\n", "nv")
            buttonTest = True
            
        if buttonTest:
            buttonTest = False
            wait = 3
            view.writeToOutput(f"\nPress and hold button for {wait} seconds.\n", "nv")
            start = time.time()
            while time.time() < start + wait:
                result = execute_commands(client, ["cat /sys/class/gpio/gpio364/value"], log=False)[2]
                if int(result) == 1:
                    view.writeToOutput("\nButton press detected.\n", "nv")
                    view.writeToOutput("\nHARDWARE BUTTON TEST SUCCESS\n", "nv", "success")
                    stats[3] = datetime.datetime.now().__str__()
                    stats[7] = "PASS"
                    buttonTest = True
                    break
            if not buttonTest:
                raise Exception
        else:
            view.writeToOutput("\nHARDWARE BUTTON TEST FAILED\n", "nv", "error")
    except Exception as e:
        view.writeToOutput("\nHARDWARE BUTTON TEST FAILED\n", "nv", "error")

    client.close()
    return stats

def testManufacture():

    """ Performs image capture test for Prospera camera. The test succeeds if an image is captured by the camera and copied 
    from the remote device to your device.
    """

    ## STILL NEEDS WORK

    client = connect(ip, username, f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem")
    # LOAD, ZOOM VALUE, FILENAME, DATE, UPLOAD TIME, SIZE, UPLOAD SPEED, STATUS
    stats = ["N/A", zoomVal, f"pic_{save}", "N/A", "N/A", "N/A", "N/A", "FAIL"]
    # capture camera image
    execute_commands(client, [f"export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; iesLens -c reset; iesLens -c zoom -v {zoomVal}"], log=False)
    startM = time.time()
    manufactureTest = execute_commands(client, [f"""export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; echo 0x40000> /sys/class/video4linux/video0/device/vinc0/vin_log_mask; ienso_image_capture -o /tmp/pic_{save} --overwrite --flash 1; sleep 20"""])[0] # test value in 0th, 1st index
    endM = time.time()
    view.writeToOutput(f"\nTime taken to capture image: {endM-startM} seconds\n", "nv")
    
    if manufactureTest:
        try:
            if os.path.exists(f"C:/Users/{user}/Desktop/Prospera/test_imgs/pic_{save}.jpeg"):
                os.remove(f"C:/Users/{user}/Desktop/Prospera/test_imgs/pic_{save}.jpeg")
            stats = scpCopy(client, f"../tmp/pic_{save}.jpeg", f"C:/Users/{user}/Desktop/Prospera/test_imgs")
            os.system(f"ssh -o StrictHostKeyChecking=no -i C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem {username}@{ip} rm ./../tmp/pic_{save}.jpeg")
            view.writeToOutput("\nMANUFACTURER TEST SUCCESS.\n", "nv", "success")
            #read the image
            im = Image.open(pathlib.Path(rf"C:/Users/{user}/Desktop/Prospera/test_imgs/pic_{save}.jpeg"))
            #show image
            im.show()
        except Exception as e:
            #view.writeToOutput("\n" + e.__str__() + "\n", "nv")
            view.writeToOutput(f"\nUnable to transfer file(s) from {hn}.\n", "nv")
            view.writeToOutput("\nMANUFACTURER TEST FAILED.\n", "nv", "error")
            view.writeToOutput("\nUnable to retrieve image from Prospera Camera. Please try again.\n", "v")
    else:
        view.writeToOutput("\nIMAGE CAPTURE TEST FAILED. AN ISP ERROR HAS OCCURED.\n", "nv", "error")
    
    client.close()
    return stats

def testCalibration():

    """ Performs test that calibrates that ProSpera camera and captures an image. If an image is captured and displayed, 
    the test is successful.
    """

    # LOAD, ZOOM VALUE, FILENAME, DATE, UPLOAD TIME, SIZE, UPLOAD SPEED, STATUS
    client = connect(ip, username, f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem")
    startC = time.time()

    # SLEEP FOR TEN SECONDS AFTER CAMERA CALIBRATION
    execute_commands(client, [f"export LD_LIBRARY_PATH=/usr/lib/eyesee-mpp; iesLens -c reset; iesLens -c cali; sleep 10"], files="calibrationTest")
    execute_commands(client, ["reboot"], log=False)
    endC = time.time()
    view.writeToOutput(f"\nTime taken to calibrate: {endC-startC} seconds\n", "nv")
    client.close()
    view.writeToOutput(f"\nPerforming Image Capture test...\n", "nv")
    time.sleep(50)
    stats = testImageCapture()
    stats[2] = "calibration"
    return stats

def testWifiBoard():

    """ Performs a test to retrieve information about the ProSpera camera's connection to it's connected network.
    """

    client = connect(ip, username, f"C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem")

    # SIGNAL POWER, STATUS
    stats = ["N/A", "FAIL"]
    startWB = time.time()
    os.system(f"scp -i C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem C:/Users/{user}/Desktop/Prospera/valley.ico {username}@{ip}:/mnt/UDISK")
    execute_commands(client, ["ssh 172.16.1.1 iw dev wlan0 station dump"], files="wifiBoardTest")
    try:
        file = open(f"C:/Users/{user}/Desktop/Prospera/log/wifiBoard/info_wfboard.txt", "r")
        output = file.readlines()
        found = False
        for line in output:
            if "signal avg:" in line:
                found = True
                items = line.split()
                stats[0] = items[2]
                stats[1] = "PASS"
                view.writeToOutput(f"\nThe average received signal power from the Prospera camera is {items[2]} dBm.\n", "nv")
                view.writeToOutput(f"\nWI-FI BOARD TEST SUCCESS\n", "nv", "success")
                break
        if not found:
            raise Exception
    except Exception as e:
        view.writeToOutput(f"\nAn error has occurred:\n" + e.__str__(), "nv", "error")
        view.writeToOutput(f"\nWI-FI BOARD TEST FAILED\n", "nv", "error")
    endWB = time.time()
    view.writeToOutput(f"\nTime taken to get signal power: {endWB-startWB} seconds\n", "nv")
    os.system(f"ssh -o StrictHostKeyChecking=no -i C:/Users/{user}/Desktop/Prospera/private_keys/prospera-dev.pem {username}@{ip} rm ./../mnt/UDISK/valley.ico")

    # write statistics for wifi statistics test
    # message - mac address, ip address of camera, connection time, name of test, average signal power, test status
    writeStatistics("wifiBoard", [mac_address.getMAC(), ip, connectionTime, test, stats[0], stats[1]], "wifiBoard")

# MAIN PROGRAM

# create view and set cursor
view = ProsperaView()
view.enableEntry()
view.display()
