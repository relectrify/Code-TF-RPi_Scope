import visa
from rigol import ds1000z

def raw_data_to_string(raw_data):
    string = str(raw_data).strip("b\'").strip("\\ne")
    string = string.replace(',', '\n')
    return string

def main():
    rm = visa.ResourceManager('@py')
    resources = rm.list_resources()
    usb = list(filter(lambda x: 'USB' in x, resources))
    print(usb[0])
    device = rm.open_resource(usb[0])
    device.timeout = None
    scope = ds1000z.Ds1000z(device)
    scope.get_screenshot("test.png")

    waveform = raw_data_to_string(scope.get_data())
    with open("waveform.csv", 'w') as f:
        for point in waveform:
            f.write(point)

if __name__ == "__main__":
    main()