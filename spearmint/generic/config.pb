language: PYTHON
name:     "job"

variable {
 name: "learningRate"
 type: FLOAT
 size: 1
 min:  1e-4
 max:  1
}

variable {
 name: "momentum"
 type: FLOAT
 size: 1
 min:  0
 max:  1
}

variable {
 name: "learningRateDecay"
 type: FLOAT
 size: 1
 min:  0
 max:  1e-2
}


variable {
 name: "weightDecay"
 type: FLOAT
 size: 1
 min:  0
 max:  1e-3
}

