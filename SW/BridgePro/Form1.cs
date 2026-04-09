using J1850Tool;
using Microsoft.VisualBasic.Logging;

namespace BridgePro
{
    public partial class Form1 : Form
    {
        private bool _isUpdating = false;
        private bool _querying = false;
        private readonly SerialManager _serial = new SerialManager();
        private CheckBox[] boxes;
        // ---- Playback state ----------------------------------------
        private List<(byte[] Data, int DelayMs)> _playbackFrames = new List<(byte[], int)>();
        private CancellationTokenSource _playbackCts = null;
        private bool _playbackRunning = false;
        public Form1()
        {
            InitializeComponent();
            _serial.LogMessage += (s, msg) => Invoke(new Action(() => AppendLog(msg, Color.Gray)));
            _serial.FrameReceived += (s, e) => Invoke(new Action(() => OnFrameReceived(e)));
            boxes = new CheckBox[] { by0, by1, by2, by3, by4, by5, by6, by7 };
        }

        private void button1_Click(object sender, EventArgs e)
        {
            string input = textBox1.Text.Trim();

            if (string.IsNullOrWhiteSpace(input))
            {
                AppendLog("Please enter hex bytes to send.", Color.Orange);
                return;
            }
            byte[] j1850Data = ProtocolHelper.ParseHexString(input);

            if (j1850Data == null || j1850Data.Length == 0)
            {
                AppendLog("Invalid hex — use format: 6C FE F0 28 00 F0", Color.Orange);
                return;
            }

            if (j1850Data.Length > 11)
            {
                AppendLog($"Too many bytes ({j1850Data.Length}) — maximum J1850 payload is 11 bytes.", Color.Orange);
                return;
            }

            // BuildSendFrame wraps the data in [ STX | LEN | CMD_SEND | data... | ETX ]
            // where LEN = data.Length + 1 (accounting for the CMD byte per the updated ProtocolHelper)
            byte[] frame = ProtocolHelper.BuildSendFrame(j1850Data);

            if (_serial.SendFrame(frame))
                AppendLog($"→ Sent: {ProtocolHelper.ToHexString(j1850Data)}", Color.LightGreen);
        }
        private void Form1_Load(object sender, EventArgs e)
        {
            RefreshPorts();
        }
        private void RefreshPorts()
        {
            comboBox1.Items.Clear();
            foreach (string p in SerialManager.GetAvailablePorts())
                comboBox1.Items.Add(p);

            if (comboBox1.Items.Count > 0)
                comboBox1.SelectedIndex = 0;
        }

        private void button3_Click(object sender, EventArgs e)
        {
            RefreshPorts();
        }
        private void AppendLog(string msg, Color color)
        {
            string line = $"[{DateTime.Now:HH:mm:ss.fff}] {msg}\n";

            _log.SelectionStart = _log.TextLength;
            _log.SelectionLength = 0;
            _log.SelectionColor = color;
            _log.AppendText(line);
            _log.ScrollToCaret();
        }

        private void button4_Click(object sender, EventArgs e)
        {
            if (_serial.IsConnected)
            {
                // Already connected — disconnect
                _serial.Disconnect();
                button4.Text = "Connect";
                comboBox1.Enabled = true;
                button3.Enabled = true;

            }
            else
            {
                // Not connected — try to connect
                if (comboBox1.SelectedItem == null)
                {
                    AppendLog("Please select a COM port.", Color.Orange);
                    return;
                }
                string port = comboBox1.SelectedItem.ToString();
                if (_serial.Connect(port))
                {
                    button4.Text = "Disconnect";
                    comboBox1.Enabled = false;
                    button3.Enabled = false;
                    byte[] frame = ProtocolHelper.BuildFrame(0x49, null);
                    _serial.SendFrame(frame);
                }
            }
        }

        private void _chkRxEnable_CheckedChanged(object sender, EventArgs e)
        {
            bool enable = _chkRxEnable.Checked;
            byte[] frame = ProtocolHelper.BuildRxModeFrame(enable);
            _serial.SendFrame(frame);
            AppendLog($"RX mode {(enable ? "ENABLED" : "DISABLED")} sent.", Color.CornflowerBlue);
        }
        // ---- Incoming frame handler --------------------------------

