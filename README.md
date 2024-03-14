# Scattering-parameter-viewer

This Application additionally calculates the average |S21| and writes it to a .csv.

To calculate average S21 from a .s2p:

$|S21| = \sqrt{Real(S21)^2 + Imag(S21)^2}$

*Note: Mean S21 is always calculated using linear values first, then converted to log scale (dB)!

$|S21|(dB) = 20log{S21}$ dB

The 4th column in a .s2p file is typically the S21 real component, and the 5th being the imaginary component.


## Create a standalone application use pyinstaller
First install pyinstaller

`python -m pip install pyinstaller`


Then, if not already, add python scripts to PATH in environment variables

run the .bat file.

Done!

[Credit for the GUI](https://github.com/Partmedia/s2p-view)
