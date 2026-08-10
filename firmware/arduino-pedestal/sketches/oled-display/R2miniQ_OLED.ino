#include <HCSR04.h>     //避障超声波库文件
#include <MsTimer2.h>   //定时器2
#include <Servo.h>
#include <PS2X_lib.h>  //for v1.6
#include <SSD1306.h>    //OLED显示器库文件

////////OLED显示屏引脚相关设置///////////
#define OLED_DC 11
#define OLED_RESET 12
#define OLED_MOSI A0
#define OLED_CLK 13
SSD1306 oled(OLED_MOSI, OLED_CLK, OLED_DC, OLED_RESET, 0);

#define PS2_DAT        17  //14    
#define PS2_CMD        16  //15
#define PS2_SEL        18  //16
#define PS2_CLK        19  //17

#define TRIG A2
#define ECHO A3
//#define
double* distances;

#define AIN1 6 //L
#define AIN2 9
#define BIN1 5 //R
#define BIN2 10

#define ENCODER_R 2  //编码器采集引脚 每路2个 共4个
#define DIRECTION_R 7

#define ENCODER_L 3
#define DIRECTION_L 8

#define KEY A1

PS2X ps2x; // create PS2 Controller Class
unsigned char servo, PS2_LX, PS2_LY, PS2_RX,PS2_RY;
int Plug;//手柄数据相关标志
Servo myservo;

volatile long Velocity_L, Velocity_R = 0;   //左右轮编码器数据
int Velocity_Left, Velocity_Right = 0;     //左右轮速度

float Velocity_KP = -0.5, Velocity_KI = -0.5;
float Target_A, Target_B;
int Velocity = 0, Turn = 0;

int Battery_Voltage = 0;

char BT_CMD = 'A';
byte CTRL_MODE = 3; //2 避障模式，1 蓝牙遥控，3 PS2手柄，4 四路红外循迹

/************************************************************************
  函数功能：求次方的函数
  入口参数：m,n
  返回  值：m的n次幂
**************************************************************************/
uint32_t oled_pow(uint8_t m, uint8_t n) {
  uint32_t result = 1;
  while (n--)result *= m;
  return result;
}
/**************************************************************************
  函数功能：OLED显示变量函数
  入口参数：x:x坐标   y:行     num：显示的变量   len ：变量的长度
**************************************************************************/
void OLED_ShowNumber(uint8_t x, uint8_t y, uint32_t num, uint8_t len) {
  uint8_t t, temp;
  uint8_t enshow = 0;
  for (t = 0; t < len; t++)  {
    temp = (num / oled_pow(10, len - t - 1)) % 10;
    oled.drawchar(x + 6 * t, y, temp + '0');
  }
}