        private void OnFrameReceived(FrameReceivedEventArgs e)
        {
            switch (e.FrameType)
            {
                case "ACK":
                    AppendLog(" ACK", Color.LimeGreen);
                    break;

                case "NACK":
                    AppendLog(" NACK", Color.OrangeRed);
                    break;

                case "IDENTIFY":
                    AppendLog(" Device identified: 0x4A", Color.LimeGreen);
                    break;

                case "RX":
                    AppendLog($" RX: {ProtocolHelper.ToHexString(e.Data)}", Color.Cyan);
                    TryParseDataResponse(e.Data);
                    break;
            }
        }

        private void comboBox2_SelectedIndexChanged(object sender, EventArgs e)
        {

        }

        private void button2_Click(object sender, EventArgs e)
        {
            _log.Clear();
        }

        private void button5_Click(object sender, EventArgs e)
        {
            textBox1.Text = "6C FE F0 28 00 F0";
            button1_Click(sender, e);
        }

        private void button6_Click(object sender, EventArgs e)
        {
            textBox1.Text = "99 01 43 41 4C 31";
            button1_Click(sender, e);
        }

        private void checkBox2_CheckedChanged(object sender, EventArgs e)
        {
            _serial.TrimCrc = checkBox2.Checked;
            AppendLog($"CRC trim {(checkBox2.Checked ? "ON" : "OFF")}", Color.Gray);
        }
        /// <summary>
        /// Parses a data response frame and routes the value to the correct text box.
        ///
        /// Frame layout after 0x10 and CRC are stripped:
        ///   byte[0]     = data point ID
        ///   byte[1..4]  = value, little-endian (float or uint32 depending on ID)
        /// </summary>
        private void TryParseDataResponse(byte[] data)
        {
            // Must be exactly 5 bytes: 1 ID + 4 value bytes
            if (data == null || data.Length != 5 || _querying == false)

                return;
            _querying = false;
            byte dataPointId = data[0];
            string display;

            switch (dataPointId)
            {
                // ---- Float responses (IEEE-754 little-endian) ----------
                case 0x02:
                    display = BitConverter.ToSingle(data, 1).ToString("F4");
                    textBox2.Text = display;
                    break;

                case 0x03:
                    display = BitConverter.ToSingle(data, 1).ToString("F4");
                    textBox3.Text = display;
                    break;

                case 0x05:
                    display = BitConverter.ToSingle(data, 1).ToString("F4");
                    textBox4.Text = display;
                    break;
                // ---- UInt32 responses (little-endian) ------------------
                case 0x04:
                    uint sn = BitConverter.ToUInt32(data, 1);
                    display = sn.ToString();
                    textBox5.Text = display;
                    break;

                case 0x06:
                    uint val6 = BitConverter.ToUInt32(data, 1);
                    display = val6.ToString();
                    textBox6.Text = display;
                    break;
                case 0x07:
                    uint val7 = BitConverter.ToUInt32(data, 1);
                    display = val7.ToString();
                    textBox7.Text = display;
                    break;

                default:
                    display = ProtocolHelper.ToHexString(data, 1);   // raw hex for unknowns
                    break;
            }

            AppendLog($" Data[0x{dataPointId:X2}] = {display}", Color.Yellow);
        }

        private void read1_Click(object sender, EventArgs e)
        {
            textBox1.Text = "98 02";
            _querying = true;
            button1_Click(sender, e);
        }

        private void button7_Click(object sender, EventArgs e)
        {
            textBox1.Text = "98 03";
            _querying = true;
            button1_Click(sender, e);
        }

        private void button8_Click(object sender, EventArgs e)
        {
            textBox1.Text = "98 05";
            _querying = true;
            button1_Click(sender, e);
        }

        private void button9_Click(object sender, EventArgs e)
        {
            textBox1.Text = "98 04";
            _querying = true;
            button1_Click(sender, e);
        }

