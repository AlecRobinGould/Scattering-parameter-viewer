# Scattering-parameter-viewer

This Application additionally calculates the average |S21| and writes it to a .csv.

## IF the .s2p is formatted as mag and phase - get linear first!

$S21_{real} = 10^{S21_{magnitude}\over20} \times \cos(S21_{phase}\times{\Pi \over 180})$

$S21_{imag} = 10^{S21_{magnitude}\over20} \times \sin(S21_{phase}\times{\Pi \over 180})$

From here proceed to the next section

## To calculate average S21 from a .s2p with linear values

*Note: Mean S21 is always calculated using linear values first, then converted to log scale (dB)!

$|S21| = \sqrt{Real(S21)^2 + Imag(S21)^2}$


$|S21|(dB) = 20log{S21}$ dB

The 4th column in a .s2p file is typically the S21 real component, and the 5th being the imaginary component.

## Create a standalone application use pyinstaller
First install pyinstaller

`python -m pip install pyinstaller`


Then, if not already, add python scripts to PATH in environment variables

Open and edit the .bat file for the splash image you desire.
run the .bat file.

Done!

[Credit for the GUI](https://github.com/Partmedia/s2p-view)
