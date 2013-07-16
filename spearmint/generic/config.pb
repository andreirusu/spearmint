language: PYTHON
name:     "job"

variable {
 name: "learningRate"
 type: FLOAT
 size: 3
 min:  1e-4
 max:  1
}

variable {
 name: "momentum"
 type: FLOAT
 size: 3
 min:  0
 max:  1
}

variable {
 name: "learningRateDecay"
 type: FLOAT
 size: 3
 min:  0
 max:  1e-2
}


variable {
 name: "weightDecay"
 type: FLOAT
 size: 3
 min:  0
 max:  1e-3
}

variable {
 name: "szMinibatch"
 type: INT
 size: 3
 min:  1
 max:  300
}

variable {
 name: "dropoutRatio"
 type: FLOAT
 size: 3
 min:  0.0
 max:  0.75
}

variable {
 name: "L1Cost"
 type: FLOAT
 size: 3
 min:  0.001
 max:  10.0
}

variable {
 name: "hidden"
 type: INT
 size: 3
 min:  100
 max:  1500
}

