defineRule("dt1_round_value_rule", {
    whenChanged: "wb-w1/28-00000ec7a9f9",
    then: function(newValue, devName, cellName) {
      dev["CoolingSystem/DT1 Value"] = newValue.toFixed(2); // 9.99
    }
});

defineRule("dt6_round_value_rule", {
    whenChanged: "wb-w1/28-00000ec5e8de",
    then: function(newValue, devName, cellName) {
      dev["CoolingSystem/DT6 Value"] = newValue.toFixed(2); // 9.99
    }
});

defineRule("dt8_round_value_rule", {
    whenChanged: "wb-w1/28-00000ec5f529",
    then: function(newValue, devName, cellName) {
      dev["CoolingSystem/DT8 Value"] = newValue.toFixed(2); // 9.99
    }
});

defineRule("dt9_round_value_rule", {
    whenChanged: "wb-w1/28-00000ec7b1ac",
    then: function(newValue, devName, cellName) {
      dev["CoolingSystem/DT9 Value"] = newValue.toFixed(2); // 9.99
    }
});

defineRule("dt10_round_value_rule", {
    whenChanged: "wb-w1/28-00000ec76957",
    then: function(newValue, devName, cellName) {
      dev["CoolingSystem/DT10 Value"] = newValue.toFixed(2); // 9.99
    }
});