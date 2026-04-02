namespace BridgePro
{
    partial class Form1
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            button1 = new Button();
            textBox1 = new TextBox();
            button2 = new Button();
            label1 = new Label();
            comboBox1 = new ComboBox();
            button3 = new Button();
            button4 = new Button();
            _chkRxEnable = new CheckBox();
            label2 = new Label();
            _log = new RichTextBox();
            label3 = new Label();
            groupBox1 = new GroupBox();
            button16 = new Button();
            label10 = new Label();
            textBox7 = new TextBox();
            button15 = new Button();
            button14 = new Button();
            button13 = new Button();
            button12 = new Button();
            battsend = new Button();
            label9 = new Label();
            by7 = new CheckBox();
            by6 = new CheckBox();
            by5 = new CheckBox();
            by4 = new CheckBox();
            by3 = new CheckBox();
            by2 = new CheckBox();
            by1 = new CheckBox();
            by0 = new CheckBox();
            button11 = new Button();
            button10 = new Button();
            button9 = new Button();
            button8 = new Button();
            button7 = new Button();
            read1 = new Button();
            label8 = new Label();
            textBox6 = new TextBox();
            label7 = new Label();
            textBox5 = new TextBox();
            label6 = new Label();
            textBox4 = new TextBox();
            label5 = new Label();
            textBox3 = new TextBox();
            label4 = new Label();
            textBox2 = new TextBox();
            button6 = new Button();
            button5 = new Button();
            checkBox2 = new CheckBox();
            groupBox1.SuspendLayout();
            SuspendLayout();
            // 
            // button1
            // 
            button1.BackColor = Color.FromArgb(64, 64, 64);
            button1.ForeColor = Color.Lime;
            button1.Location = new Point(850, 981);
            button1.Name = "button1";
            button1.Size = new Size(136, 44);
            button1.TabIndex = 0;
            button1.Text = "Send";
            button1.UseVisualStyleBackColor = false;
            button1.Click += button1_Click;
            // 
            // textBox1
            // 
            textBox1.BackColor = Color.FromArgb(64, 64, 64);
            textBox1.Font = new Font("Segoe UI", 11F);
            textBox1.ForeColor = Color.Lime;
            textBox1.Location = new Point(11, 984);
            textBox1.Name = "textBox1";
            textBox1.Size = new Size(827, 37);
            textBox1.TabIndex = 1;
            // 
            // button2
            // 
            button2.BackColor = Color.FromArgb(64, 64, 64);
            button2.ForeColor = Color.Lime;
            button2.Location = new Point(888, 344);
            button2.Name = "button2";
            button2.Size = new Size(98, 42);
            button2.TabIndex = 3;
            button2.Text = "Clear";
            button2.UseVisualStyleBackColor = false;
            button2.Click += button2_Click;
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.ForeColor = Color.Lime;
            label1.Location = new Point(12, 9);
            label1.Name = "label1";
            label1.Size = new Size(48, 25);
            label1.TabIndex = 4;
            label1.Text = "Port:";
            // 
            // comboBox1
            // 
            comboBox1.BackColor = Color.FromArgb(64, 64, 64);
            comboBox1.ForeColor = Color.Lime;
            comboBox1.FormattingEnabled = true;
            comboBox1.Location = new Point(80, 6);
            comboBox1.Name = "comboBox1";
            comboBox1.Size = new Size(182, 33);
            comboBox1.TabIndex = 5;
            // 
            // button3
            // 
            button3.BackColor = Color.FromArgb(64, 64, 64);
            button3.ForeColor = Color.Lime;
            button3.Location = new Point(268, 5);
            button3.Name = "button3";
            button3.Size = new Size(112, 34);
            button3.TabIndex = 6;
            button3.Text = "Refresh";
            button3.UseVisualStyleBackColor = false;
            button3.Click += button3_Click;
            // 
            // button4
            // 
            button4.BackColor = Color.FromArgb(64, 64, 64);
            button4.ForeColor = Color.Lime;
            button4.Location = new Point(386, 4);
            button4.Name = "button4";
            button4.Size = new Size(112, 34);
            button4.TabIndex = 7;
            button4.Text = "Connect";
            button4.UseVisualStyleBackColor = false;
            button4.Click += button4_Click;
            // 
            // _chkRxEnable
            // 
            _chkRxEnable.AutoSize = true;
            _chkRxEnable.ForeColor = Color.Lime;
            _chkRxEnable.Location = new Point(504, 10);
            _chkRxEnable.Name = "_chkRxEnable";
            _chkRxEnable.Size = new Size(112, 29);
            _chkRxEnable.TabIndex = 8;
            _chkRxEnable.Text = "RX Mode";
            _chkRxEnable.UseVisualStyleBackColor = true;
            _chkRxEnable.CheckedChanged += _chkRxEnable_CheckedChanged;
            // 
            // label2
            // 
            label2.AutoSize = true;
            label2.ForeColor = Color.Lime;
            label2.Location = new Point(12, 353);
            label2.Name = "label2";
            label2.Size = new Size(46, 25);
            label2.TabIndex = 9;
            label2.Text = "Log:";
            // 
            // _log
            // 
            _log.BackColor = Color.Black;
            _log.ForeColor = Color.Green;
            _log.Location = new Point(10, 395);
            _log.Name = "_log";
            _log.Size = new Size(976, 580);
            _log.TabIndex = 10;
            _log.Text = "";
            // 
            // label3
            // 
            label3.AutoSize = true;
            label3.ForeColor = Color.Lime;
            label3.Location = new Point(6, 27);
            label3.Name = "label3";
            label3.Size = new Size(108, 25);
            label3.TabIndex = 12;
            label3.Text = "Commands:";
            // 
            // groupBox1
            // 
            groupBox1.Controls.Add(button16);
            groupBox1.Controls.Add(label10);
            groupBox1.Controls.Add(textBox7);
            groupBox1.Controls.Add(button15);
            groupBox1.Controls.Add(button14);
            groupBox1.Controls.Add(button13);
            groupBox1.Controls.Add(button12);
            groupBox1.Controls.Add(battsend);
            groupBox1.Controls.Add(label9);
            groupBox1.Controls.Add(by7);
            groupBox1.Controls.Add(by6);
            groupBox1.Controls.Add(by5);
            groupBox1.Controls.Add(by4);
            groupBox1.Controls.Add(by3);
            groupBox1.Controls.Add(by2);
            groupBox1.Controls.Add(by1);
            groupBox1.Controls.Add(by0);
            groupBox1.Controls.Add(button11);
            groupBox1.Controls.Add(button10);
            groupBox1.Controls.Add(button9);
            groupBox1.Controls.Add(button8);
            groupBox1.Controls.Add(button7);
            groupBox1.Controls.Add(read1);
            groupBox1.Controls.Add(label8);
            groupBox1.Controls.Add(textBox6);
            groupBox1.Controls.Add(label7);
            groupBox1.Controls.Add(textBox5);
            groupBox1.Controls.Add(label6);
            groupBox1.Controls.Add(textBox4);
            groupBox1.Controls.Add(label5);
            groupBox1.Controls.Add(textBox3);
            groupBox1.Controls.Add(label4);
            groupBox1.Controls.Add(textBox2);
            groupBox1.Controls.Add(button6);
            groupBox1.Controls.Add(button5);
            groupBox1.Controls.Add(label3);
            groupBox1.ForeColor = Color.Lime;
            groupBox1.Location = new Point(12, 57);
            groupBox1.Name = "groupBox1";
            groupBox1.Size = new Size(968, 273);
            groupBox1.TabIndex = 13;
            groupBox1.TabStop = false;
            groupBox1.Text = "99-02 Swap";
            // 
            // button16
            // 
            button16.BackColor = Color.FromArgb(64, 64, 64);
            button16.Location = new Point(412, 223);
            button16.Name = "button16";
            button16.Size = new Size(87, 34);
            button16.TabIndex = 47;
            button16.Text = "Read Val";
            button16.UseVisualStyleBackColor = false;
            button16.Click += button16_Click;
            // 
            // label10
            // 
            label10.AutoSize = true;
            label10.ForeColor = Color.Lime;
            label10.Location = new Point(165, 232);
            label10.Name = "label10";
            label10.Size = new Size(78, 25);
            label10.TabIndex = 46;
            label10.Text = "FW VER:";
            // 
            // textBox7
            // 
            textBox7.BackColor = Color.FromArgb(64, 64, 64);
            textBox7.Enabled = false;
            textBox7.ForeColor = Color.Lime;
            textBox7.Location = new Point(256, 226);
            textBox7.Name = "textBox7";
            textBox7.Size = new Size(150, 31);
            textBox7.TabIndex = 45;
            // 
            // button15
            // 
            button15.BackColor = Color.FromArgb(64, 64, 64);
            button15.Location = new Point(505, 185);
            button15.Name = "button15";
            button15.Size = new Size(129, 34);
            button15.TabIndex = 44;
            button15.Text = "Send to RAM";
            button15.UseVisualStyleBackColor = false;
            button15.Click += button15_Click;
            // 
            // button14
            // 
            button14.BackColor = Color.FromArgb(64, 64, 64);
            button14.Location = new Point(505, 145);
            button14.Name = "button14";
            button14.Size = new Size(129, 34);
            button14.TabIndex = 43;
            button14.Text = "Send to RAM";
            button14.UseVisualStyleBackColor = false;
            button14.Click += button14_Click;
            // 
            // button13
            // 
            button13.BackColor = Color.FromArgb(64, 64, 64);
            button13.Location = new Point(505, 104);
            button13.Name = "button13";
            button13.Size = new Size(129, 34);
            button13.TabIndex = 42;
            button13.Text = "Send to RAM";
            button13.UseVisualStyleBackColor = false;
            button13.Click += button13_Click;
            // 
            // button12
            // 
            button12.BackColor = Color.FromArgb(64, 64, 64);
            button12.Location = new Point(505, 64);
            button12.Name = "button12";
            button12.Size = new Size(129, 34);
            button12.TabIndex = 41;
            button12.Text = "Send to RAM";
            button12.UseVisualStyleBackColor = false;
            button12.Click += button12_Click;
            // 
            // battsend
            // 
            battsend.BackColor = Color.FromArgb(64, 64, 64);
            battsend.Location = new Point(505, 22);
            battsend.Name = "battsend";
            battsend.Size = new Size(129, 34);
            battsend.TabIndex = 40;
            battsend.Text = "Send to RAM";
            battsend.UseVisualStyleBackColor = false;
            battsend.Click += battsend_Click;
            // 
            // label9
            // 
            label9.AutoSize = true;
            label9.ForeColor = Color.Lime;
            label9.Location = new Point(678, 27);
            label9.Name = "label9";
            label9.Size = new Size(106, 25);
            label9.TabIndex = 39;
            label9.Text = "Option bits:";
            // 
            // by7
            // 
            by7.AutoSize = true;
            by7.Location = new Point(838, 160);
            by7.Name = "by7";
            by7.Size = new Size(105, 29);
            by7.TabIndex = 38;
            by7.Text = "reserved";
            by7.UseVisualStyleBackColor = true;
            by7.CheckedChanged += by7_CheckedChanged;
            // 
            // by6
            // 
            by6.AutoSize = true;
            by6.Location = new Point(838, 125);
            by6.Name = "by6";
            by6.Size = new Size(105, 29);
            by6.TabIndex = 37;
            by6.Text = "reserved";
            by6.UseVisualStyleBackColor = true;
            by6.CheckedChanged += by6_CheckedChanged;
            // 
            // by5
            // 
            by5.AutoSize = true;
            by5.Location = new Point(838, 90);
            by5.Name = "by5";
            by5.Size = new Size(105, 29);
            by5.TabIndex = 36;
            by5.Text = "reserved";
            by5.UseVisualStyleBackColor = true;
            by5.CheckedChanged += by5_CheckedChanged;
            // 
            // by4
            // 
            by4.AutoSize = true;
            by4.Location = new Point(838, 55);
            by4.Name = "by4";
            by4.Size = new Size(105, 29);
            by4.TabIndex = 35;
            by4.Text = "reserved";
            by4.UseVisualStyleBackColor = true;
            by4.CheckedChanged += by4_CheckedChanged;
            // 
            // by3
            // 
            by3.AutoSize = true;
            by3.Location = new Point(678, 160);
            by3.Name = "by3";
            by3.Size = new Size(105, 29);
            by3.TabIndex = 34;
            by3.Text = "reserved";
            by3.UseVisualStyleBackColor = true;
            by3.CheckedChanged += by3_CheckedChanged;
            // 
            // by2
            // 
            by2.AutoSize = true;
            by2.Location = new Point(678, 125);
            by2.Name = "by2";
            by2.Size = new Size(105, 29);
            by2.TabIndex = 33;
            by2.Text = "reserved";
            by2.UseVisualStyleBackColor = true;
            by2.CheckedChanged += by2_CheckedChanged;
            // 
            // by1
            // 
            by1.AutoSize = true;
            by1.Location = new Point(678, 90);
            by1.Name = "by1";
            by1.Size = new Size(105, 29);
            by1.TabIndex = 32;
            by1.Text = "reserved";
            by1.UseVisualStyleBackColor = true;
            by1.CheckedChanged += by1_CheckedChanged;
            // 
            // by0
            // 
            by0.AutoSize = true;
            by0.Location = new Point(678, 55);
            by0.Name = "by0";
            by0.Size = new Size(116, 29);
            by0.TabIndex = 31;
            by0.Text = "99 Airbag";
            by0.UseVisualStyleBackColor = true;
            by0.CheckedChanged += by0_CheckedChanged;
            // 
            // button11
            // 
            button11.BackColor = Color.FromArgb(64, 64, 64);
            button11.Location = new Point(6, 135);
            button11.Name = "button11";
            button11.Size = new Size(112, 34);
            button11.TabIndex = 30;
            button11.Text = "Save Ram";
            button11.UseVisualStyleBackColor = false;
            button11.Click += button11_Click;
            // 
            // button10
            // 
            button10.BackColor = Color.FromArgb(64, 64, 64);
            button10.Location = new Point(412, 184);
            button10.Name = "button10";
            button10.Size = new Size(87, 34);
            button10.TabIndex = 29;
            button10.Text = "Read Val";
            button10.UseVisualStyleBackColor = false;
            button10.Click += button10_Click;
            // 
            // button9
            // 
            button9.BackColor = Color.FromArgb(64, 64, 64);
            button9.Location = new Point(412, 144);
            button9.Name = "button9";
            button9.Size = new Size(87, 34);
            button9.TabIndex = 28;
            button9.Text = "Read Val";
            button9.UseVisualStyleBackColor = false;
            button9.Click += button9_Click;
            // 
            // button8
            // 
            button8.BackColor = Color.FromArgb(64, 64, 64);
            button8.Location = new Point(412, 104);
            button8.Name = "button8";
            button8.Size = new Size(87, 34);
            button8.TabIndex = 27;
            button8.Text = "Read Val";
            button8.UseVisualStyleBackColor = false;
            button8.Click += button8_Click;
            // 
            // button7
            // 
            button7.BackColor = Color.FromArgb(64, 64, 64);
            button7.Location = new Point(412, 64);
            button7.Name = "button7";
            button7.Size = new Size(87, 34);
            button7.TabIndex = 26;
            button7.Text = "Read Val";
            button7.UseVisualStyleBackColor = false;
            button7.Click += button7_Click;
            // 
            // read1
            // 
            read1.BackColor = Color.FromArgb(64, 64, 64);
            read1.Location = new Point(412, 22);
            read1.Name = "read1";
            read1.Size = new Size(87, 34);
            read1.TabIndex = 25;
            read1.Text = "Read Val";
            read1.UseVisualStyleBackColor = false;
            read1.Click += read1_Click;
            // 
            // label8
            // 
            label8.AutoSize = true;
            label8.ForeColor = Color.Lime;
            label8.Location = new Point(206, 193);
            label8.Name = "label8";
            label8.Size = new Size(39, 25);
            label8.TabIndex = 24;
            label8.Text = "SN:";
            // 
            // textBox6
            // 
            textBox6.BackColor = Color.FromArgb(64, 64, 64);
            textBox6.ForeColor = Color.Lime;
            textBox6.Location = new Point(256, 187);
            textBox6.Name = "textBox6";
            textBox6.Size = new Size(150, 31);
            textBox6.TabIndex = 23;
            // 
            // label7
            // 
            label7.AutoSize = true;
            label7.ForeColor = Color.Lime;
            label7.Location = new Point(165, 153);
            label7.Name = "label7";
            label7.Size = new Size(80, 25);
            label7.TabIndex = 22;
            label7.Text = "Options:";
            // 
            // textBox5
            // 
            textBox5.BackColor = Color.FromArgb(64, 64, 64);
            textBox5.Enabled = false;
            textBox5.ForeColor = Color.Lime;
            textBox5.Location = new Point(256, 147);
            textBox5.Name = "textBox5";
            textBox5.Size = new Size(150, 31);
            textBox5.TabIndex = 21;
            textBox5.TextChanged += textBox5_TextChanged;
            // 
            // label6
            // 
            label6.AutoSize = true;
            label6.ForeColor = Color.Lime;
            label6.Location = new Point(183, 113);
            label6.Name = "label6";
            label6.Size = new Size(62, 25);
            label6.TabIndex = 20;
            label6.Text = "Alpha:";
            // 
            // textBox4
            // 
            textBox4.BackColor = Color.FromArgb(64, 64, 64);
            textBox4.ForeColor = Color.Lime;
            textBox4.Location = new Point(256, 107);
            textBox4.Name = "textBox4";
            textBox4.Size = new Size(150, 31);
            textBox4.TabIndex = 19;
            // 
            // label5
            // 
            label5.AutoSize = true;
            label5.ForeColor = Color.Lime;
            label5.Location = new Point(183, 70);
            label5.Name = "label5";
            label5.Size = new Size(67, 25);
            label5.TabIndex = 18;
            label5.Text = "Oil Cal:";
            label5.TextAlign = ContentAlignment.TopRight;
            // 
            // textBox3
            // 
            textBox3.BackColor = Color.FromArgb(64, 64, 64);
            textBox3.ForeColor = Color.Lime;
            textBox3.Location = new Point(256, 67);
            textBox3.Name = "textBox3";
            textBox3.Size = new Size(150, 31);
            textBox3.TabIndex = 17;
            // 
            // label4
            // 
            label4.AutoSize = true;
            label4.ForeColor = Color.Lime;
            label4.Location = new Point(150, 31);
            label4.Name = "label4";
            label4.Size = new Size(100, 25);
            label4.TabIndex = 16;
            label4.Text = "Battery Cal:";
            // 
            // textBox2
            // 
            textBox2.BackColor = Color.FromArgb(64, 64, 64);
            textBox2.ForeColor = Color.Lime;
            textBox2.Location = new Point(256, 25);
            textBox2.Name = "textBox2";
            textBox2.Size = new Size(150, 31);
            textBox2.TabIndex = 15;
            // 
            // button6
            // 
            button6.BackColor = Color.FromArgb(64, 64, 64);
            button6.Location = new Point(6, 95);
            button6.Name = "button6";
            button6.Size = new Size(112, 34);
            button6.TabIndex = 14;
            button6.Text = "Magic";
            button6.UseVisualStyleBackColor = false;
            button6.Click += button6_Click;
            // 
            // button5
            // 
            button5.BackColor = Color.FromArgb(64, 64, 64);
            button5.Location = new Point(6, 55);
            button5.Name = "button5";
            button5.Size = new Size(112, 34);
            button5.TabIndex = 13;
            button5.Text = "Mute";
            button5.UseVisualStyleBackColor = false;
            button5.Click += button5_Click;
            // 
            // checkBox2
            // 
            checkBox2.AutoSize = true;
            checkBox2.ForeColor = Color.Lime;
            checkBox2.Location = new Point(622, 12);
            checkBox2.Name = "checkBox2";
            checkBox2.Size = new Size(109, 29);
            checkBox2.TabIndex = 14;
            checkBox2.Text = "Trim CRC";
            checkBox2.UseVisualStyleBackColor = true;
            checkBox2.CheckedChanged += checkBox2_CheckedChanged;
            // 
            // Form1
            // 
            AutoScaleDimensions = new SizeF(10F, 25F);
            AutoScaleMode = AutoScaleMode.Font;
            BackColor = Color.FromArgb(32, 36, 36);
            ClientSize = new Size(992, 1034);
            Controls.Add(checkBox2);
            Controls.Add(groupBox1);
            Controls.Add(_log);
            Controls.Add(label2);
            Controls.Add(_chkRxEnable);
            Controls.Add(button4);
            Controls.Add(button3);
            Controls.Add(comboBox1);
            Controls.Add(label1);
            Controls.Add(button2);
            Controls.Add(textBox1);
            Controls.Add(button1);
            Name = "Form1";
            Text = "Bridge Pro";
            Load += Form1_Load;
            groupBox1.ResumeLayout(false);
            groupBox1.PerformLayout();
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private Button button1;
        private TextBox textBox1;
        private Button button2;
        private Label label1;
        private ComboBox comboBox1;
        private Button button3;
        private Button button4;
        private CheckBox _chkRxEnable;
        private Label label2;
        private RichTextBox _log;
        private Label label3;
        private GroupBox groupBox1;
        private Button button6;
        private Button button5;
        private CheckBox checkBox2;
        private TextBox textBox2;
        private Label label4;
        private Label label6;
        private TextBox textBox4;
        private Label label5;
        private TextBox textBox3;
        private Label label8;
        private TextBox textBox6;
        private Label label7;
        private TextBox textBox5;
        private Button button10;
        private Button button9;
        private Button button8;
        private Button button7;
        private Button read1;
        private Button button11;
        private CheckBox by7;
        private CheckBox by6;
        private CheckBox by5;
        private CheckBox by4;
        private CheckBox by3;
        private CheckBox by2;
        private CheckBox by1;
        private CheckBox by0;
        private Label label9;
        private Button battsend;
        private Button button15;
        private Button button14;
        private Button button13;
        private Button button12;
        private Button button16;
        private Label label10;
        private TextBox textBox7;
    }
}
