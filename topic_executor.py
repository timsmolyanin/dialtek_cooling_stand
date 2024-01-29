class TopicExecutor:
    
    def __init__(self,nextion_mqtt_bridge, config):
        self.nextion_mqtt_bridge = nextion_mqtt_bridge
        
        self.config = config
    
    def execute(self, group_name, module_name, topic_value,):
        self.group_name = group_name
        self.module_name = module_name
        self.topic_value = topic_value
        try:
            module = self.config[self.group_name][self.module_name]
        except KeyError:
            raise KeyError('Ключ не найден, топик не прописан', self.group_name, self.module_name)
        
        if module['Condition'] == 'False':
            try:
                cmds = module["Cmd"]
                for cmd in cmds:
                    full_cmd = f'{cmd}\"{self.topic_value}\"'
                    self.nextion_mqtt_bridge.serial_write(full_cmd)
            except Exception as e:
                print(e)
          

        if module['Condition'] == 'True':
            try:
                cmds = module[str(self.topic_value)]
            except KeyError:
                raise KeyError('Состояния "' + str(self.topic_value) + '" в модуле "' + self.module_name + '" не существует. Группа: "' + self.group_name + '"')
            for cmd in cmds:
                self.nextion_mqtt_bridge.serial_write(cmd)