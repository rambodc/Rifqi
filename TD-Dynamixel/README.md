# Dynamixel Integration with Touchdesigner

## Setup Dynamixel SDK for Touchdesigner
1. Download latest [**Dynamixel SDK**](https://github.com/ROBOTIS-GIT/DynamixelSDK/archive/refs/heads/master.zip)
2. Extract all files to your prefered directory
3. Copy **dynamixel_sdk** folder from *DynamixelSDK/python/src/dynamixel_sdk* to your python **site-packages** directory. Default directory is shown below (change username with yours).
```code
C:/Users/username/AppData/Local/Programs/Python/Python37/Lib/site-packages
```
4. Open your terminal and install pyserial using this command
```code
pip3 install pyserial
```
5. Open Touchdesigner and open Edit>Preferences.
6. Check Add External Python to Search Path
7. Add your site-packages directory to Python 64-bit Module Path
8. Uncheck Search External Python Path Last
9. Open Dialogs>Texport and DATs
10. Verify dynamixel_sdk installation by running following command and make sure there is no error.
```python
import dynamixel_sdk
```