# PKXMIZNT6KBX7EVETKAIAUWJV7LPHPVW
# liuqingling@kdniao.com
# liuqingling
# kdn2025 
# 813249
# pypi token 
# pypi-AgEIcHlwaS5vcmcCJDY1ODhkNDRkLWM2ZjAtNDFiZC05NmQ0LTgyMTdkMjk5NmVjNQACKlszLCJlNGVjZGFhMy03ODFmLTQyYjUtOGRkNS02YWE5YTM3YjYxNGYiXQAABiBWLqJfuC3JeIgVWCbhiJmvteBc2bxxdGXLSpITT8crtQ
import pyotp
 
key = 'PKXMIZNT6KBX7EVETKAIAUWJV7LPHPVW'
totp = pyotp.TOTP(key)
print(totp.now())