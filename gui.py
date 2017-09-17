#!/bin/python

import curses
import curses.textpad
import time
import psutil


def initCurses():
    screen = curses.initscr()
    curses.noecho()  # disable the keypress echo to prevent double input
    curses.cbreak()  # disable line buffers to run the keypress immediately
    curses.curs_set(0)
    screen.keypad(1)  # enable keyboard use

    screen.addstr(1, 2, "Fuzzing For Worms", curses.A_UNDERLINE)
    return screen


def initGui(threadCount):
    screen = initCurses()

    base_window_x = 15
    window_x_offset = 12
    window_height = 3 + 2

    box_y = 10

    boxes = []
    screen.border(0)

    screen.addstr(box_y + 1, 2, "Per second:")
    screen.addstr(box_y + 2, 2, "Count:")
    screen.addstr(box_y + 3, 2, "Crashes:")

    #screen.addstr(10, 2, "BB:             BB previous: ")
    #screen.addstr(11, 2, "Max crashes     reduced crahses: ")

    screen.addstr(3, 2, "CPU usage:")
    screen.addstr(4, 2, "Memory free:")

    n = 0
    while n < threadCount:
        boxX = base_window_x + n * window_x_offset
        screen.addstr(box_y - 1, boxX + 1, "Process " + str(n))
        boxx = curses.newwin(window_height, 10, box_y, boxX)
        boxx.box()
        boxes.append(boxx)

        n += 1

    return screen, boxes


def updateGui(screen, boxes, data):
    maxy, maxx = screen.getmaxyx()

    date = str(time.strftime("%c"))
    screen.addstr(1, maxx - len(date) - 2, date)

    screen.addstr(3, 15, '%3d' % (psutil.cpu_percent()))
    # svmem(total=10367352832, available=6472179712, percent=37.6, used=8186245120, free=2181107712, active=4748992512, inactive=2758115328, buffers=790724608, cached=3500347392, shared=787554304)
    screen.addstr(4, 15, str(psutil.virtual_memory()[4] / (1024 * 1024)))

    screen.refresh()
    n = 0
    for box in boxes:
        testspersecond = '%8d' % data[n]["testspersecond"]
        testcount = '%8d' % data[n]["testcount"]
        crashcount = '%8d' % data[n]["crashcount"]
        box.addstr(1, 1, testspersecond)
        box.addstr(2, 1, testcount)
        box.addstr(3, 1, crashcount)
        box.refresh()
        n += 1


def cleanup():
    curses.endwin()


def main():
    data = [
        {
            "testspersecond": 1,
            "testcount": 2,
            "crashcount": 3,
        },
        {
            "testspersecond": 11,
            "testcount": 22,
            "crashcount": 33,
        },
        {
            "testspersecond": 111,
            "testcount": 222,
            "crashcount": 333,
        }
    ]

    screen, boxes = initGui( len(data) )

    try:
        while True:
            data[0]["testspersecond"] += 1
            updateGui(screen, boxes, data)

            # handle key presses
            #c = screen.getch()
            #if c == ord('q'):
            #    break;

            time.sleep(1)
    except KeyboardInterrupt:
        curses.endwin()


if __name__ == '__main__':
    main()
