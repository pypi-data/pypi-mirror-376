import asyncio
import threading
import ssl
import websocket
import websockets
from polypacket.transport.Transport import Transport


class WebsocketTransport(Transport):
    def __init__(self, uri, callback=None, allow_insecure=True):
        super().__init__(callback)
        self.uri = uri
        self.allow_insecure = allow_insecure
        self.ws = None
        self.opened = False
        self.should_stop = False
        self.server = None
        self.current_websocket = None
        self.loop = None
        self.mode = 'client'
        self.port = None
        self.secure = False
        
    def configure_server(self, port, secure=False):
        self.mode = 'server'
        self.port = port
        self.secure = secure
        
    def __del__(self):
        self.close()
        
    def close(self):
        self.should_stop = True
        if self.mode == 'client' and self.ws:
            self.ws.close()
        elif self.mode == 'server' and self.server:
            if self.loop and not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(self._close_server(), self.loop)
            
    async def _close_server(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
    def connect(self):
        try:
            if self.mode == 'client':
                print(f" WebSocket client trying {self.uri}")
                
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
            else:
                print(f" WebSocket server starting on port {self.port}")
                
            # Start the connection in a separate thread
            self.start()
            
        except Exception as e:
            print(f" WebSocket Exception: {str(e)}")
            
    def send(self, data):
        try:
            if self.mode == 'client' and self.ws and self.opened:
                self.ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
            elif self.mode == 'server' and self.current_websocket and self.opened:
                if self.loop and not self.loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        self.current_websocket.send(data), self.loop
                    )
        except Exception as e:
            print(f" WebSocket Send Exception: {str(e)}")
            self.opened = False
            
    def run(self):
        try:
            if self.mode == 'client':
                sslopt = None
                if self.uri.startswith('wss://') and self.allow_insecure:
                    sslopt = {"cert_reqs": ssl.CERT_NONE}
                    
                self.ws.run_forever(sslopt=sslopt)
            else:
                # Server mode
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                self.loop.run_until_complete(self._start_server())
        except Exception as e:
            print(f" WebSocket Run Exception: {str(e)}")
            
    async def _start_server(self):
        try:
            ssl_context = None
            if self.secure:
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                # For development/testing - you'd want proper certificates in production
                if self.allow_insecure:
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
            self.server = await websockets.serve(
                self._handle_client,
                "0.0.0.0",
                self.port,
                ssl=ssl_context
            )
            print(f" WebSocket server started on port {self.port}")
            self.opened = True
            await self.server.wait_closed()
        except Exception as e:
            print(f" WebSocket Server Exception: {str(e)}")
            
    async def _handle_client(self, websocket, path):
        try:
            print(" WebSocket client connected")
            self.current_websocket = websocket
            async for message in websocket:
                if self.callback and not self.should_stop:
                    self.callback(message)
        except websockets.exceptions.ConnectionClosed:
            print(" WebSocket client disconnected")
        except Exception as e:
            print(f" WebSocket Client Handler Exception: {str(e)}")
        finally:
            self.current_websocket = None
            self.opened = False
            
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

    [ws://host:port/path] for insecure WebSocket client connection
    [wss://host:port/path] for secure WebSocket client connection
    [ws:port] for insecure WebSocket server on specified port
    [wss:port] for secure WebSocket server on specified port
    
Examples:
    Client connections:
        ws://localhost:8080/websocket
        wss://example.com:443/api/websocket
    
    Server mode:
        ws:8080
        wss:8443
"""


def parseWebsocketConnectionString(connString):
    try:
        if connString.startswith('ws://') or connString.startswith('wss://'):
            return {'uri': connString, 'mode': 'client'}
        elif connString.startswith('ws:') and not connString.startswith('ws://'):
            # Server mode: ws:port
            port_str = connString[3:]
            try:
                port = int(port_str)
                return {'port': port, 'mode': 'server', 'secure': False}
            except ValueError:
                return None
        elif connString.startswith('wss:') and not connString.startswith('wss://'):
            # Secure server mode: wss:port
            port_str = connString[4:]
            try:
                port = int(port_str)
                return {'port': port, 'mode': 'server', 'secure': True}
            except ValueError:
                return None
        else:
            return None
        
    except Exception:
        return None