        private void button10_Click(object sender, EventArgs e)
        {
            textBox1.Text = "98 06";
            _querying = true;
            button1_Click(sender, e);
        }
        private void button16_Click(object sender, EventArgs e)
        {
            textBox1.Text = "98 07";
            _querying = true;
            button1_Click(sender, e);
        }

        private void textBox5_TextChanged(object sender, EventArgs e)
        {
            if (_isUpdating) return;

            if (!byte.TryParse(textBox5.Text, out byte value))
                return;

            _isUpdating = true;

            for (int i = 0; i < boxes.Length; i++)
            {
                boxes[i].Checked = (value & (1 << i)) != 0;
            }
            _isUpdating = false;
        }

        private void by0_CheckedChanged(object sender, EventArgs e)
        {
            if (_isUpdating) return;

            _isUpdating = true;

            byte value = 0;

            for (int i = 0; i < boxes.Length; i++)
            {
                if (boxes[i].Checked)
                    value |= (byte)(1 << i);
            }

            textBox5.Text = value.ToString();

            _isUpdating = false;
        }

        private void by1_CheckedChanged(object sender, EventArgs e)
        {
            if (_isUpdating) return;

            _isUpdating = true;

            byte value = 0;

            for (int i = 0; i < boxes.Length; i++)
            {
                if (boxes[i].Checked)
                    value |= (byte)(1 << i);
            }

            textBox5.Text = value.ToString();

            _isUpdating = false;
        }

        private void by2_CheckedChanged(object sender, EventArgs e)
        {
            if (_isUpdating) return;

            _isUpdating = true;

            byte value = 0;

            for (int i = 0; i < boxes.Length; i++)
            {
                if (boxes[i].Checked)
                    value |= (byte)(1 << i);
            }

            textBox5.Text = value.ToString();

            _isUpdating = false;
        }

        private void by3_CheckedChanged(object sender, EventArgs e)
        {
            if (_isUpdating) return;

            _isUpdating = true;

            byte value = 0;

            for (int i = 0; i < boxes.Length; i++)
            {
                if (boxes[i].Checked)
                    value |= (byte)(1 << i);
            }

            textBox5.Text = value.ToString();

            _isUpdating = false;
        }

        private void by4_CheckedChanged(object sender, EventArgs e)
        {
            if (_isUpdating) return;

            _isUpdating = true;

            byte value = 0;

            for (int i = 0; i < boxes.Length; i++)
            {
                if (boxes[i].Checked)
                    value |= (byte)(1 << i);
            }

            textBox5.Text = value.ToString();

            _isUpdating = false;
        }

        private void by5_CheckedChanged(object sender, EventArgs e)
        {
            if (_isUpdating) return;

            _isUpdating = true;

            byte value = 0;

            for (int i = 0; i < boxes.Length; i++)
            {
                if (boxes[i].Checked)
                    value |= (byte)(1 << i);
            }

            textBox5.Text = value.ToString();

            _isUpdating = false;
        }

        private void by6_CheckedChanged(object sender, EventArgs e)
        {
            if (_isUpdating) return;

            _isUpdating = true;

            byte value = 0;

            for (int i = 0; i < boxes.Length; i++)
            {
                if (boxes[i].Checked)
                    value |= (byte)(1 << i);
            }

            textBox5.Text = value.ToString();

            _isUpdating = false;
        }

        private void by7_CheckedChanged(object sender, EventArgs e)
        {
            if (_isUpdating) return;

            _isUpdating = true;

            byte value = 0;

            for (int i = 0; i < boxes.Length; i++)
            {
                if (boxes[i].Checked)
                    value |= (byte)(1 << i);
            }

            textBox5.Text = value.ToString();

            _isUpdating = false;
        }

