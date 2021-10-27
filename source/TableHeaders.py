class TableHeaders:
    def __init__(self, type:str) -> None:
        self.header_template = ''
        self.template = ''
        self.table_headers = []

        if type == "default":
            self.header_template = '{:<30}  {:<30}  {:<45}  {:<30}  {:<30}  {:<30}  {:<30}  {:<30}  {:<30}  {:<30}  {:<30}  {:<30}'
            self.template = '{:<30}  {:<30}  {:>45}  {:<30}  {:>30}  {:<30}  {:<30}  {:<30}  {:>30}  {:>30}  {:>30}  {:<30}'
            self.table_headers = ["MAC Address", "IP Address", "Established Connection Time (seconds)", "Test", "Load (Pictures)", "Zoom", "Filename/Folder", "Date", "Upload Time (seconds)", "Size (KBs)", "Upload Speed (KB/s)", "Test Status"]
        elif type == "reboot":
            self.header_template = '{:<30}  {:<30}  {:<45}  {:<30}  {:<30}  {:<30}  {:<30}  {:<30}'
            self.template = '{:<30}  {:<30}  {:>45}  {:<30}  {:>30}  {:<30}  {:<30}  {:<30}'
            self.table_headers = ["MAC Address", "IP Address", "Established Connection Time (seconds)", "Test", "Attempt", "Reconnection Time (seconds)", "Filename/Folder", "Test Status"]
        elif type == "zoomChange":
            self.header_template = '{:<30}  {:<30}  {:<45}  {:<30}  {:<30}  {:<30}  {:<30}  {:<45}  {:<30}'
            self.template = '{:<30}  {:<30}  {:>45}  {:<30}  {:>30}  {:>30}  {:>30}  {:>45}  {:<30}'
            self.table_headers = ["MAC Address", "IP Address", "Established Connection Time (seconds)", "Test", "Filename/Folder", "Old Zoom Value", "New Zoom Value", "Zoom Change Time", "Test Status"]
        elif type == "wifiBoard":
            self.header_template = '{:<30}  {:<30}  {:<45}  {:<30}  {:<30}  {:<30}'
            self.template = '{:<30}  {:<30}  {:>45}  {:<30}  {:>30}  {:<30}'
            self.table_headers = ["MAC Address", "IP Address", "Established Connection Time (seconds)", "Test", "Signal Power (dBm)", "Test Status"]
        
    def getHeaderTemplate(self) -> str:
        return self.header_template

    def getTemplate(self) -> str:
        return self.template
    
    def getTableHeaders(self) -> list[str]:
        return self.table_headers

    