void OLED_Static()
{
  oled.drawstring(00, 0, "Voltage:");
  oled.drawstring(71, 0, ".");
  oled.drawstring(93, 0, "V");

  oled.drawstring(00, 2, "Mode:");
  oled.drawstring(00, 4, "Velocity:");//显示手柄设定的目标速度
  oled.drawstring(00, 5, "Turn:");

  oled.drawstring(00, 06, "LY:");//手柄数据显示
  oled.drawstring(42, 06, "LX:");//手柄数据显示
  oled.drawstring(84, 06, "RX:");//手柄数据显示
  oled.display();
}
void OLED_Refresh()
{
  int DISTANCE = 0;
  OLED_ShowNumber(54, 0, Battery_Voltage / 100, 2);//显示电池电量
  OLED_ShowNumber(77, 0, Battery_Voltage % 100, 2);//显示电池电量
  if ( Velocity_Left < 0)     {
    oled.drawstring(00, 01, "-:");
    OLED_ShowNumber(06, 01, -Velocity_Left, 4);//显示轮子实时速度
  }
  else if ( Velocity_Left >= 0)               {
    oled.drawstring(00, 01, "+:");
    OLED_ShowNumber(06, 01, Velocity_Left, 4);//显示轮子实时速度
  }
  if ( Velocity_Right < 0)  {
    oled.drawstring(70, 01, "-:");
    OLED_ShowNumber(76, 01, -Velocity_Right, 4);//显示轮子实时速度
  }
  else if ( Velocity_Right >= 0)               {
    oled.drawstring(70, 01, "+:");
    OLED_ShowNumber(76, 01, Velocity_Right, 4);//显示轮子实时速度
  }

  if ( Velocity < 0)  {
    oled.drawstring(54, 04, "-:");
    OLED_ShowNumber(60, 04, -Velocity, 4);//显示目标速度
  }
  else if ( Velocity >= 0)               {
    oled.drawstring(54, 04, "+:");
    OLED_ShowNumber(60, 04, Velocity, 4);//显示目标速度
  }

  if ( Turn < 0)  {
    oled.drawstring(54, 05, "-:");
    OLED_ShowNumber(60, 05, -Turn, 3);//显示目标速度
  }
  else if ( Turn >= 0)               {
    oled.drawstring(54, 05, "+:");
    OLED_ShowNumber(60, 05, Turn, 3);//显示目标速度
  }
  switch (CTRL_MODE)
  {
    case 1:
      oled.drawstring(54, 2, "Bluetooth");
      break;
    case 2:
      DISTANCE = distances[0] * 100;
      oled.drawstring(54, 2, "SR04");
      oled.drawstring(00, 3, "Distance:");
      oled.drawstring(75, 3, ".");
      oled.drawstring(94, 3, "cm");
      OLED_ShowNumber(58, 3, DISTANCE / 100, 3);//显示距离
      OLED_ShowNumber(81, 3, DISTANCE % 100, 2);//显示距离
      break;
    case 3:
      oled.drawstring(54, 2, "PS2");
      OLED_ShowNumber(18, 06, abs(PS2_LY), 3); //手柄数据显示
      OLED_ShowNumber(60, 06, abs(PS2_LX), 3); //手柄数据显示
      OLED_ShowNumber(100, 06, abs(PS2_RX), 3); //手柄数据显示
      break;
    case 4:
      oled.drawstring(54, 2, "IR Tracking");
      break;
  }
  oled.display();
}
byte MODE_Keypress()
{
  static byte count = 0;
  if (!digitalRead(A1)) count++;
  else count = 0;
  if (count >= 20)
  {
    count = 0;
    if (++CTRL_MODE == 5) CTRL_MODE = 1;
    oled.drawstring(54, 2, "          ");
    oled.drawstring(00, 3, "          ");
    oled.drawstring(58, 3, "    ");
    oled.drawstring(81, 3, "   ");
    oled.drawstring(94, 3, "  ");
    MODE_Init();
  }
  return count;
}
void MODE_Init()
{
  switch (CTRL_MODE)
  {
    case 1:
      break;
    case 2:
      HCSR04.begin(TRIG, ECHO);
      break;
    case 3:
      ps2x.config_gamepad(PS2_CLK, PS2_CMD, PS2_SEL, PS2_DAT, false, false);//PS2控制
      break;
    case 4:
      pinMode(A2, INPUT);
      pinMode(A3, INPUT);
      pinMode(A4, INPUT);
      pinMode(A5, INPUT);
      Velocity = 20;
      break;
  }
}
void setup() {
  char error;
  Serial.begin(9600);

  oled.ssd1306_init(SSD1306_SWITCHCAPVCC);//显示器初始化
  oled.clear();   // clears the screen and buffer

  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);

  //TCCR2A = TCCR2A & B11111000 | B00000011;

  attachInterrupt(0, READ_ENCODER_R, CHANGE);           //开启外部中断 编码器接口1
  attachInterrupt(1, READ_ENCODER_L, CHANGE);  //开启外部中断 编码器接口2
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);

  MODE_Init();

  MsTimer2::set(20, control);
  MsTimer2::start();
  OLED_Static();
}
/**************************************************************************
  函数功能：外部中断读取编码器数据，具有二倍频功能 注意外部中断是跳变沿触发
  入口参数：无
  返回  值：无
**************************************************************************/
void READ_ENCODER_L() {
  if (digitalRead(ENCODER_L) == LOW) {     //如果是下降沿触发的中断
    if (digitalRead(DIRECTION_L) == LOW)      Velocity_L--;  //根据另外一相电平判定方向
    else      Velocity_L++;
  }
  else {     //如果是上升沿触发的中断
    if (digitalRead(DIRECTION_L) == LOW)      Velocity_L++; //根据另外一相电平判定方向
    else     Velocity_L--;
  }
}
/**************************************************************************
  函数功能：外部中断读取编码器数据，具有二倍频功能 注意外部中断是跳变沿触发
  入口参数：无
  返回  值：无
**************************************************************************/
void READ_ENCODER_R() {
  if (digitalRead(ENCODER_R) == LOW) { //如果是下降沿触发的中断
    if (digitalRead(DIRECTION_R) == LOW)      Velocity_R--;//根据另外一相电平判定方向
    else      Velocity_R++;
  }
  else {   //如果是上升沿触发的中断
    if (digitalRead(DIRECTION_R) == LOW)      Velocity_R++; //根据另外一相电平判定方向
    else     Velocity_R--;
  }
}
/**************************************************************************
  函数功能：赋值给PWM寄存器
  入口参数：PWM
**************************************************************************/
void Set_Pwm(int motora, int motorb) {
  if (motora > 0)
    analogWrite(AIN2, motora), digitalWrite(AIN1, LOW); //赋值给PWM寄存器
  else if (motora < 0)
    digitalWrite(AIN2, LOW), analogWrite(AIN1, -motora); //赋值给PWM寄存器
  else if (motora == 0)
    digitalWrite(AIN1, HIGH), digitalWrite(AIN2, HIGH); //赋值给PWM寄存器

  if (motorb > 0)
    analogWrite(BIN1, motorb), digitalWrite(BIN2, LOW); //赋值给PWM寄存器
  else if (motorb < 0)
    digitalWrite(BIN1, LOW), analogWrite(BIN2, -motorb); //赋值给PWM寄存器
  else if (motorb == 0)
    digitalWrite(BIN1, HIGH), digitalWrite(BIN2, HIGH); //赋值给PWM寄存器
}
/**************************************************************************
  函数功能：小车运动数学模型
  入口参数：速度和转角
  //**************************************************************************/
