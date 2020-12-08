
#define N_SAMPLES 600
uint8_t achan0[N_SAMPLES];
uint8_t achan1[N_SAMPLES];

uint8_t adc_read( uint8_t channel )
{
  // Kanal waehlen, ohne andere Bits zu beeinflußen
  ADMUX = (ADMUX & ~(0x1F)) | (channel & 0x1F);
  ADCSRA |= (1<<ADSC);            // trigger "single conversion"
  while (ADCSRA & (1<<ADSC) ) {   // wait ready
  }
  return ADCH;                    // left justified 8 bit result (see ADLAR)
}

void adc_init() {
  ADMUX = (1<<REFS0) | (1<<ADLAR); // ref to AVcc, left-justified output (for 8 bit)
  ADCSRA = (1<<ADPS2) | (1<<ADEN); // Presc=16, conversion rate 76.9kHz, enable
  adc_read(0); // dummy read required after init
}


void send_packet() {
  uint8_t header[4] = { 0x00, 0x00, 0xFF, 0xFF };
  Serial.write(header, sizeof(header));  
  // TODO: add aux later
  Serial.write(achan0, sizeof(achan0));  
  Serial.write(achan1, sizeof(achan1)); 
  
  // not waiting for ack is faster but can produce overflows
  while (Serial.available() < 1) { 
  }
  uint8_t ack = Serial.read();
  if (ack != 0) {
    // TODO: parse config
  }
}

void capture_run() {
  //trigger test
  uint8_t lvl = 0x8F;
  uint8_t cur = adc_read(0);
  uint8_t last = cur;
  while (!(last < lvl && cur >= lvl)) {
    last = cur;
    cur = adc_read(0);  
  } 
  
  for (uint16_t i=0; i<N_SAMPLES; ++i) {
    // TODO: timed sampling
    achan0[i] = adc_read(0);
    achan1[i] = adc_read(1);
  }
}

void setup() {
  adc_init();
  Serial.setTimeout(10000);
  Serial.begin( 115200);//57600);
}

void loop() {
  capture_run();
  send_packet();
}
