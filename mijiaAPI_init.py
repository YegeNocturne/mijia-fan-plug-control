from mijiaAPI import mijiaAPI, mijiaDevice
api = mijiaAPI()
#api.login()
devices = api.get_devices_list()
for device in devices:
    print(f"设备名称: {device['name']}, Model: {device['model']}, Did: {device['did']}")

#plug_device = mijiaDevice(api, dev_name="散热器插座")
#print(plug_device)
#print(plug_device.on_2)