        private void button11_Click(object sender, EventArgs e)
        {
            textBox1.Text = "99 99 43 41 4C 31";
            button1_Click(sender, e);
        }
        //vbat
        private async void battsend_Click(object sender, EventArgs e)
        {
            button5_Click(sender, e);
            await Task.Delay(200);
            button6_Click(sender, e);
            await Task.Delay(200);
            if (!float.TryParse(textBox2.Text, out float value))
            {
                AppendLog("Invalid float in textBox2 — cannot build frame.", Color.Orange);
                return;
            }
            // Convert float back to 4 little-endian IEEE-754 bytes
            byte[] floatBytes = BitConverter.GetBytes(value);

            textBox1.Text = $"99 02 {floatBytes[0]:X2} {floatBytes[1]:X2} {floatBytes[2]:X2} {floatBytes[3]:X2}";
            button1_Click(sender, e);
        }
        //oilcal
        private async void button12_Click(object sender, EventArgs e)
        {
            button5_Click(sender, e);
            await Task.Delay(200);
            button6_Click(sender, e);
            await Task.Delay(200);
            if (!float.TryParse(textBox3.Text, out float value))
            {
                AppendLog("Invalid float in textBox3 — cannot build frame.", Color.Orange);
                return;
            }
            // Convert float back to 4 little-endian IEEE-754 bytes
            byte[] floatBytes = BitConverter.GetBytes(value);

            textBox1.Text = $"99 03 {floatBytes[0]:X2} {floatBytes[1]:X2} {floatBytes[2]:X2} {floatBytes[3]:X2}";
            button1_Click(sender, e);
        }
        //alpha
        private async void button13_Click(object sender, EventArgs e)
        {
            button5_Click(sender, e);
            await Task.Delay(200);
            button6_Click(sender, e);
            await Task.Delay(200);
            if (!float.TryParse(textBox4.Text, out float value))
            {
                AppendLog("Invalid float in textBox4 — cannot build frame.", Color.Orange);
                return;
            }
            // Convert float back to 4 little-endian IEEE-754 bytes
            byte[] floatBytes = BitConverter.GetBytes(value);

            textBox1.Text = $"99 05 {floatBytes[0]:X2} {floatBytes[1]:X2} {floatBytes[2]:X2} {floatBytes[3]:X2}";
            button1_Click(sender, e);
        }
        //SN
        private async void button15_Click(object sender, EventArgs e)
        {
            button5_Click(sender, e);
            await Task.Delay(200);
            button6_Click(sender, e);
            await Task.Delay(200);
            if (!uint.TryParse(textBox6.Text, out uint uintValue))
            {
                AppendLog("Invalid value in textBox6 — must be a whole number (0 to 4294967295).", Color.Orange);
                return;
            }
            byte[] uintBytes = BitConverter.GetBytes(uintValue);

            textBox1.Text = $"99 06 {uintBytes[0]:X2} {uintBytes[1]:X2} {uintBytes[2]:X2} {uintBytes[3]:X2}";

            button1_Click(sender, e);
        }
        //options
        private async void button14_Click(object sender, EventArgs e)
        {
            button5_Click(sender, e);
            await Task.Delay(200);
            button6_Click(sender, e);
            await Task.Delay(200);
            if (!uint.TryParse(textBox5.Text, out uint uintValue))
            {
                AppendLog("Invalid value in textBox5 — must be a whole number (0 to 4294967295).", Color.Orange);
                return;
            }
            // Convert uint32 to 4 little-endian bytes
            byte[] uintBytes = BitConverter.GetBytes(uintValue);

            textBox1.Text = $"99 04 {uintBytes[0]:X2} {uintBytes[1]:X2} {uintBytes[2]:X2} {uintBytes[3]:X2}";

            button1_Click(sender, e);
        }
        // ---- Playback ----------------------------------------------

