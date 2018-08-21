'''
Copyright (C) 2018 Meister Lab at Caltech 
-----------------------------------------------------
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

#####################
#
# Run once, do not move file
#
#####################
import sys
import os
import site

def main(argv):
    rasPiSoftwarePath = os.path.dirname(os.path.realpath(__file__))
    modulePath = os.path.join(rasPiSoftwarePath, 'Modules')
    packages = site.getusersitepackages()
    sitePackages = site.getsitepackages()
    sp = None
    for s in sitePackages:
        if 'package' in s:
            sp = s
            break
    print(sp)
    with open(os.path.join(sp, 'MouseAcademyPi.pth'), 'w') as pth:
        pth.write(rasPiSoftwarePath)
        pth.write('\n')
        pth.write(modulePath)

if __name__ == "__main__":
    main(sys.argv[1:])