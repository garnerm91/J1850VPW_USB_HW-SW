// SerialManager.cs
// Handles all COM port communication.
// Runs a background receive thread that feeds incoming bytes into the
// STX/ETX parser and fires an event when a complete frame arrives.

using System;
using System.IO.Ports;
using System.Threading;

namespace J1850Tool
{
    /// <summary>
    /// Fired when a complete, valid frame is received from the STM32.
    /// frameType is "ACK", "NACK", or "RX" (a J1850 frame forwarded by the firmware).
    /// data contains the payload bytes (empty for ACK/NACK).
    /// </summary>
    public class FrameReceivedEventArgs : EventArgs
    {
        public string FrameType { get; }   // "ACK", "NACK", or "RX"
        public byte[] Data { get; }   // payload bytes

        public FrameReceivedEventArgs(string frameType, byte[] data)
        {
            FrameType = frameType;
            Data = data ?? Array.Empty<byte>();
        }
    }

    public class SerialManager : IDisposable
    {
        // ---- Events ------------------------------------------------
        // Fired on a background thread — use Invoke() to update the UI
        public event EventHandler<FrameReceivedEventArgs> FrameReceived;
        public event EventHandler<string> LogMessage;

        // ---- State -------------------------------------------------
        private SerialPort _port;
        private Thread _rxThread;
        private volatile bool _running;

        // ---- Parser state ------------------------------------------
        private enum ParseState { WaitSTX, WaitLEN, WaitData, WaitETX }
        private ParseState _parseState = ParseState.WaitSTX;
        private byte _frameLen;
        private int _dataIndex;
        private byte[] _frameData;
        private const byte J1850_HEADER_BYTE = 0x10;

        // ---- Public API --------------------------------------------

        public bool IsConnected => _port?.IsOpen ?? false;

        /// <summary>
        /// When true, the last byte (CRC) is stripped from incoming J1850 RX frames
        /// before they are passed to the UI. Bind this to your checkBox2.Checked.
        /// </summary>
        public bool TrimCrc { get; set; } = false;

        public bool Connect(string portName, int baudRate = 115200)
        {
            try
            {
                _port = new SerialPort(portName, baudRate, Parity.None, 8, StopBits.One)
                {
                    ReadTimeout = 500,
                    WriteTimeout = 500
                };
                _port.Open();

                _running = true;
                _rxThread = new Thread(ReceiveLoop) { IsBackground = true, Name = "J1850-RX" };
                _rxThread.Start();

                Log($"Connected to {portName} at {baudRate} baud.");
                return true;
            }
            catch (Exception ex)
            {
                Log($"Connect failed: {ex.Message}");
                return false;
            }
        }

        public void Disconnect()
        {
            _running = false;

            try { _port?.Close(); } catch { }
            try { _rxThread?.Join(500); } catch { }

            _port = null;
            _rxThread = null;

            ResetParser();
            Log("Disconnected.");
        }

        public bool SendFrame(byte[] frame)
        {
            if (!IsConnected)
            {
                Log("Not connected.");
                return false;
            }
            try
            {
                _port.Write(frame, 0, frame.Length);
                Log($"TX: {ProtocolHelper.ToHexString(frame)}");
                return true;
            }
            catch (Exception ex)
            {
                Log($"Send failed: {ex.Message}");
                return false;
            }
        }

        public static string[] GetAvailablePorts()
        {
            return SerialPort.GetPortNames();
        }

        // ---- Background receive loop -------------------------------

        private void ReceiveLoop()
        {
            while (_running)
            {
                try
                {
                    int b = _port.ReadByte();
                    if (b >= 0)
                        ParseByte((byte)b);
                }
                catch (TimeoutException)
                {
                    // Normal — no data within ReadTimeout, loop again
                }
                catch (Exception ex)
                {
                    if (_running)
                        Log($"RX error: {ex.Message}");
                    break;
                }
            }
        }

        // ---- STX/ETX parser ----------------------------------------
        // Firmware send_to_serial() produces two frame types:
        //
        // ACK/NACK:   [ STX | 0x01 | 0x06 or 0x15          | ETX ]
        // J1850 RX:   [ STX | LEN  | 0x10 | payload bytes... | ETX ]


