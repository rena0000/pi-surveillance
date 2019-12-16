#!/bin/bash

echo "-----------------------------------------------"
echo "---------Raspberry Pi Motion Detection---------"
echo "-----------------------------------------------"

echo "1: Run with security feed display"
echo "2: Run without windows"

selection=2

while true; do
    read -p "Select how you want to run this program (1 or 2): " selection
    if [[ ($selection == 1 ) || ($selection == 2) ]]
    then
        echo "Starting motion detection, press 'q' to quit"
        break
    else
        echo "Sorry, please enter a valid option"
    fi
done

if [[ $selection == 1 ]]
then
    python3 mvmt.py
else
    python3 mvmt-no-display.py
fi

sync
exit 0
