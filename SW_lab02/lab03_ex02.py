import Service

from time import time
from threading import Thread


REFRESH_TIME = 60


def refresh(service: Service):
    while True:
        service.update()
        time.sleep(REFRESH_TIME)


def main():
    service: Service
    Thread(target = refresh, args = (service))
    


if __name__ == '__main__':
    main()