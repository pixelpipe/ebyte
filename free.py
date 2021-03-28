"""Free memory usage utilities"""

import gc
import os

def prog(log=False):
    """Returns free Micropython FLASH memory"""
    s = os.statvfs('//')
    sectorSize=s[0]
    sectorTotal=s[2]
    sectorFree=s[3]
    percentage = '{0:.2f} %'.format(sectorFree/sectorTotal*100)
    if (log):
        print('■ Micropython FLASH')
        print('  Sector : {0} Bytes'.format(s[0]))
        print('  Total  : {0} Sectors, {1:.4f} MB'.format(s[2],sectorSize*sectorTotal/1048576))
        print('  Free   : {0} Sectors, {1:.4f} MB'.format(s[3],sectorSize*sectorFree/1048576))
        print('  Free % : {0}'.format(percentage))
        print()
    return sectorSize*sectorFree

def ram(log=False):
    """Returns free Micropython RAM memory"""
    gc.collect()
    freeRam = gc.mem_free()
    allocatedRam = gc.mem_alloc()
    totalRam = freeRam+allocatedRam
    percentage = '{0:.2f} %'.format(freeRam/totalRam*100)
    if (log):
        print('■ Micropython RAM')
        print('  Total  : {0:.2f} KB'.format(totalRam/1024))
        print('  Free   : {0:.2f} KB'.format(freeRam/1024))
        print('  Free % : {0}'.format(percentage))
        print()
    return freeRam

