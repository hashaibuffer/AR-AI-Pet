byte comdataL[3] = {}; //接受左边传感器的数据
int DistanceL = 6800; //左边小车的距离发送模块的距离
byte comdataR[3] = {}; //接受右边传感器的数据
int DistanceR = 6800; //右边小车的距离发送模块的距离


void setup() {
  Serial.begin(115200);
}




/*******************************************************************
   电压采集计算
 *******************************************************************/
float Battery()
{
  static float VOLTAGE = analogRead(7);
  float Voltage;
  VOLTAGE = analogRead(7)* 0.0537;  //采集一下电池电压
  //Voltage = Temp2 * 0.0537;   // Temp2/1024*5*11  1024为AI5V时满值，10K+1K电阻分压
  //VOLTAGE = VOLTAGE * 0.9 + Voltage * 0.1;
  return VOLTAGE;
}
/*******************************************************************
   10ms进行控制计算
   50ms进行超声波距离读取
   1s进行电压采集
 *******************************************************************/
void control() {
  int Vel = Velocity();
  int Tn = Turn();
  Serial.print(Vel);
  Serial.print("\t");
  Serial.println(Tn);
  Kinematic_Analysis(Vel, Tn);
  Set_Pwm(Target_A, Target_B);
}

void loop()
{
  static int Distance_Tim = millis();
  static int Control_Tim = Distance_Tim;
  static int Voltage_Tim = Distance_Tim;
  static float Voltage = 0;
  if (millis() - Distance_Tim >= 50)
  {
    ReadDistances();
    Distance_Tim = millis();
  }
  if (millis() - Voltage_Tim >= 1000)
  {
    Voltage = Battery();
    //Serial.println(Voltage);
    Voltage_Tim = millis();
  }
  if (millis() - Control_Tim >= 20)
  {
    if (Voltage >= 6.4)
      control();
    else
      Set_Pwm(0, 0);
    Control_Tim = millis();
  }
}
void ReadDistances()
{
  static byte index_L = 0, index_R = 0;
  while (Serial.available()) //如果串口数据可用
  {
    if (index_L == 0)
    {
      comdataL[index_L] = Serial.read();//把获取传感器的数据存放到数组里面
      if (comdataL[index_L] == 0xA5) //判断数据的头文件
        index_L++;
    }
    else
    {
      comdataL[index_L++] = Serial.read();
    }
    if (index_L >= 3)
    {
      index_L = 0;
      DistanceL = comdataL[1] << 8 | comdataL[2]; //把收到的数据合成为距离值
    }
  }
  mySerial.listen();
  while (mySerial.available()) //如果串口数据可用
  {
    if (index_R == 0)
    {
      comdataR[index_R] = mySerial.read();//把获取传感器的数据存放到数组里面
      if (comdataR[index_R] == 0xA5) //判断数据的头文件
        index_R++;
    }
    else
    {
      comdataR[index_R++] = mySerial.read();
    }
  }
  if (index_R >= 3)
  {
    index_R = 0;
    DistanceR = comdataR[1] << 8 | comdataR[2]; //把收到的数据合成为距离值
  }
  Serial.print(DistanceL);
  Serial.print("\t");
  Serial.println(DistanceR);
}

int Velocity(void)
{
  float Velocity;
  float kp_chaoshengbo_zhixian = 0.4;
  float line_distance1, line_distance2;
  float set_distance = 1000;
  float line_distance = 0;

  line_distance1 = DistanceL - set_distance;
  line_distance2 = DistanceR - set_distance;

  if ((line_distance1 > 0 && line_distance2 > 0) || (line_distance1 < 0 && line_distance2 < 0))
  {
    line_distance = (line_distance1 + line_distance2) / 2;
    if (abs(line_distance) < 900)
      Velocity = kp_chaoshengbo_zhixian * line_distance;
    else
      Velocity = 0;
  }

  if (DistanceL > 4000 || DistanceR > 4000) Velocity = 0;
  return Velocity;
}

int Turn(void)
{
  float Turn;
  float Kp1 = 0.5;
  float cha1;

  cha1 =  DistanceR - DistanceL;

  if (DistanceL > 20 && DistanceL < 4000 && DistanceR > 20 && DistanceR < 4000)
  {
    Turn = -cha1 * Kp1;
  }
  else
  {
    Turn = 0;
  }
  return Turn;
}
