defineVirtualDevice("CoolingSystem", {
    title: "CoolingSystem",
    cells: {
      "Auto Mode": {
      type: "switch",
      value: true,
      readonly: false
      },
      "Debug msg": {
      type: "txt",
      value: "",
      readonly: false
      },
      "Up limit": {
      type: "float",
      value: 18.0,
      readonly: false
      },
      "Down limit": {
      type: "float",
      value: 16.0,
      readonly: false
      },
      "Wait time": {
      type: "float",
      value: 60.0,
      readonly: false
      },
      "Counter": {
      type: "float",
      value: 0.0,
      readonly: false
      },
      "Fans ON count": {
      type: "int",
      value: 0,
      readonly: false
      },
      "Current state": {
      type: "txt",
      value: "",
      readonly: false
      },
      "DT1 Status": {
      type: "int",
      value: 0,
      readonly: false
      },
      "DT8 Status": {
      type: "int",
      value: 0,
      readonly: false
      },
      "DT9 Status": {
      type: "int",
      value: 0,
      readonly: false
      },
      "DT10 Status": {
      type: "int",
      value: 0,
      readonly: false
      },
      "DT6 Status": {
      type: "int",
      value: 0,
      readonly: false
      }
    }
  });