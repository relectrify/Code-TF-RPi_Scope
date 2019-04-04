import visa
from rigol import ds1000z

def main():
    rm = visa.ResourceManager('@py')
    resources = rm.list_resources()
    usb = list(filter(lambda x: 'USB' in x, resources))
    print(usb[0])
    device = rm.open_resource(usb[0])
    device.timeout = None
    scope = ds1000z.Ds1000z(device)
    print(scope.get_id())
    scope.get_screenshot("test.png")

if __name__ == "__main__":
    main()