* =====================================================
* ring_osc_test.sp
* Testbench for 7-stage Ring Oscillator
* =====================================================

.include "ring_osc_7stage.subckt"

VDD vdd 0 1.1
VEN enable 0 DC 1.1

* Instantiate the ring oscillator
XROSC n1 n2 n3 n4 n5 n6 n7 enable vdd 0 RING_OSC

* --- Transient simulation ---
.tran 0.1n 200n uic

* --- Measurement commands ---
* Measure time period between two rising edges of node n4
.measure tran TPERIOD TRIG v(n4) VAL=0.55 RISE=2 TARG v(n4) VAL=0.55 RISE=3
* Compute frequency as reciprocal of period
.measure tran FREQ PARAM='1/TPERIOD'

.control
run
print TPERIOD
print FREQ
plot v(n1) v(n4) v(n7)
.endc

.end

