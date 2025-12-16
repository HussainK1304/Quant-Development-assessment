import asyncio
import websockets
import json
from data_handler import resample_and_store
from collections import defaultdict 

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/!miniTicker@arr"
SYMBOLS = ["btcusdt", "ethusdt"] 


TICK_BUFFER = defaultdict(list) 
RESAMPLE_TIMEFRAME = '1s'

async def receive_and_process_data():
    """Connects to Binance WS and processes the data asynchronously."""
    async with websockets.connect(BINANCE_WS_URL) as websocket:
        print(f"Connected to Binance WebSocket: {BINANCE_WS_URL}")

        while True:
            try:
                data = await websocket.recv()
                message = json.loads(data)
                
                if isinstance(message, list):
                    for tick in message:
                        symbol = tick.get('s', '').lower() 
                        
                        if symbol in SYMBOLS: 
                            
                            raw_tick = {
                                'time': tick.get('E'),
                                'price': float(tick.get('c')),
                                'qty': float(tick.get('v')),
                            }
                            
                            TICK_BUFFER[symbol].append(raw_tick)
                            
                
                symbols_to_clear = []
                for symbol_key, buffer in TICK_BUFFER.items():
                    if len(buffer) >= 50:
                        
                        resample_and_store(buffer, RESAMPLE_TIMEFRAME, symbol_key.upper()) 
                        symbols_to_clear.append(symbol_key)
                        
                
                for symbol_key in symbols_to_clear:
                    TICK_BUFFER[symbol_key].clear()

            except websockets.ConnectionClosed:
                print("Connection closed, retrying...")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Error processing data: {e}")
                await asyncio.sleep(1)


def start_ws_client():
    asyncio.run(receive_and_process_data())