void Kinematic_Analysis(float velocity, float turn) {
  Target_A = -velocity + turn;
  Target_B = -velocity - turn;  //后轮差速
}
/**************************************************************************
  函数功能：增量PI控制器
  入口参数：编码器测量值，目标速度
  返回  值：电机PWM
  根据增量式离散PID公式
  pwm+=Kp[e（k）-e(k-1)]+Ki*e(k)+Kd[e(k)-2e(k-1)+e(k-2)]
  e(k)代表本次偏差
  e(k-1)代表上一次的偏差  以此类推
  pwm代表增量输出
  在我们的速度控制闭环系统里面，只使用PI控制
  pwm+=Kp[e（k）-e(k-1)]+Ki*e(k)
**************************************************************************/
int Incremental_PI_A (int Encoder, int Target)
{
  static float Bias, Pwm, Last_bias;
  Bias = Encoder - Target;                              //计算偏差
  Pwm += Velocity_KP * (Bias - Last_bias) + Velocity_KI * Bias; //增量式PI控制器
  if (Pwm > 255)Pwm = 255;                            //限幅
  if (Pwm < -255)Pwm = -255;                            //限幅
  Last_bias = Bias;                                     //保存上一次偏差
  return Pwm;                                           //增量输出
}
int Incremental_PI_B (int Encoder, int Target)
{
  static float Bias, Pwm, Last_bias;
  Bias = Encoder - Target;                              //计算偏差
  Pwm += Velocity_KP * (Bias - Last_bias) + Velocity_KI * Bias; //增量式PI控制器
  if (Pwm > 255)Pwm = 255;                            //限幅
  if (Pwm < -255)Pwm = -255;                            //限幅
  Last_bias = Bias;                                     //保存上一次偏差
  return Pwm;                                           //增量输出
}

int i = 0;

void control() {
  static float Voltage_All; //电压采样相关变量
  static unsigned char  Voltage_Count; //位置控制分频用的变量
  int Motora, Motorb, Temp2; //临时变量
  Velocity_Left = Velocity_L;
  Velocity_L = 0;
  Velocity_Right = Velocity_R;
  Velocity_R = 0;
  if (MODE_Keypress() != 0) return;
  GetRC();
  Kinematic_Analysis(Velocity, Turn);

  Motora = Incremental_PI_A(Velocity_Left, Target_A); //===速度PI控制器
  Motorb = Incremental_PI_B(Velocity_Right, Target_B); //===速度PI控制器
  Set_Pwm(Motora, Motorb);

  //  Serial.print(Motora);
  //  Serial.print("\t");
  //  Serial.print(Motorb);
  //  Serial.print("\t");
  //  Serial.print(Velocity_Left);
  //  Serial.print("\t");
  //  Serial.println(Velocity_Right);

  Temp2 = analogRead(A7);  //采集一下电池电压
  Voltage_Count++;        //平均值计数器
  Voltage_All += Temp2;   //多次采样累积
  if (Voltage_Count == 100) Battery_Voltage = Voltage_All * 0.05371, Voltage_All = 0, Voltage_Count = 0; //求平均值
}

