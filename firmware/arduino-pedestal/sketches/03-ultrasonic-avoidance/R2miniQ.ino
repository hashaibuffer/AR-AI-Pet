#include <HCSR04.h>     //避障超声波库文件
#include <MsTimer2.h>   //定时器2
 #include <Servo.h>
#include <PS2X_lib.h>  //for v1.6

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

PS2X ps2x; // create PS2 Controller Class
unsigned char servo,PS2_LY, PS2_RX;
Servo myservo;
 
volatile long Velocity_L, Velocity_R = 0;   //左右轮编码器数据
int Velocity_Left, Velocity_Right = 0;     //左右轮速度

float Velocity_KP = 0.5, Velocity_KI =  0.5;
float Target_A, Target_B;
int Velocity = 0, Turn = 0;

int Battery_Voltage = 0;

char BT_CMD = 'A';
byte CTRL_MODE = 1; //2 避障模式，1 蓝牙遥控，3 PS2手柄，4 四路红外循迹

void setup() {
  char error;
  Serial.begin(115200);

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
  switch (CTRL_MODE)
  {
    case 1:
      break;
    case 2:
      HCSR04.begin(TRIG, ECHO);
      break;
    case 3:
      error = ps2x.config_gamepad(PS2_CLK, PS2_CMD, PS2_SEL, PS2_DAT, false, false);//PS2控制
      break;
    case 4:
      pinMode(A2, INPUT);
      pinMode(A3, INPUT);
      pinMode(A4, INPUT);
      pinMode(A5, INPUT);
      break;
  }
  MsTimer2::set(10, control);
  MsTimer2::start();
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
    analogWrite(AIN1, motora), digitalWrite(AIN2, LOW); //赋值给PWM寄存器
  else if (motora < 0)
    digitalWrite(AIN1, LOW), analogWrite(AIN2, -motora); //赋值给PWM寄存器
  else if (motora == 0)
    digitalWrite(AIN1, HIGH), digitalWrite(AIN2, HIGH); //赋值给PWM寄存器

  if (motorb > 0)
    analogWrite(BIN2, motorb), digitalWrite(BIN1, LOW); //赋值给PWM寄存器
  else if (motorb < 0)
    digitalWrite(BIN2, LOW), analogWrite(BIN1, -motorb); //赋值给PWM寄存器
  else if (motorb == 0)
    digitalWrite(BIN2, HIGH), digitalWrite(BIN1, HIGH); //赋值给PWM寄存器
}
/**************************************************************************
  函数功能：小车运动数学模型
  入口参数：速度和转角
  //**************************************************************************/
void Kinematic_Analysis(float velocity, float turn) {
  Target_A = velocity + turn;
  Target_B = velocity - turn;  //后轮差速
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

  Kinematic_Analysis(Velocity, Turn);

  Motora = Incremental_PI_A(Velocity_Left, Target_A); //===速度PI控制器
  Motorb = Incremental_PI_B(Velocity_Right, Target_B); //===速度PI控制器
  Set_Pwm(Motora, Motorb);

  //  Serial.print(Motora);
  //  Serial.print("\t");
  //  Serial.print(Motorb);
  //  Serial.print("\t");
  Serial.print(Velocity_Left);
  Serial.print("\t");
  Serial.println(Velocity_Right);

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
