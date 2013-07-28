language: PYTHON
name:     "job"

variable {
 name: "epochs_stage1"
 type: INT
 size: 1
 min:  300
 max:  500
}

variable {
 name: "epochs_stage2"
 type: INT
 size: 1
 min:  100
 max:  300
}

variable {
 name: "epsW"
 type: FLOAT
 size: 1
 min:  1e-5
 max:  1e-3
}

variable {
 name: "wc_conv1"
 type: FLOAT
 size: 1
 min:  0
 max:  0.1
}

variable {
 name: "wc_conv2"
 type: FLOAT
 size: 1
 min:  0
 max:  0.1
}

variable {
 name: "wc_local3"
 type: FLOAT
 size: 1
 min:  0
 max:  0.1
}

variable {
 name: "wc_local4"
 type: FLOAT
 size: 1
 min:  0
 max:  0.1
}

variable {
 name: "wc_fc10"
 type: FLOAT
 size: 1
 min:  0
 max:  0.1
}

variable {
 name: "scale_rnorm"
 type: FLOAT
 size: 1
 min:  0.0001
 max:  0.1
}

variable {
 name: "size_rnorm"
 type: INT
 size: 1
 min:  3
 max:  12
}

variable {
 name: "pow_rnorm"
 type: FLOAT
 size: 1
 min:  0
 max:  1
}




