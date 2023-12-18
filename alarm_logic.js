var buzzer_state = false;
var dt1_alarm_state = false
var dt10_alarm_state = false
var dt8_alarm_state = false
var dt6_alarm_state = false
var dt9_alarm_state = false


defineRule("dt1_sensor_state_rule", {
    whenChanged: "CoolingSystem/DT1 Status",
    then: function(newValue, devName, cellName) {
        if (newValue == 1) {
          dt1_alarm_state = true;
        }
        else if (newValue == 0){
          dt1_alarm_state = false;
        }
    }
});

defineRule("dt10_sensor_state_rule", {
    whenChanged: "CoolingSystem/DT10 Status",
    then: function(newValue, devName, cellName) {
        if (newValue == 1) {
          dt10_alarm_state = true;
        }
        else if (newValue == 0){
          dt10_alarm_state = false;
        }
    }
});

defineRule("dt6_sensor_state_rule", {
    whenChanged: "CoolingSystem/DT6 Status",
    then: function(newValue, devName, cellName) {
        if (newValue == 1) {
          dt6_alarm_state = true;
        }
        else if (newValue == 0){
          dt6_alarm_state = false;
        }
    }
});

defineRule("dt8_sensor_state_rule", {
    whenChanged: "CoolingSystem/DT8 Status",
    then: function(newValue, devName, cellName) {
        if (newValue == 1) {
          dt8_alarm_state = true;
        }
        else if (newValue == 0){
          dt8_alarm_state = false;
        }
    }
});

defineRule("dt9_sensor_state_rule", {
    whenChanged: "CoolingSystem/DT9 Status",
    then: function(newValue, devName, cellName) {
        if (newValue == 1) {
          dt9_alarm_state = true;
        }
        else if (newValue == 0){
          dt9_alarm_state = false;
        }
    }
});

defineRule("buzzer_state_rule", {
    whenChanged: "buzzer/enabled",
    then: function(newValue, devName, cellName) {
      buzzer_state = newValue;
    }
});


defineRule("cron_timer", {
    when: cron("@every 0h0m1s"),
    then: function() {
        if (dt1_alarm_state == true || dt10_alarm_state == true || dt6_alarm_state == true || dt8_alarm_state == true || dt9_alarm_state == true) {
            if (buzzer_state == true) {
                dev["buzzer/enabled"] = false;
            } else {
                dev["buzzer/enabled"] = true;
            }
        } else {
          dev["buzzer/enabled"] = false;
        }
    }
});