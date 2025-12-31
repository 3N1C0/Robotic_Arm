/*
 */
#include <math.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver arm = Adafruit_PWMServoDriver();

#define servoMIN 150
#define servoMAX 600
#define pi 3.1415926535897932384626433832795

const float final_x = 89;
const float final_y = 89;

const int base_servo = 0;
const int servo_1 = 1;
const int servo_2 = 2;
const int servo_3 = 3;

//Units in mm
const float link_one_length = 65;
const float link_two_length = 65;
const float link_three_length = 10;  

float r2d(float x) {
    float ans;
    ans = x * (180/pi);
    return ans;
}

float theta1(){
  //Triangle one
  float line_three_final_x = final_x - link_three_length;
  float hyp_one = sqrt(sq(line_three_final_x) + sq(final_y));
  float alpha_one = atan2(final_y, line_three_final_x);
  float beta_one = acos((sq(link_one_length) - sq(link_two_length) - sq(hyp_one))/(-2*hyp_one*link_two_length));
  float theta_one = r2d(alpha_one+beta_one);
  //float triangle_one_height = link_one_length * sin(radians(theta_one));
  //float triangle_one_width = link_one_length * cos(radians(theta_one));

  return theta_one;
}

float theta2(){
  //Triangle two
  float line_three_final_x = final_x - link_three_length;
  float hyp_one = sqrt(sq(line_three_final_x) + sq(final_y));

  float triangle_two_height = final_y;
  float triangle_two_width = final_x - link_three_length;

  float theta_two = acos((sq(link_one_length) + sq(link_two_length) - sq(hyp_one))/ (2 * link_one_length * link_two_length));
  theta_two = -1 * (180 - r2d(theta_two));

  return theta_two;
}

float theta3(float theta_one, float theta_two){
  //Triangle three
  float gamma = 0;
  float theta_three = gamma - (theta_one+theta_two);

  return theta_three;
}

float theta_base(){
  //Base Angle
  //float theta_base = atan2(final_y, line_three_final_x);
  float theta_base = 90;

  return theta_base;
}

float calibrate(float x){
  float y = x + 90;
  return y;
}

float d2P(float x){  
  int pulse = map(x,0, 180, SERVOMIN,SERVOMAX);   
  return pulse;
}

void setup() {
  //Arduino Setup
  Serial.begin(9600);
  arm.begin();
  arm.setPWMFreq(60);

  pinMode(base_servo, OUTPUT);
  pinMode(servo_1, OUTPUT);
  pinMode(servo_2, OUTPUT);
  pinMode(servo_3, OUTPUT);

  Serial.println(theta_one);
  Serial.println(theta_two);
  Serial.println(theta_three);
}

void loop() {
  if (Serial.available() > 0) {
    String msg = Serial.readString();
  }

  //Call all Calculations
  float t1 = theta1();
  float t2 = theta2();
  float t3 = theta3(t1, t2);
  float tb = theta_base();

  //Calibrate them taking into account the 90 degree offset
  t1 = calibrate(t1);
  t2 = calibrate(t2);
  t3 = calibrate(t3);
  tb = calibrate(tb);

  arm.setPWM(1,0,d2p(t1));
  arm.setPWM(2,0,d2p(t2));
  arm.setPWM(3,0,d2p(t3));
  arm.setPWM(0,0,d2p(tb));
}
