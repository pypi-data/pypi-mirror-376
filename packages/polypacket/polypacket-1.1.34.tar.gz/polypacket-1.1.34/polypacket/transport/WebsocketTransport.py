import asyncio
import threading
import ssl
import websocket
from polypacket.transport.Transport import Transport


class WebsocketTransport(Transport):
    def __init__(self, uri, callback=None, allow_insecure=True):
        super().__init__(callback)
        self.uri = uri
        self.allow_insecure = allow_insecure
        self.ws = None
        self.opened = False
        self.should_stop = False
        
    def __del__(self):
        self.close()
        
    def close(self):
        self.should_stop = True
        if self.ws:
            self.ws.close()
            
    def connect(self):
        try:
            print(f" WebSocket trying {self.uri}")
            
            # Configure SSL options for insecure connections
            sslopt = None
            if self.uri.startswith('wss://') and self.allow_insecure:
                sslopt = {"cert_reqs": ssl.CERT_NONE}
                
            self.ws = websocket.WebSocketApp(
                self.uri,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Start the connection in a separate thread
            self.start()
            
        except Exception as e:
            print(f" WebSocket Exception: {str(e)}")
            
    def send(self, data):
        try:
            if self.ws and self.opened:
                self.ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            print(f" WebSocket Send Exception: {str(e)}")
            self.opened = False
            
    def run(self):
        try:
            sslopt = None
            if self.uri.startswith('wss://') and self.allow_insecure:
                sslopt = {"cert_reqs": ssl.CERT_NONE}
                
            self.ws.run_forever(sslopt=sslopt)
        except Exception as e:
            print(f" WebSocket Run Exception: {str(e)}")
            
    def _on_open(self, ws):
        print(" WebSocket Connected")
        self.opened = True
        
    def _on_message(self, ws, message):
        if self.callback and not self.should_stop:
            self.callback(message)
            
    def _on_error(self, ws, error):
        print(f" WebSocket Error: {str(error)}")
        self.opened = False
        
    def _on_close(self, ws, close_status_code, close_msg):
        print(" WebSocket Disconnected")
        self.opened = False


websocketConnectionHelp = """
Invalid WebSocket connection string. Options:

    [ws://host:port/path] for insecure WebSocket connection
    [wss://host:port/path] for secure WebSocket connection
    
Examples:
    ws://localhost:8080/websocket
    wss://example.com:443/api/websocket
"""


def parseWebsocketConnectionString(connString):
    try:
        if not (connString.startswith('ws://') or connString.startswith('wss://')):
            return None
            
        return {'uri': connString}
        
    except Exception:
        return None