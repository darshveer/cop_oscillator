* =====================================================
* Testbench for Two 7-Stage Ring Oscillators with Delayed Enables and Coupling
* =====================================================

.include "ring_osc_7stage.subckt"
.include "coupling.subckt"

VDD vdd 0 1.1

* --- Enable signals ---
* First oscillator enabled immediately
VEN1 enable1 0 PULSE(0 1.1 0n 0.1n 0.1n 10u 2u)

* Second oscillator enabled slightly later (10 ns delay)
VEN2 enable2 0 PULSE(0 1.1 0n 0.1n 0.1n 10u 2u)

* Coupling enable comes even later (e.g. 50 ns)
VCPL_EN w_en 0 PULSE(0 1.1 200n 0.1n 0.1n 10u 20u)

* === Instantiate Ring Oscillator 1 ===
XROSC1 n1_1 n2_1 n3_1 n4_1 n5_1 n6_1 n7_1 enable1 vdd 0 RING_OSC

* === Instantiate Ring Oscillator 2 ===
XROSC2 n1_2 n2_2 n3_2 n4_2 n5_2 n6_2 n7_2 enable2 vdd 0 RING_OSC

* === Coupling Stage ===
* Connect midpoint nodes of both oscillators through coupling circuits
XCOUP w_en n4_1 n4_2 vdd 0 COUPLING

* --- Initial condition to break symmetry ---
.ic V(n4_1)=0.9

* --- Transient simulation ---
.tran 0.1n 2u uic

* --- Measurement commands ---
.measure tran TPERIOD1 TRIG v(n4_1) VAL=0.55 RISE=2 TARG v(n4_1) VAL=0.55 RISE=3
.measure tran TPERIOD2 TRIG v(n4_2) VAL=0.55 RISE=2 TARG v(n4_2) VAL=0.55 RISE=3
.measure tran FREQ1 PARAM='1/TPERIOD1'
.measure tran FREQ2 PARAM='1/TPERIOD2'
.measure tran PHASE_DELAY TRIG v(n4_1) VAL=0.55 RISE=2 TARG v(n4_2) VAL=0.55 RISE=2
.measure tran PHASE_DIFF PARAM='360*PHASE_DELAY/TPERIOD1'
.measure tran VOUT1_MAX MAX v(n4_1)
.measure tran VOUT1_MIN MIN v(n4_1)
.measure tran VOUT2_MAX MAX v(n4_2)
.measure tran VOUT2_MIN MIN v(n4_2)

.control
run
print TPERIOD1
print TPERIOD2
print FREQ1
print FREQ2
print VOUT1_MAX
print VOUT1_MIN
print VOUT2_MAX
print VOUT2_MIN

* --- Plot main waveforms ---
plot v(n4_1) v(n4_2) v(w_en)

* (Removed internal node plots like v(@XCOUP%mp_out_0) — those cause errors)
.endc

.end