        private void btnLoadPlayback_Click(object sender, EventArgs e)
        {
            using var dlg = new OpenFileDialog
            {
                Title = "Load Playback File",
                Filter = "Text files (*.txt)|*.txt|All files (*.*)|*.*",
                RestoreDirectory = true
            };

            if (dlg.ShowDialog() != DialogResult.OK) return;

            var frames = new List<(byte[] Data, int DelayMs)>();
            int lineNum = 0;
            int skipped = 0;
            int currentDelay = 500; // default delay between frames

            foreach (string raw in File.ReadLines(dlg.FileName))
            {
                lineNum++;
                string line = raw.Trim();

                // Skip blank lines and comment lines (# or //)
                if (string.IsNullOrEmpty(line) || line.StartsWith("#") || line.StartsWith("//"))
                    continue;

                // Delay directive: *XXXX sets the delay (ms) for all subsequent frames
                if (line.StartsWith("*"))
                {
                    string msPart = line.Substring(1).Trim();
                    if (int.TryParse(msPart, out int ms) && ms >= 0)
                    {
                        currentDelay = ms;
                        AppendLog($"Playback: line {lineNum} — delay set to {ms} ms", Color.DimGray);
                    }
                    else
                    {
                        AppendLog($"Playback: line {lineNum} invalid delay directive \"{line}\" — ignored.", Color.Orange);
                    }
                    continue;
                }

                byte[] parsed = ProtocolHelper.ParseHexString(line);
                if (parsed == null || parsed.Length == 0)
                {
                    AppendLog($"Playback: line {lineNum} skipped (bad hex): \"{line}\"", Color.Orange);
                    skipped++;
                    continue;
                }

                if (parsed.Length > 11)
                {
                    AppendLog($"Playback: line {lineNum} skipped (>11 bytes): \"{line}\"", Color.Orange);
                    skipped++;
                    continue;
                }

                frames.Add((parsed, currentDelay));
            }

            _playbackFrames = frames;
            string fname = Path.GetFileName(dlg.FileName);
            lblPlaybackStatus.Text = $"{fname}  ({frames.Count} frames{(skipped > 0 ? $", {skipped} skipped" : "")})";
            btnStartStopPlayback.Enabled = frames.Count > 0;
            AppendLog($"Playback file loaded: {fname} — {frames.Count} frame(s) ready.", Color.CornflowerBlue);
        }

        private async void btnStartStopPlayback_Click(object sender, EventArgs e)
        {
            if (_playbackRunning)
            {
                _playbackCts?.Cancel();
                return;
            }

            if (_playbackFrames.Count == 0)
            {
                AppendLog("No playback file loaded.", Color.Orange);
                return;
            }

            if (!_serial.IsConnected)
            {
                AppendLog("Not connected — cannot start playback.", Color.Orange);
                return;
            }

            await RunPlaybackAsync();
        }

        private async Task RunPlaybackAsync()
        {
            _playbackRunning = true;
            _playbackCts = new CancellationTokenSource();
            btnStartStopPlayback.Text = "Stop";
            btnStartStopPlayback.ForeColor = Color.OrangeRed;
            btnLoadPlayback.Enabled = false;

            int total = _playbackFrames.Count;
            AppendLog($"Playback started — {total} frame(s).", Color.CornflowerBlue);

            try
            {
                for (int i = 0; i < total; i++)
                {
                    _playbackCts.Token.ThrowIfCancellationRequested();

                    var (j1850Data, delayMs) = _playbackFrames[i];
                    byte[] frame = ProtocolHelper.BuildSendFrame(j1850Data);

                    AppendLog($"[{i + 1}/{total}] Playback TX: {ProtocolHelper.ToHexString(j1850Data)}  (+{delayMs} ms)", Color.LightGreen);
                    _serial.SendFrame(frame);

                    if (i < total - 1 && delayMs > 0)
                        await Task.Delay(delayMs, _playbackCts.Token);
                }

                AppendLog("Playback complete.", Color.CornflowerBlue);
            }
            catch (OperationCanceledException)
            {
                AppendLog("Playback stopped by user.", Color.Orange);
            }
            finally
            {
                _playbackRunning = false;
                _playbackCts?.Dispose();
                _playbackCts = null;
                btnStartStopPlayback.Text = "▶  Play";
                btnStartStopPlayback.ForeColor = Color.Lime;
                btnLoadPlayback.Enabled = true;
            }
        }


    }
}