        private enum CmdType { Unknown, AckNack, J1850Rx }
        private CmdType _frameCmd;

        private void ParseByte(byte b)
        {
            switch (_parseState)
            {
                case ParseState.WaitSTX:
                    if (b == ProtocolHelper.STX)
                        _parseState = ParseState.WaitLEN;
                    break;

                case ParseState.WaitLEN:
                    _frameLen = b;
                    _dataIndex = 0;
                    _frameCmd = CmdType.Unknown;
                    // LEN includes the CMD byte, so actual payload = LEN - 1
                    // Allocate for the payload only (CMD byte handled in WaitData first pass)
                    int payloadLen = Math.Max(0, _frameLen - 1);
                    _frameData = new byte[payloadLen == 0 ? 1 : payloadLen];
                    _parseState = ParseState.WaitData;
                    break;

                case ParseState.WaitData:
                    // First byte after LEN is always the CMD byte
                    if (_frameCmd == CmdType.Unknown)
                    {
                        if (b == ProtocolHelper.ACK || b == ProtocolHelper.NACK)
                        {
                            // ACK/NACK — store the byte and wait for ETX
                            _frameCmd = CmdType.AckNack;
                            _frameData[0] = b;
                            _dataIndex = 1;
                        }
                        else if (b == J1850_HEADER_BYTE)
                        {
                            // J1850 RX frame — 0x10 consumed, now collect payload
                            _frameCmd = CmdType.J1850Rx;
                            _dataIndex = 0;
                        }
                        else
                        {
                            // Unknown CMD — bail out
                            Log($"Unknown CMD byte: 0x{b:X2} — frame dropped.");
                            ResetParser();
                        }

                        // Check if there is no payload (LEN was 1, only a CMD byte)
                        if (_frameLen <= 1)
                            _parseState = ParseState.WaitETX;

                        break;
                    }

                    // Collect payload bytes
                    if (_dataIndex < _frameData.Length)
                        _frameData[_dataIndex++] = b;

                    if (_dataIndex >= _frameData.Length)
                        _parseState = ParseState.WaitETX;
                    break;

                case ParseState.WaitETX:
                    if (b == ProtocolHelper.ETX)
                        DispatchFrame();
                    else
                        Log($"Bad ETX: 0x{b:X2} — frame dropped.");

                    ResetParser();
                    break;
            }
        }

        private void DispatchFrame()
        {
            switch (_frameCmd)
            {
                case CmdType.AckNack:
                    string type = _frameData[0] == ProtocolHelper.ACK ? "ACK" : "NACK";
                    // Check for identify response: ACK followed by device ID byte 0x4A
                    if (_frameData[0] == ProtocolHelper.ACK && _frameData.Length > 1 && _frameData[1] == 0x4A)
                        type = "IDENTIFY";
                    FrameReceived?.Invoke(this, new FrameReceivedEventArgs(type, _frameData));
                    break;

                case CmdType.J1850Rx:
                    // _frameData contains the J1850 payload with 0x10 already stripped.
                    // If TrimCrc is true, remove the last byte (the J1850 CRC).
                    if (TrimCrc && _frameData.Length > 1)
                    {
                        byte[] stripped = new byte[_frameData.Length - 1];
                        Array.Copy(_frameData, 0, stripped, 0, stripped.Length);
                        FrameReceived?.Invoke(this, new FrameReceivedEventArgs("RX", stripped));
                    }
                    else if (TrimCrc && _frameData.Length <= 1)
                    {
                        Log("RX frame too short after CRC strip — ignored.");
                    }
                    else
                    {
                        // TrimCrc is off — pass the full payload including CRC
                        FrameReceived?.Invoke(this, new FrameReceivedEventArgs("RX", _frameData));
                    }
                    break;

                default:
                    Log("Frame with unknown CMD dropped.");
                    break;
            }
        }

        private void ResetParser()
        {
            _parseState = ParseState.WaitSTX;
            _frameLen = 0;
            _dataIndex = 0;
            _frameData = null;
            _frameCmd = CmdType.Unknown;
        }

        private void Log(string msg)
        {
            LogMessage?.Invoke(this, msg);
        }

        // ---- IDisposable -------------------------------------------
        public void Dispose()
        {
            Disconnect();
            _port?.Dispose();
        }
    }
}
