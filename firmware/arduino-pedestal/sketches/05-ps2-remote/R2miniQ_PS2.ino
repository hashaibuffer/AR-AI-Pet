 #include <Servo.h>
#include <MsTimer2.h>
#include <PS2X_lib.h>  //for v1.6

#define PS2_DAT        17  //14    
#define PS2_CMD        16  //15
#define PS2_SEL        18  //16
#define PS2_CLK        19  //17

#define AIN1 9
#define AIN2 6
#define BIN1 5
#define BIN2 10

#define ENCODER_L 2  //编码器采集引脚 每路2个 共4个
#define DIRECTION_L 7
#define ENCODER_R 3
#define DIRECTION_R 8

PS2X ps2x; // create PS2 Controller Class
unsigned char servo,PS2_LY, PS2_RX;
Servo myservo;
volatile long Velocity_L, Velocity_R = 0;   //左右轮编码器数据
int Velocity_Left, Velocity_Right = 0;     //左右轮速度

float Velocity_KP = 0.5, Velocity_KI =  0.5;
float Target_A, Target_B;
int Velocity=0,Turn=0;

void setup() {
  char error;
  Serial.begin(115200);
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  myservo.attach(4);
  TCCR2A = TCCR2A & B11111000 | B00000011;

  attachInterrupt(0, READ_ENCODER_L, CHANGE);           //开启外部中断 编码器接口1
  attachInterrupt(1, READ_ENCODER_R, CHANGE);  //开启外部中断 编码器接口2
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);

  error = ps2x.config_gamepad(PS2_CLK, PS2_CMD, PS2_SEL, PS2_DAT, false, false);//PS2控制
  
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
    if (digitalRead(DIRECTION_L) == LOW)      Velocity_L++;  //根据另外一相电平判定方向
    else      Velocity_L--;
  }
  else {     //如果是上升沿触发的中断
    if (digitalRead(DIRECTION_L) == LOW)      Velocity_L--; //根据另外一相电平判定方向
    else     Velocity_L++;
  }
}
/**************************************************************************
  函数功能：外部中断读取编码器数据，具有二倍频功能 注意外部中断是跳变沿触发
  入口参数：无
  返回  值：无
**************************************************************************/
void READ_ENCODER_R() {
  if (digitalRead(ENCODER_R) == LOW) { //如果是下降沿触发的中断
    if (digitalRead(DIRECTION_R) == LOW)      Velocity_R++;//根据另外一相电平判定方向
    else      Velocity_R--;
  }
  else {   //如果是上升沿触发的中断
    if (digitalRead(DIRECTION_R) == LOW)      Velocity_R--; //根据另外一相电平判定方向
    else     Velocity_R++;
  }
}
/**************************************************************************
  函数功能：赋值给PWM寄存器
  入口参数：PWM
**************************************************************************/
void Set_Pwm(int motora, int motorb) {
  if (motora > 0)
    digitalWrite(BIN1, LOW), analogWrite(BIN2, motora); //赋值给PWM寄存器
  else if (motora < 0)
    analogWrite(BIN1, -motora), digitalWrite(BIN2, LOW); //赋值给PWM寄存器
  else if (motora == 0)
    digitalWrite(BIN2, LOW), digitalWrite(BIN1, LOW); //赋值给PWM寄存器

  if (motorb > 0)
    digitalWrite(AIN2, LOW), analogWrite(AIN1, motorb); //赋值给PWM寄存器
  else if (motorb < 0)
    analogWrite(AIN2, -motorb), digitalWrite(AIN1, LOW); //赋值给PWM寄存器
  else if (motorb == 0)
    digitalWrite(AIN1, LOW), digitalWrite(AIN2, LOW); //赋值给PWM寄存器
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

/*******************************************************************
   电压采集计算
 *******************************************************************/
float Battery()
{
  static float VOLTAGE;
  float Voltage;
  int Temp2 = analogRead(7);  //采集一下电池电压
  Voltage = Temp2 * 0.0537;   // Temp2/255*5*11  255为AI5V时满值，10K+1K电阻分压
  VOLTAGE = VOLTAGE * 0.9 + Voltage * 0.1;
  return VOLTAGE;
}

int i = 0;

void GetRC()
{
  char Yuzhi = 2;
  float LY, RX;
  LY = PS2_LY - 128; //计算偏差
  RX = PS2_RX - 128;
  if (LY > -Yuzhi && LY < Yuzhi)LY = 0; //小角度设为死区 防止抖动出现异常
  if (RX > -Yuzhi && RX < Yuzhi)RX = 0;
  //Serial.print(LY);
  //Serial.print("\t");
  //Serial.println(RX);
  Velocity = LY / 5; //速度和摇杆的力度相关。
  Turn = RX / 7;
//  Serial.print(Velocity);
//  Serial.print("\t");
//  Serial.println(Turn);
}
void control() {

  int Motora, Motorb; //临时变量
  Velocity_Left = Velocity_L;
  Velocity_L = 0;
  Velocity_Right = Velocity_R;
  Velocity_R = 0;
  GetRC();  
  Kinematic_Analysis(Velocity, Turn);
  Motora = Incremental_PI_A(Velocity_Left, Target_A); //===速度PI控制器
  Motorb = Incremental_PI_B(Velocity_Right, Target_B); //===速度PI控制器
  Set_Pwm(Motora, Motorb);
  
//  Serial.print(Velocity_Left);
//  Serial.print("\t");
//  Serial.println(Velocity_Right);
//  Serial.print("\t");
  Serial.print(Motora);
  Serial.print("\t");
  Serial.println(Motorb);
  Battery();
}

void loop()
{
  ps2x.read_gamepad(false, 0); //read controller and set large motor to spin at 'vibrate' speed
  PS2_LY=ps2x.Analog(PSS_LY);
  PS2_RX=ps2x.Analog(PSS_RX);
//  Serial.print(PS2_LY);
//  Serial.print("\t");
//  Serial.println(PS2_RX);
  delay(10);
}
