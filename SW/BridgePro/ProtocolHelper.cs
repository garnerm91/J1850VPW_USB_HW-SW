// ProtocolHelper.cs
// Builds and parses the STX/ETX framed serial protocol
// that the STM32 firmware expects.
//
// Frame format:  [ STX | LEN | CMD | data bytes... | ETX ]
//   STX = 0x02  (start of frame)
//   LEN = CMD (1 byte) + number of data bytes (NOT including STX, LEN, or ETX)
//   CMD = command byte
//   ETX = 0x03  (end of frame)
//
// ACK  response from STM32: [ 0x02 | 0x01 | 0x06 | 0x03 ] (LEN is 1 for the ACK byte)
// NACK response from STM32: [ 0x02 | 0x01 | 0x15 | 0x03 ] (LEN is 1 for the NACK byte)
// RX frame from STM32:      [ 0x02 | LEN  | data...| 0x03 ]
// ID Response from STM32:   [ 0x02 | LEN  | 0x06 | 0x4A |0x03 ] (ack with data payload "J" = 0x4A) J for J1850VPW

using System;

namespace J1850Tool
{
    public static class ProtocolHelper
    {
        // Protocol constants — must match firmware protocol.h
        public const byte STX = 0x02;
        public const byte ETX = 0x03;
        public const byte ACK = 0x06;
        public const byte NACK = 0x15;

        // Command bytes — must match firmware protocol.h
        public const byte CMD_RX_MODE = 0x01;
        public const byte CMD_SEND = 0x02;
        public const byte CMD_IDN = 0x4A;

        /// <summary>
        /// Build a complete STX/ETX frame ready to send to the STM32.
        /// </summary>
        /// <param name="cmd">Command byte (CMD_RX_MODE or CMD_SEND)</param>
        /// <param name="data">Data payload bytes</param>
        /// <returns>Complete frame as byte array</returns>
        public static byte[] BuildFrame(byte cmd, byte[] data)
        {
            int dataLen = data?.Length ?? 0;

            // LEN is CMD (1 byte) + the data length
            int lenField = dataLen + 1;

            // Total frame = STX + LEN + CMD + data + ETX (which is dataLen + 4 bytes total)
            byte[] frame = new byte[dataLen + 4];
            frame[0] = STX;
            frame[1] = (byte)lenField;  // LEN field now accounts for CMD
            frame[2] = cmd;

            // Copy data bytes into the frame starting at index 3
            if (data != null)
            {
                Buffer.BlockCopy(data, 0, frame, 3, dataLen);
            }

            frame[frame.Length - 1] = ETX;

            return frame;
        }

        /// <summary>
        /// Build the RX Mode command frame.
        /// </summary>
        /// <param name="enable">true = enable RX forwarding, false = disable</param>
        public static byte[] BuildRxModeFrame(bool enable)
        {
            return BuildFrame(CMD_RX_MODE, new byte[] { enable ? (byte)0x01 : (byte)0x00 });
        }

        /// <summary>
        /// Build a Send command frame with the given J1850 data bytes.
        /// The STM32 firmware appends the CRC automatically before putting
        /// the frame on the J1850 bus — do NOT include CRC here.
        /// </summary>
        public static byte[] BuildSendFrame(byte[] j1850Data)
        {
            return BuildFrame(CMD_SEND, j1850Data);
        }

        /// <summary>
        /// Format a byte array as a readable hex string, e.g. "68 6A F1 01 00"
        /// </summary>
        public static string ToHexString(byte[] data)
        {
            if (data == null || data.Length == 0) return "";
            return BitConverter.ToString(data).Replace("-", " ");
        }

        /// <summary>
        /// Format a byte array as hex starting from a given offset.
        /// e.g. ToHexString(data, 1) skips the first byte.
        /// </summary>
        public static string ToHexString(byte[] data, int startIndex)
        {
            if (data == null || startIndex >= data.Length) return "";
            byte[] slice = new byte[data.Length - startIndex];
            Array.Copy(data, startIndex, slice, 0, slice.Length);
            return BitConverter.ToString(slice).Replace("-", " ");
        }

        /// <summary>
        /// Parse a hex string like "68 6A F1" or "686AF1" into a byte array.
        /// Returns null if the string is invalid.
        /// </summary>
        public static byte[] ParseHexString(string hex)
        {
            if (string.IsNullOrWhiteSpace(hex)) return null;

            hex = hex.Replace(" ", "").Replace(",", "").Replace("0x", "").Replace("0X", "");

            if (hex.Length % 2 != 0) return null;

            try
            {
                byte[] result = new byte[hex.Length / 2];
                for (int i = 0; i < result.Length; i++)
                    result[i] = Convert.ToByte(hex.Substring(i * 2, 2), 16);
                return result;
            }
            catch
            {
                return null;
            }
        }
    }
}






















