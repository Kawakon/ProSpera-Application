import threading
import sys

class thread_with_trace(threading.Thread):

    """ Creates instance of threading.Thread that can be 
    destroyed with the kill() method
    """

    def __init__(self, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.killed = False
    
    def start(self):
        self.__run_backup = self.run
        self.run = self.__run     
        threading.Thread.start(self)
    
    def __run(self):
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup
    
    def globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.localtrace
        else:
            return None
    
    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == 'line' or event == 'call' or event == 'return':
                raise SystemExit()
        return self.localtrace
    
    def kill(self):
        self.killed = True