void loop()
{
  if (CTRL_MODE == 2)
  {
    distances = HCSR04.measureDistanceCm();
    if (distances[0] <= 20)
    {
      Velocity = 0;
      Turn = 15;
    }
    else
    {
      Velocity = 15;
      Turn = 0;
    }
  }
  OLED_Refresh();
}
void Track()
{
  int turn = 0;
  if (!digitalRead(A2)) turn += 1;
  if (!digitalRead(A4)) turn -= 1;
  if (!digitalRead(A3)) turn += 6;
  if (!digitalRead(A5)) turn -= 6;
  //  if (turn != 0 && Velocity>0)Velocity--;
  //  else Velocity = 20;
  Turn = turn;
}
void ReadGamepad()
{
  if (Plug == 0)ps2x.read_gamepad(false, 0); //read controller and set large motor to spin at 'vibrate' speed 
  PS2_LY = ps2x.Analog(PSS_LY); //手柄左摇杆Y轴数据读取
  PS2_RX = ps2x.Analog(PSS_RX); //手柄右摇杆X轴数据读取
  PS2_LX = ps2x.Analog(PSS_LX); //手柄左摇杆X轴数据读取
  PS2_RY = ps2x.Analog(PSS_RY); //手柄右摇杆Y轴数据读取

  if(ps2x.Button(PSB_R2))
    CTRL_MODE = 3; //手柄R2，进入手柄模式
  else if(ps2x.Button(PSB_R1))
    CTRL_MODE = 1; //手柄R1，进入APP模式

  if (PS2_RY == 255 && PS2_RX == 255 && PS2_LY == 255 && PS2_LX == 255) 
  {
    Plug = 1;
    CTRL_MODE = 1;  //拔掉手柄接收模块，进入APP模式
  }
  else 
  {
    Plug = 0;
  }

  if (Serial.available() <= 0) {
    Plug = 0; //APP停止指令，允许进入手柄模式
  }
}
void PS2CMD()
{
  char Yuzhi = 5;
  float LY, RX, RY, LX;
  LY = PS2_LY - 128; //计算偏差
  RY = PS2_RY - 128; //计算偏差
  LX = PS2_LX - 128; //计算偏差
  RX = PS2_RX - 128; //计算偏差
  if (LY > -Yuzhi && LY < Yuzhi)LY = 0; //小角度设为死区 防止抖动出现异常
  if (RX > -Yuzhi && RX < Yuzhi)RX = 0;
  //Serial.print(LY);
  //Serial.print("\t");
  //Serial.println(RX);
  Velocity = LY / 2; //速度和摇杆的力度相关。
  Turn = RX / 3;
  //  Serial.print(Velocity);
  //  Serial.print("\t");
  //  Serial.println(Turn);
}
void GetRC()
{
  switch (CTRL_MODE)
  {
    case 3:
      ReadGamepad();
      PS2CMD();
      break;
    case 4:
      Track();
      break;
  }
}
void serialEvent()
{
  while (Serial.available())
  {
    BT_CMD = (char)Serial.read();
  }
  if (CTRL_MODE == 1)
  {
    switch (BT_CMD)
    {
      case 'A'://前进
        Velocity = 30;
        Turn = 0;
        break;
      case 'H'://左转
        Velocity = 15;
        Turn = -5;
        break;
      case 'B'://右转
        Velocity = 15;
        Turn = 5;
        break;
      case 'Z'://停止
        Velocity = 0;
        Turn = 0;
        break;
      case 'G'://左旋
        Velocity = 0;
        Turn = -10;
        break;
      case 'C'://右旋
        Velocity = 0;
        Turn = 10;
        break;
      case 'F'://左后
        Velocity = -15;
        Turn = 5;
        break;
      case 'E'://后退
        Velocity = -30;
        Turn = 0;
        break;
      case 'D'://右后
        Velocity = -15;
        Turn = -5;
        break;
    }
  }
}
